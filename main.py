import json
import time

import matplotlib.pyplot as plt
import networkx as nx

import utils

script_start = time.time()

MAIN_URL = "https://www.njcourts.gov/jurors"
main_soup = utils.get_soup(MAIN_URL)
main_content = main_soup.find("div", {"id": "page-content"})
page_urls = utils.get_urls(main_content)

print(f"Fetched Pages From {MAIN_URL}: {page_urls}")

pages = {}
page_stack = page_urls.copy()

# no need to scrape whole site, just jurors
pages["https://www.njcourts.gov/"] = {}

"""
{
    url: {
        title: "title"
        text: "text",
        parent_page: "parent page",
        child_pages: ["child page", ...]
    }, ...
}
"""

while page_stack:
    url = page_stack.pop()

    if url not in pages:
        print(f"<SCRAPING PAGE>: {url}...")
        page = utils.scrape_page(url)

        if not page:
            continue

        page["parent_page"] = MAIN_URL
        pages[url] = page

        print(f"<COMPLETED PAGE>: {url}")

        page_stack.extend(page["child_pages"])
    else:
        print(f"<SKIPPING PAGE>: {url}")

script_end = time.time()
print("--------------------------------------------------")
print(f"Script Total Time (s): {script_end - script_start}")


with open("scraped_data_2.json", "w", encoding="utf-8") as f:
    json.dump(pages, f)
