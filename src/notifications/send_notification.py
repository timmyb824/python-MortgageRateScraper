import os

import apprise

from src.logs.log_handler import logger


def send_notification(message: str, title: str = "Current Mortgage Rates") -> None:
    """Send notification using Apprise with environment variables."""

    apobj = apprise.Apprise()
    # Add all services from environment variables
    for key, value in os.environ.items():
        if key.startswith("APPRISE_"):
            logger.info(f"Adding {key} to notification")
            apobj.add(value)
    try:
        if _ := apobj.notify(body=message, title=title):
            logger.info("Notification sent successfully")
        else:
            logger.error("Apprise notification failed to send")
    except Exception as e:
        logger.error(f"Exception occurred while sending notification: {e}")
