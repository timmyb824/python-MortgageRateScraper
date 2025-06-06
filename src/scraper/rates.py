import re
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
    """Convert text to a float, safely handling errors."""
    try:
        return float(text.strip().rstrip("%"))
    except (ValueError, AttributeError):
        return None


def send_request(url: str) -> Optional[requests.Response]:
    """Send an HTTP GET request and handle errors."""
    try:
        logger.info(f"Sending request to {url}")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        logger.error(f"An error occurred: {str(e)}")
        return None


def parse_primary_mortgage_rates(soup: BeautifulSoup) -> list[MortgageRate]:
    """Parse the primary source for mortgage rates."""
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

        # Extract change
        change_div = product.find("div", class_="change")
        change = safe_float(change_div.text) if change_div else None

        rates.append(MortgageRate(type=rate_type, rate=rate, change=change))

    return rates


# def parse_freddie_mac_html(soup: BeautifulSoup) -> list[MortgageRate]:
#     # sourcery skip: extract-method
#     """Parse the Freddie Mac PMMS page to extract mortgage rates."""
#     rates = []
#     try:
#         # Extract the headline and date
#         headline = soup.find("h3").get_text(strip=True)
#         date = soup.find("h5").get_text(strip=True)

#         # Log these for reference
#         logger.info(f"Freddie Mac headline: {headline}")
#         logger.info(f"Freddie Mac date: {date}")

#         # Extract rate data from the Excel file link
#         excel_link = soup.find(
#             "a", href=True, text="Current Mortgage Rates Data Since 1971"
#         )
#         excel_url = (
#             f"https://www.freddiemac.com{excel_link['href']}" if excel_link else None
#         )

#         if excel_url:
#             logger.info(f"Excel file URL: {excel_url}")
#             rates.append(MortgageRate(type="Excel Data Link", rate=None, change=None))
#         else:
#             logger.warning("Excel file link not found.")
#     except Exception as e:
#         logger.error(f"Error parsing Freddie Mac HTML: {e}")
#     return rates


def parse_fred_mortgage_rate(soup: BeautifulSoup) -> list[MortgageRate]:
    """Parse the FRED page to extract the 30-year fixed mortgage rate."""
    rates = []
    try:
        if value_span := soup.find("span", class_="series-meta-observation-value"):
            rate = value_span.get_text(strip=True)
            rates.append(
                MortgageRate(type="30-Year Fixed", rate=safe_float(rate), change=None)
            )
            logger.info(f"Extracted FRED rate: {rate}")
        else:
            logger.error("Unable to locate the current rate value on FRED.")
    except Exception as e:
        logger.error(f"Error parsing FRED HTML: {e}")
    return rates


def scrape_mortgage_rates() -> list[MortgageRate]:
    # sourcery skip: use-named-expression
    """Scrape mortgage rates from multiple sources with fallback logic."""
    primary_url = "https://www.mortgagenewsdaily.com/mortgage-rates"
    fallback_url = "https://fred.stlouisfed.org/series/MORTGAGE30US"  # "https://www.freddiemac.com/pmms"

    # Try the primary source
    response = send_request(primary_url)
    # response = ""  # for testing backup
    if response:
        soup = BeautifulSoup(response.text, "html.parser")
        if rates := parse_primary_mortgage_rates(soup):
            logger.info("Successfully retrieved rates from the primary source.")
            return rates
        else:
            logger.warning("Primary source returned no usable data.")

    # Fallback to Freddie Mac PMMS if the primary source fails
    logger.warning(f"Primary source failed, falling back to {fallback_url}")
    response = send_request(fallback_url)
    if response:
        soup = BeautifulSoup(response.text, "html.parser")
        if rates := parse_fred_mortgage_rate(soup):
            logger.info("Successfully retrieved rates from FRED.")
            return rates
        else:
            logger.warning("FRED returned no usable data.")

    # If all sources fail, return an empty list
    logger.error("Both primary and fallback sources failed.")
    return []


def format_notification(rates: list[MortgageRate]) -> str:
    """Format the scraped mortgage rates for notification."""
    notification = ""
    for rate in rates:
        if rate.rate is None or "ARM" in rate.type:
            continue
        # Remove all types of quotes (straight and curly) from the rate type
        clean_type = re.sub(
            r"[\"\'“”‘’]", "", rate.type
        )  # Remove all quote-like characters
        clean_type = clean_type.replace(
            ":", ""
        ).strip()  # Also remove colons from type just to be safe
        rate_str = f"{rate.rate:.2f}%" if rate.rate is not None else "N/A"
        change_str = f"({rate.change:+.2f})" if rate.change is not None else ""
        logger.debug(f"Formatting: type='{rate.type}', cleaned='{clean_type}'")
        notification += f"{clean_type}: {rate_str} {change_str}\n"
    return notification
