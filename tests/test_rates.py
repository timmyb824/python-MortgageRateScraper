from unittest.mock import Mock, patch

import pytest
from bs4 import BeautifulSoup

from src.scraper.rates import (
    MortgageRate,
    format_notification,
    safe_float,
    scrape_mortgage_rates,
    send_request,
)


@pytest.mark.parametrize(
    "text, expected",
    [
        ("3.5%", 3.5),
        ("0%", 0.0),
        ("", None),
        (None, None),
        ("invalid", None),
    ],
    ids=["valid_float", "zero_percent", "empty_string", "none_value", "invalid_string"],
)
def test_safe_float(text, expected):
    # Act
    result = safe_float(text)

    # Assert
    assert result == expected


@pytest.mark.parametrize(
    "url, response_status, response_text, expected",
    [
        (
            "http://valid.url",
            200,
            "<html></html>",
            Mock(status_code=200, text="<html></html>"),
        ),
        ("http://invalid.url", 404, "", None),
    ],
    ids=["valid_request", "invalid_request"],
)
@patch("src.scraper.rates.requests.get")
def test_send_request(mock_get, url, response_status, response_text, expected):
    # Arrange
    mock_response = Mock(status_code=response_status, text=response_text)
    mock_get.return_value = mock_response

    # Act
    result = send_request(url)

    # Assert
    if expected is None:
        assert result.status_code != 200
    else:
        assert result.status_code == expected.status_code
        assert result.text == expected.text


@pytest.mark.parametrize(
    "html_content, expected_rates",
    [
        (
            """
            <div class="rate-product">
                <div class="rate-product-name">30 Year Fixed</div>
                <div class="rate">3.5%</div>
                <div class="change">+0.1</div>
            </div>
            """,
            [MortgageRate(type="30 Year Fixed", rate=3.5, change=0.1)],
        ),
        (
            """
            <div class="rate-product">
                <div class="rate-product-name">15 Year Fixed</div>
                <div class="rate">2.75%</div>
                <div class="change">-0.05</div>
            </div>
            """,
            [MortgageRate(type="15 Year Fixed", rate=2.75, change=-0.05)],
        ),
        ("", []),
    ],
    ids=["single_rate", "another_single_rate", "empty_html"],
)
@patch("src.scraper.rates.send_request")
def test_scrape_mortgage_rates(mock_send_request, html_content, expected_rates):
    # Arrange
    mock_response = Mock(text=html_content)
    mock_send_request.return_value = mock_response

    # Act
    result = scrape_mortgage_rates()

    # Assert
    assert result == expected_rates


@pytest.mark.parametrize(
    "rates, expected_notification",
    [
        (
            [MortgageRate(type="30 Year Fixed", rate=3.5, change=0.1)],
            "30 Year Fixed: 3.50% (+0.10)\n",
        ),
        (
            [MortgageRate(type="15 Year Fixed", rate=2.75, change=-0.05)],
            "15 Year Fixed: 2.75% (-0.05)\n",
        ),
        ([MortgageRate(type="5/1 ARM", rate=3.0, change=0.0)], ""),
        ([], ""),
    ],
    ids=["single_rate", "another_single_rate", "arm_rate", "empty_rates"],
)
def test_format_notification(rates, expected_notification):
    # Act
    result = format_notification(rates)

    # Assert
    assert result == expected_notification
