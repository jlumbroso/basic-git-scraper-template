import os
import sys

import bs4
import daily_event_monitor
import loguru
import requests


def scrape_data_point():
    req = requests.get("https://www.thedp.com")

    loguru.logger.info(f"Request URL: {req.url}")
    loguru.logger.info(f"Request status code: {req.status_code}")

    if req.ok:
        soup = bs4.BeautifulSoup(req.text, "html.parser")
        target_element = soup.find("a", class_="frontpage-link")
        data_point = "" if target_element is None else target_element.text

        loguru.logger.info(f"Data point: {data_point}")

        return data_point


# output something in "./data"
if __name__ == "__main__":
    loguru.logger.add("scrape.log", rotation="1 day")

    loguru.logger.info("Creating data directory if it does not exist")
    try:
        os.makedirs("data", exist_ok=True)
    except Exception as e:
        loguru.logger.error(f"Failed to create data directory: {e}")
        sys.exit(1)

    loguru.logger.info("Loading daily event monitor")
    dem = daily_event_monitor.DailyEventMonitor(
        "data/daily_pennsylvanian_headlines.json"
    )

    loguru.logger.info("Starting scrape")
    try:
        data_point = scrape_data_point()
    except Exception as e:
        loguru.logger.error(f"Failed to scrape data point: {e}")
        data_point = None

    if data_point is not None:
        dem.add_today(data_point)

    loguru.logger.info("Scrape complete")

    dem.save()
    loguru.logger.info("Saved daily event monitor")
    loguru.logger.info("Exiting")
