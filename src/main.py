import os
import time

import schedule

from src.healthcheck import send_health_check
from src.logs.log_handler import logger
from src.notifications.send_notification import send_notification
from src.scraper.rates import format_notification, scrape_mortgage_rates

HEALTHCHECK_URL = os.getenv("HEALTHCHECK_URL")


def main():
    try:
        if mortgage_rates := scrape_mortgage_rates():
            logger.info(f"Mortgage rate(s) found: {mortgage_rates}")
            notification_message = format_notification(mortgage_rates)
            send_notification(notification_message)

            if HEALTHCHECK_URL:
                send_health_check(HEALTHCHECK_URL)
        else:
            logger.info(
                "No mortgage rates were found. The website structure may have changed."
            )
    except Exception as e:
        print(f"An error occurred: {str(e)}")


def run_scheduler():
    # schedule.every(5).seconds.do(main) # for testing
    schedule.every().day.at("09:00", "America/New_York").do(main)
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    logger.info("Starting mortgage rate scraper")
    run_scheduler()
