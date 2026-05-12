<a href="https://crawlbase.com/signup?utm_source=github&utm_medium=readme&utm_campaign=crawling_api_banner" target="_blank">
  <img src="https://github.com/user-attachments/assets/afa4f6e7-25fb-442c-af2f-b4ddcfd62ab2" 
       alt="crawling-api-cta" 
       style="max-width: 100%; border: 0;">
</a>



# Enterprise Web Scraping API Example

Production-style Crawlbase Crawling API integration with retries, logging, and response validation. Matches the blog post *Web Scraping API for Enterprise: What CTOs Look For*.

## Architecture

- **config.py** — Validated env config; `get_token()` fails fast with clear error if token is missing.
- **fetcher.py** — Crawling API client with tenacity retries (429, 503, timeouts), logging, and `original_status`/`pc_status` validation. Includes `fetch_page_enterprise_crawler()` for bulk push.
- **fetcher.js** — Node.js equivalent with axios + axios-retry, same patterns.
- **main.py** — CLI: fetch one URL or push to Enterprise Crawler.

## Setup

From your local clone of the repository (same layout as [GitHub](https://github.com/ScraperHub/web-scraping-api-for-enterprise-what-cto-look-for)):

```bash
cp .env.example .env   # Edit with your tokens
python3 -m venv .venv && source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
export CRAWLBASE_JS_TOKEN=your_token   # Get one at https://crawlbase.com/signup
```

## Run

```bash
# Fetch a URL (returns HTML)
python main.py https://example.com

# With page_wait for JavaScript-rendered pages
python main.py https://example.com --page-wait 2000

# With geo-targeting
python main.py https://example.com --country US

# Push to Enterprise Crawler (webhook delivery)
python main.py https://example.com --push --crawler MyCrawler
```

## Node.js

```bash
npm install
CRAWLBASE_JS_TOKEN=your_token node -e "
import('./fetcher.js').then(m =>
  m.fetchPage('https://example.com').then(html => console.log(html.slice(0, 200)))
)
"
```

## References

- [Crawlbase Crawling API](https://crawlbase.com/docs/crawling-api/)
- [Crawlbase Enterprise Crawler](https://crawlbase.com/docs/crawler)
- **Official SDKs** — [github.com/crawlbase](https://github.com/crawlbase): Python, Node.js, PHP, Ruby, Java, Scrapy middleware
