import json
import logging
import time

import colorlog

import utils

# initialize logger and custom formatter for INFO logs
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class CustomColorFormatter(colorlog.ColoredFormatter):
    def format(self, record: logging.LogRecord) -> str:
        if "SKIPPING" in record.msg:
            self.log_colors = {"INFO": "blue"}
        elif "COMPLETED" in record.msg:
            self.log_colors = {"INFO": "green"}
        elif "PREVIOUSLY" in record.msg:
            self.log_colors = {"INFO": "purple"}
        else:
            self.log_colors = {"INFO": "cyan"}

        return super().format(record)


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

# script starts
script_start = time.time()

MAIN_URL = "https://www.njcourts.gov/jurors"
main_soup = utils.get_soup(MAIN_URL)
main_content = main_soup.find("div", {"id": "page-content"})
page_urls = utils.get_urls(main_content)

logger.info("Fetched Pages From %s: %s", MAIN_URL, page_urls)

pages = {}
# {
#     url: {
#         title: "title"
#         text: "text",
#         parent_pages: ["parent page", ...],
#         child_pages: ["child page", ...]
#     }, ...
# }

page_stack = [{"url": url, "parent_url": MAIN_URL} for url in page_urls]

# to prevent overscraping
# restrict going to anything under these links
# only care about /jurors for now
pages_to_ignore = [
    "https://www.njcourts.gov/self-help",
    "https://www.njcourts.gov/attorneys",
    "https://www.njmcdirect.com/",
    "https://www.njcourts.gov/courts",
    "https://www.njcourts.gov/public",
]


pages_scraped = 0
scraping_times = []

while page_stack:
    url = page_stack.pop()

    # restricts scraping of anything outside /jurors
    if any(ignored_page in url["url"] for ignored_page in pages_to_ignore) or url["url"] == "https://www.njcourts.gov/":
        logger.info("<SKIPPING PAGE>: %s", url["url"])
        continue

    if url["url"] not in pages:
        logger.info("<SCRAPING PAGE>: %s...", url["url"])

        scraping_time_start = time.time()
        page = utils.scrape_page(url["url"])

        if not page:
            continue

        page["parent_pages"] = [url["parent_url"]]
        pages[url["url"]] = page

        scraping_time_end = time.time()
        scraping_times.append(scraping_time_end - scraping_time_start)
        pages_scraped += 1

        child_pages = [{"url": child_url, "parent_url": url["url"]} for child_url in page["child_pages"]]
        page_stack.extend(child_pages)

        logger.info("<COMPLETED PAGE>: %s", url["url"])
    else:
        logger.info("<PREVIOUSLY SCRAPED PAGE>: %s", url["url"])

script_end = time.time()
total_time = str(script_end - script_start)
avg_time = str(sum(scraping_times) / pages_scraped)

logger.info("--------------------------------------------------")
logger.info("Script Total Time: %s seconds", total_time)
logger.info("Average Scraping Time Per Page: %s seconds", avg_time)
logger.info("--------------------------------------------------")

with open("scraped_data.json", "w", encoding="utf-8") as f:
    json.dump(pages, f)
