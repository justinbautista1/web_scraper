import json

import pymupdf
import requests
from bs4 import BeautifulSoup, Tag

DOMAIN = "https://www.njcourts.gov"


def format_url(url: str) -> str:
    if url[0] == "/":
        return DOMAIN + url

    return url


def get_urls(soup_content: Tag | BeautifulSoup) -> list[str]:
    main_anchors = soup_content.find_all("a")
    main_urls = set()

    for url in main_anchors:
        href = url.get("href")

        if href and (href[0] == "/" or DOMAIN in href):
            main_urls.add(format_url(href))

    return list(main_urls)


def get_pdf_text(pdf_link: str) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0",
    }

    stream = requests.get(pdf_link, headers=headers)

    pdf = pymupdf.open(stream=stream.content, filetype="pdf")
    text = ""
    for page in pdf:
        text += page.get_text()
    pdf.close()

    return text.encode("ascii", "ignore").decode()


def get_text(soup_content: Tag | BeautifulSoup) -> str:
    return soup_content.text.encode("ascii", "ignore").decode()


def get_soup(url: str) -> BeautifulSoup:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0",
        "Content-Type": "text/html",
    }

    page = requests.get(url, headers=headers)
    soup = BeautifulSoup(page.content, "html.parser")

    return soup


def scrape_page(url: str) -> dict[str, str | list[str]] | None:
    split_url = url.split(".")
    page = {}

    if len(split_url) > 3 and split_url[-1] == "pdf":
        page["text"] = get_pdf_text(url)
        page["child_pages"] = []
    elif len(split_url) == 3:
        soup = get_soup(url)
        content = soup.find("div", {"id": "page-content"})
        page["text"] = get_text(content)

        targeted_content = content.find("article")
        page["child_pages"] = get_urls(targeted_content)
    else:
        return None

    return page


##### MAIN CODE #####

# main_soup = get_soup("https://www.njcourts.gov/jury-reporting-messages/bergen")

# main_content = main_soup.find("div", {"id": "page-content"})
# main_urls = get_urls(main_content)
# main_text = get_text(main_content)

# subpages_text = {}
# for url in main_urls:
# split_url = url.split(".")

# if len(split_url) > 3 and split_url[-1] == "pdf":
#     subpages_text[url] = get_pdf_text(url)
# elif len(split_url) == 3:
#     soup = get_soup(url)
#     content = soup.find("div", {"id": "page-content"})
#     text = get_text(content)
#     subpages_text[url] = text

# Script for specifically https://www.njcourts.gov/jurors/reporting
MAIN_URL = "https://www.njcourts.gov/jurors/reporting"
main_soup = get_soup(MAIN_URL)
main_content = main_soup.find("div", {"id": "page-content"})
page_urls = get_urls(main_content)

print(f"Fetched Pages From {MAIN_URL}: {page_urls}")

pages = {}
"""
{
    url: {
        title: asd,
        text:asd,
        parent_page:asd or null,
        child_pages:[asd]
    }, ...
}
"""

page_process_counter = 0
skipped_page_counter = 0

for url in page_urls:
    # top level
    print("----------------------------")
    if url in pages:
        print(f"Parent Page Already Scraped {url}...")
        skipped_page_counter += 1
        continue

    print(f"Scraping Parent Page {url}...")

    page = scrape_page(url)
    if not page:
        continue

    page["parent_page"] = MAIN_URL
    pages[url] = page

    # lower level
    for child_url in page["child_pages"]:
        if child_url in pages:
            print(f"Child Page Already Scraped {child_url}...")
            skipped_page_counter += 1
            continue

        print(f"Scraping Child Page {child_url}...")

        child_page = scrape_page(child_url)
        if not child_page:
            continue

        child_page["parent_page"] = url
        pages[child_url] = child_page

        print(f"Child Page Scraped: {child_url}")

    page_process_counter += 1
    print(f"Parent Page Scraped: {url}")

print(f"Pages Scraped: [{page_process_counter}/{len(page_urls)}]")
print(f"Pages Skipped: [{skipped_page_counter}/{len(page_urls)}]")

with open("scraped_data.json", "w", encoding="utf-8") as f:
    json.dump(pages, f)
