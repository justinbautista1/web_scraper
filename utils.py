import base64
import json
import re

import requests
from azure.storage.blob import ContainerClient
from bs4 import BeautifulSoup, Tag

DOMAIN = "https://www.njcourts.gov"

Page = dict[str, str | list[str] | bool]


def format_url(url: str) -> str:
    """
    Appends url path to domain (njcourts.gov) or returns url if its a full url

    Args:
        url (str): url path or full url within the njcourts.gov domain

    Returns:
        str: full url
    """

    if url[0] == "/":
        return DOMAIN + url

    return url


def get_urls(soup_content: Tag | BeautifulSoup) -> list[str]:
    """
    Get all unique urls within the soup in the njcourts.gov domain

    Args:
        soup_content (Tag | BeautifulSoup): soup

    Returns:
        list[str]: list of unique urls within the soup in the njcourts.gov domain
    """

    main_anchors = soup_content.find_all("a")
    main_urls = set()

    for url in main_anchors:
        href = url.get("href")

        if not href:
            continue

        # only allow urls within domain
        # some hrefs are just the url paths, therefore accept those
        if href[0] == "/" or DOMAIN in href:
            main_urls.add(format_url(href))

    return list(main_urls)


def get_soup(url: str) -> BeautifulSoup:
    """
    Get soup from url

    Args:
        url (str): url

    Returns:
        BeautifulSoup: soup
    """

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0",
        "Content-Type": "text/html",
    }

    page = requests.get(url, headers=headers)
    soup = BeautifulSoup(page.content, "html.parser")

    return soup


def scrape_faq_content() -> list[dict[str, Page | str]]:
    url = "https://www.njcourts.gov/jurors/faq"

    soup = get_soup(url)
    page_title = soup.find("title").string
    content = soup.find("article", {"about": "/jurors/faq"})
    faq_content = content.find_all("li", {"class": "mt-3 faq-item"})
    faqs = []

    for faq in faq_content:
        page_faq_pair = {}
        question = faq.find("h3")
        faq_id = question["id"]
        faq_title = question.text.strip().lstrip("Q. ").strip()

        page_faq = {"source": "website"}
        page_faq["title"] = f"{page_title} | {faq_title}"
        page_faq["text"] = re.sub(r"\s+", " ", faq.text)
        page_faq["is_file"] = False
        page_faq["parent_pages"] = [url, "https://www.njcourts.gov/jurors"]

        page_faq["child_pages"] = get_urls(faq)
        page_faq["child_pages"] = [child_page for child_page in page_faq["child_pages"] if url not in child_page]

        page_faq_pair["url"] = f"{url}#{faq_id}"
        page_faq_pair["faq"] = page_faq

        faqs.append(page_faq_pair)

    return faqs


def scrape_page(url: str) -> Page | None:
    """
    Scrape page by extracting text and urls

    Args:
        url (str): url

    Returns:
        dict[str, str | list[str]] | None: page object
    """

    split_url = url.split(".")
    page = {"source": "website"}

    # split urls > 3 indicate its a file url
    if len(split_url) > 3:
        page["title"] = url.split("/")[-1].split("?")[0]
        page["text"] = ""
        page["child_pages"] = []
        page["is_file"] = True
    # makes sure its a normal url
    elif len(split_url) == 3:
        soup = get_soup(url)
        content = soup.find("div", {"id": "page-content"})
        page["title"] = soup.find("title").string
        page["text"] = re.sub(r"\s+", " ", content.text)
        page["is_file"] = False

        page["child_pages"] = get_urls(content)
        if url in page["child_pages"]:
            page["child_pages"].remove(url)
    else:
        return None

    return page


def upload_to_blob(container_client: ContainerClient, pages: dict[Page], directory: str | None = None) -> None:
    path = ""
    if directory:
        path = f"{directory}/"

    for page_url, page_content in pages.items():
        metadata = {"url": page_url}
        metadata.update(page_content)
        encoded_bytes = base64.b64encode(page_url.encode("utf-8"))
        encoded_str = encoded_bytes.decode("utf-8").rstrip("=")

        if page_content["is_file"]:
            file_extension = page_content["title"].split(".")[-1]
            metadata.pop("text")
            metadata["parent_pages"] = str(metadata["parent_pages"])
            metadata["child_pages"] = str(metadata["child_pages"])
            metadata["is_file"] = str(metadata["is_file"])

            blob_name = f"{path}{encoded_str}.{file_extension}"
            blob_client = container_client.get_blob_client(blob_name)
            blob_client.upload_blob_from_url(page_url, overwrite=True)
            blob_client.set_blob_metadata(metadata)
        else:
            data = {}
            data.update(metadata)
            data.pop("child_pages")
            data.pop("parent_pages")
            data.pop("is_file")
            data = json.dumps(data)

            metadata.pop("text")
            metadata["parent_pages"] = str(metadata["parent_pages"])
            metadata["child_pages"] = str(metadata["child_pages"])
            metadata["is_file"] = str(metadata["is_file"])

            blob_name = f"{path}{encoded_str}.json"
            blob_client = container_client.get_blob_client(blob_name)
            blob_client.upload_blob(data, metadata=metadata, overwrite=True)
