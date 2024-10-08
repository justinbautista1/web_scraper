import pymupdf
from bs4 import BeautifulSoup, Tag

# from selenium import webdriver

DOMAIN = "https://www.njcourts.gov"

# options = webdriver.FirefoxOptions()
# options.add_argument("--headless")
# driver = webdriver.Firefox(options=options)

import requests


def format_url(url: str) -> str:
    if url[0] == "/":
        return DOMAIN + url

    return url


def get_urls(soup_content: Tag | BeautifulSoup) -> list[str]:
    main_anchors = soup_content.find_all("a")
    main_urls = set()

    for url in main_anchors:
        href = url.get("href")

        if href and ("https" in href or href[0] == "/") and "google.com" not in href:
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


##### MAIN CODE #####

# driver.get("https://www.njcourts.gov/jury-reporting-messages/bergen")
# main_page = driver.page_source


main_soup = get_soup("https://www.njcourts.gov/jury-reporting-messages/bergen")

main_content = main_soup.find("div", {"id": "page-content"})
main_urls = get_urls(main_content)
main_text = get_text(main_content)

subpages_text = {}
for url in main_urls:
    split_url = url.split(".")

    if len(split_url) > 3 and split_url[-1] == "pdf":
        subpages_text[url] = get_pdf_text(url)
    elif len(split_url) == 3:
        soup = get_soup(url)
        content = soup.find("div", {"id": "page-content"})
        text = get_text(content)
        subpages_text[url] = text


# driver.quit()
