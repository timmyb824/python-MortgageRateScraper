import requests

from src.logs.log_handler import logger


def send_health_check(url: str) -> None:
    """Send a health check signal to the healthchecks.io endpoint."""
    try:
        response = requests.get(url, timeout=15)
        if response.status_code != 200:
            logger.error(
                f"Failed to send health check signal. Status code: {response.status_code}"
            )
        logger.info(f"Health check signal sent to {url}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send health check signal. Exception: {e}")
