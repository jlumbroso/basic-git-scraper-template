import os
import sys

import bs4
import daily_event_monitor
import loguru
import requests


def scrape_data_point():
    req = requests.get("https://www.thedp.com")
    if req.ok:
        soup = bs4.BeautifulSoup(req.text, "html.parser")
        data_point = soup.find("a", class_="frontpage-link")
        return data_point.text


# output something in "./data"
if __name__ == "__main__":
    try:
        os.makedirs("data", exist_ok=True)
    except Exception as e:
        loguru.logger.error(f"Failed to create data directory: {e}")
        sys.exit(1)

    dem = daily_event_monitor.DailyEventMonitor(
        "data/daily_pennsylvanian_headlines.csv"
    )
    try:
        data_point = scrape_data_point()
    except Exception as e:
        loguru.logger.error(f"Failed to scrape data point: {e}")
        data_point = None

    if data_point is not None:
        dem.add_today(data_point)
