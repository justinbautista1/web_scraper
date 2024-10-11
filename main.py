import json
import logging
import time

import colorlog

import utils


class CustomColorFormatter(colorlog.ColoredFormatter):
    def format(self, record):
        if "SKIP" in record.msg:
            self.log_colors = {"INFO": "blue"}
        elif "COMPLETE" in record.msg:
            self.log_colors = {"INFO": "green"}
        else:
            self.log_colors = {"INFO": "cyan"}

        return super().format(record)


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_formatter = CustomColorFormatter(
    "%(log_color)s%(levelname)s: %(message)s",
    log_colors={
        "DEBUG": "white",
        "INFO": "cyan",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "bold_red",
    },
)

console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

file_handler = logging.FileHandler("logs.txt")
file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

script_start = time.time()

MAIN_URL = "https://www.njcourts.gov/jurors"
main_soup = utils.get_soup(MAIN_URL)
main_content = main_soup.find("div", {"id": "page-content"})
page_urls = utils.get_urls(main_content)

logger.info("Fetched Pages From %s: %s", MAIN_URL, page_urls)

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

pages_scraped = 0
scraping_times = []

while page_stack:
    url = page_stack.pop()

    if url not in pages:
        logger.info("<SCRAPING PAGE>: %s...", url)

        scraping_time_start = time.time()
        page = utils.scrape_page(url)

        if not page:
            continue

        page["parent_page"] = MAIN_URL
        pages[url] = page

        scraping_time_end = time.time()
        scraping_times.append(scraping_time_end - scraping_time_start)

        pages_scraped += 1
        page_stack.extend(page["child_pages"])
        logger.info("<COMPLETED PAGE>: %s", url)
    else:
        logger.info("<SKIPPING PAGE>: %s", url)

script_end = time.time()
total_time = str(script_end - script_start)
avg_time = str(sum(scraping_times) / pages_scraped)

logger.info("--------------------------------------------------")
logger.info("Script Total Time (s): %s", total_time)
logger.info("Average Scraping Time Per Page: %s", avg_time)

pages.pop("https://www.njcourts.gov/")
with open("scraped_data.json", "w", encoding="utf-8") as f:
    json.dump(pages, f)
