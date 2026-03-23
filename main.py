"""
CLI for Crawlbase Crawling API: fetch a URL or push to Enterprise Crawler.

Usage:
    python main.py https://example.com
    python main.py https://example.com --page-wait 2000
    python main.py https://example.com --push --crawler MyCrawler
"""

import argparse
import json
import logging
import sys

from config import LOG_LEVEL, get_token
from fetcher import fetch_page, fetch_page_enterprise_crawler

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fetch a URL via Crawlbase Crawling API or push to Enterprise Crawler.",
    )
    parser.add_argument("url", help="URL to fetch or push")
    parser.add_argument(
        "--push",
        action="store_true",
        help="Push to Enterprise Crawler (webhook delivery) instead of fetching",
    )
    parser.add_argument(
        "--crawler",
        default="",
        help="Enterprise Crawler name (required when using --push)",
    )
    parser.add_argument(
        "--page-wait",
        type=int,
        default=2000,
        help="Milliseconds to wait for dynamic content (default: 2000)",
    )
    parser.add_argument(
        "--country",
        default=None,
        help="Country code for geo-targeting (e.g., US)",
    )
    args = parser.parse_args()

    url = args.url.strip()
    if not url.startswith(("http://", "https://")):
        logger.error("URL must start with http:// or https://")
        return 1

    if args.push and not args.crawler:
        logger.error("--crawler is required when using --push")
        return 1

    try:
        get_token()
    except ValueError as e:
        logger.error("%s", e)
        return 1

    try:
        if args.push:
            result = fetch_page_enterprise_crawler(
                url,
                args.crawler,
                page_wait=args.page_wait,
                country=args.country,
            )
            print(json.dumps(result, indent=2))
            logger.info("Successfully pushed to crawler %s", args.crawler)
        else:
            html = fetch_page(
                url,
                page_wait=args.page_wait,
                country=args.country,
            )
            print(html[:500] + "..." if len(html) > 500 else html)
            logger.info("Successfully fetched %d bytes", len(html))
    except Exception as e:
        logger.exception("Request failed: %s", e)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
