import json

import matplotlib.pyplot as plt
import networkx as nx

import utils

G = nx.Graph()

# Script for specifically https://www.njcourts.gov/jurors/reporting
MAIN_URL = "https://www.njcourts.gov/jurors/reporting"
main_soup = utils.get_soup(MAIN_URL)
main_content = main_soup.find("div", {"id": "page-content"})
page_urls = utils.get_urls(main_content)

print(f"Fetched Pages From {MAIN_URL}: {page_urls}")
G.add_node(MAIN_URL)

pages = {}
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

page_process_counter = 0
skipped_page_counter = 0

for url in page_urls:
    # top level
    print("----------------------------")
    if url in pages:
        G.add_edge(MAIN_URL, url)
        print(f"Parent Page Already Scraped {url}...")
        skipped_page_counter += 1
        continue

    print(f"Scraping Parent Page {url}...")

    page = utils.scrape_page(url)
    if not page:
        continue

    G.add_node(url)
    G.add_edge(MAIN_URL, url)
    page["parent_page"] = MAIN_URL
    pages[url] = page

    # lower level
    for child_url in page["child_pages"]:
        if child_url in pages:
            G.add_edge(child_url, url)
            print(f"Child Page Already Scraped {child_url}...")
            skipped_page_counter += 1
            continue

        print(f"Scraping Child Page {child_url}...")

        child_page = utils.scrape_page(child_url)
        if not child_page:
            continue

        G.add_node(child_url)
        G.add_edge(child_url, url)
        child_page["parent_page"] = url
        pages[child_url] = child_page

        for sub_url in child_page["child_pages"]:
            if sub_url in pages:
                G.add_edge(child_url, sub_url)

            G.add_node(sub_url)
            G.add_edge(child_url, sub_url)

        print(f"Child Page Scraped: {child_url}")

    page_process_counter += 1
    print(f"Parent Page Scraped: {url}")

print(f"Parent Pages Scraped: [{page_process_counter}/{len(page_urls)}]")
print(f"Pages Skipped: [{skipped_page_counter}/{len(page_urls)}]")

nx.draw(G)
plt.show()

with open("scraped_data_2.json", "w", encoding="utf-8") as f:
    json.dump(pages, f)
