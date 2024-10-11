import pymupdf
import requests
from bs4 import BeautifulSoup, Tag

DOMAIN = "https://www.njcourts.gov"


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


def get_pdf_text(pdf_link: str) -> str:
    """
    Parses pdf text from a pdf link

    Args:
        pdf_link (str): link to pdf

    Returns:
        str: pdf text
    """

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0",
    }

    stream = requests.get(pdf_link, headers=headers)

    pdf = pymupdf.open(stream=stream.content, filetype="pdf")
    text = ""
    for page in pdf:
        text += page.get_text()
    pdf.close()

    return text


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


def scrape_page(url: str) -> dict[str, str | list[str]] | None:
    """
    Scrape page by extracting text and urls (only text for pdfs)

    Args:
        url (str): url to page to pdf

    Returns:
        dict[str, str | list[str]] | None: page object
    """

    split_url = url.split(".")
    page = {}

    # split urls > 3 indicate its a file url, where the only pdfs are accepted
    if len(split_url) > 3 and "pdf" in url:
        page["title"] = url.split("/")[-1].split("?")[0]
        page["text"] = get_pdf_text(url)
        page["child_pages"] = []
    # makes sure its a normal url
    elif len(split_url) == 3:
        soup = get_soup(url)
        content = soup.find("div", {"id": "page-content"})
        page["title"] = soup.find("title").string
        page["text"] = content.text
        page["child_pages"] = get_urls(content)
    else:
        return None

    return page
