from dataclasses import dataclass
from typing import Optional

import requests
from bs4 import BeautifulSoup

from src.logs.log_handler import logger


@dataclass
class MortgageRate:
    type: str
    rate: Optional[float]
    change: Optional[float]


def safe_float(text: str) -> Optional[float]:
    try:
        return float(text.strip().rstrip("%"))
    except (ValueError, AttributeError):
        return None


def send_request(url: str) -> Optional[requests.Response]:
    try:
        logger.info(f"Sending request to {url}")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        logger.error(f"An error occurred: {str(e)}")
        return None


def scrape_mortgage_rates() -> list[MortgageRate]:
    url = "https://www.mortgagenewsdaily.com/mortgage-rates"
    response = send_request(url)
    if response is None:
        return []

    soup = BeautifulSoup(response.text, "html.parser")

    rates = []

    # Find all rate product divs
    rate_products = soup.find_all("div", class_="rate-product")

    for product in rate_products:
        # Extract rate type
        rate_type_elem = product.find("div", class_="rate-product-name")
        rate_type = rate_type_elem.text.strip() if rate_type_elem else "Unknown"

        # Extract rate
        rate_div = product.find("div", class_="rate")
        rate = safe_float(rate_div.text) if rate_div else None

        # Extract change (you may need to adjust this based on actual HTML structure)
        change_div = product.find("div", class_="change")
        change = safe_float(change_div.text) if change_div else None

        rates.append(MortgageRate(type=rate_type, rate=rate, change=change))

    return rates


def format_notification(rates: list[MortgageRate]) -> str:
    notification = ""
    for rate in rates:
        if rate.rate is None or "ARM" in rate.type:
            continue
        rate_str = f"{rate.rate:.2f}%" if rate.rate is not None else "N/A"
        change_str = f"({rate.change:+.2f})" if rate.change is not None else ""
        notification += f"{rate.type}: {rate_str} {change_str}\n"
    return notification
