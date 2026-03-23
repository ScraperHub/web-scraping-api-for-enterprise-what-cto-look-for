"""Crawlbase Crawling API client with retries, logging, and response validation."""

import logging
import time
from typing import Optional

import requests
from tenacity import (
    retry,
    retry_if_exception,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from config import (
    CRAWLBASE_API_BASE,
    DEFAULT_TIMEOUT_SECONDS,
    MIN_RESPONSE_LENGTH,
    RETRY_ATTEMPTS,
    RETRY_MAX_WAIT_SECONDS,
    RETRY_MIN_WAIT_SECONDS,
    get_token,
)

logger = logging.getLogger(__name__)


def _should_retry_http(exc: BaseException) -> bool:
    """Retry on 429 (rate limit) or 503 (service unavailable)."""
    if isinstance(exc, requests.HTTPError) and exc.response is not None:
        return exc.response.status_code in (429, 503)
    return False


@retry(
    stop=stop_after_attempt(RETRY_ATTEMPTS),
    wait=wait_exponential(
        min=RETRY_MIN_WAIT_SECONDS,
        max=RETRY_MAX_WAIT_SECONDS,
    ),
    retry=retry_if_exception_type((ConnectionError, requests.Timeout))
    | retry_if_exception(_should_retry_http),
    reraise=True,
)
def fetch_page(
    url: str,
    *,
    token: Optional[str] = None,
    page_wait: Optional[int] = None,
    country: Optional[str] = None,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
    use_js: bool = True,
) -> str:
    """Request page HTML from Crawlbase Crawling API with automatic retries.

    Retries on 429, 503, ConnectionError, and Timeout with exponential backoff.
    Logs request URL, attempt number, and duration.

    Args:
        url: Target URL to fetch.
        token: API token (default: from env via get_token).
        page_wait: Milliseconds to wait for dynamic content (JS token only).
        country: Two-letter country code for geo-targeting (e.g., "US").
        timeout: Request timeout in seconds.
        use_js: Use JavaScript token for JS-rendered pages.

    Returns:
        Raw HTML string.

    Raises:
        ValueError: Empty or too-small response.
        requests.RequestException: On HTTP errors after retries exhausted.
    """
    token = token or get_token(use_js=use_js)
    params: dict[str, str | int | bool] = {
        "token": token,
        "url": url,
    }
    if page_wait is not None:
        params["page_wait"] = page_wait
    if country:
        params["country"] = country.upper()

    start = time.perf_counter()
    resp = requests.get(
        CRAWLBASE_API_BASE,
        params=params,
        timeout=timeout,
    )
    duration_ms = (time.perf_counter() - start) * 1000

    # Check Crawlbase original_status header for upstream response
    original_status = resp.headers.get("original_status", "")
    pc_status = resp.headers.get("pc_status", "")

    resp.raise_for_status()

    text = resp.text
    if not text or len(text.strip()) < MIN_RESPONSE_LENGTH:
        logger.warning(
            "Empty or too small response for %s (original_status=%s, pc_status=%s)",
            url[:80],
            original_status,
            pc_status,
        )
        raise ValueError("Empty or too small response")

    logger.info(
        "Fetched %s in %.0fms (original_status=%s, pc_status=%s)",
        url[:80],
        duration_ms,
        original_status or "N/A",
        pc_status or "N/A",
    )
    return text


def fetch_page_enterprise_crawler(
    url: str,
    crawler_name: str,
    *,
    token: Optional[str] = None,
    page_wait: Optional[int] = None,
    country: Optional[str] = None,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
    use_js: bool = True,
) -> dict:
    """Push URL to Crawlbase Enterprise Crawler (async, webhook delivery).

    Add callback=true and crawler=Name to receive results via webhook.
    Returns Request ID (rid) immediately; HTML delivered to your webhook later.

    Args:
        url: Target URL to crawl.
        crawler_name: Name of your Enterprise Crawler (configured in dashboard).
        token: API token (default: from env).
        page_wait: Milliseconds to wait for dynamic content.
        country: Two-letter country code for geo-targeting.
        timeout: Request timeout in seconds.
        use_js: Use JavaScript token.

    Returns:
        JSON response with rid (request ID) and status.

    See: https://crawlbase.com/docs/crawler
    """
    token = token or get_token(use_js=use_js)
    params: dict[str, str | int | bool] = {
        "token": token,
        "url": url,
        "callback": True,
        "crawler": crawler_name,
    }
    if page_wait is not None:
        params["page_wait"] = page_wait
    if country:
        params["country"] = country.upper()

    logger.info("Pushing URL to Enterprise Crawler %s: %s", crawler_name, url[:80])

    resp = requests.get(
        CRAWLBASE_API_BASE,
        params=params,
        timeout=timeout,
    )
    resp.raise_for_status()
    data = resp.json()
    logger.info("Pushed to crawler, rid=%s", data.get("rid", "N/A"))
    return data
