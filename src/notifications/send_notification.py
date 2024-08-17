import os

import apprise

from src.logs.log_handler import logger


def send_notification(message: str) -> None:
    """Send notification using Apprise with environment variables."""

    apobj = apprise.Apprise()
    # Add all services from environment variables
    for key, value in os.environ.items():
        if key.startswith("APPRISE_"):
            logger.info(f"Adding {key} to notification")
            apobj.add(value)
    apobj.notify(body=message, title="Current Mortgage Rates")
    logger.info("Notification sent successfully")
