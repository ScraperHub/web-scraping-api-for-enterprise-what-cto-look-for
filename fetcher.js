/**
 * Crawlbase Crawling API client with retries, logging, and response validation.
 * @module fetcher
 */

import axios from "axios";
import axiosRetry from "axios-retry";

const CRAWLBASE_API_BASE = "https://api.crawlbase.com/";
const DEFAULT_TIMEOUT_SECONDS = 90;
const MIN_RESPONSE_LENGTH = 100;
const RETRY_ATTEMPTS = 3;

/**
 * Get Crawlbase token from environment. Fails fast if missing.
 * @param {boolean} useJs - If true, use CRAWLBASE_JS_TOKEN; else CRAWLBASE_TOKEN
 * @returns {string}
 * @throws {Error} When token is not set
 */
function getToken(useJs = true) {
  const varName = useJs ? "CRAWLBASE_JS_TOKEN" : "CRAWLBASE_TOKEN";
  const token = process.env[varName];
  if (!token || !String(token).trim()) {
    throw new Error(
      `${varName} is not set. Set it in your environment or .env file. ` +
        "Get a token at https://crawlbase.com/signup"
    );
  }
  return String(token).trim();
}

const client = axios.create({
  baseURL: CRAWLBASE_API_BASE,
  timeout: DEFAULT_TIMEOUT_SECONDS * 1000,
  validateStatus: (status) => status >= 200 && status < 300,
});

axiosRetry(client, {
  retries: RETRY_ATTEMPTS,
  retryDelay: axiosRetry.exponentialDelay,
  retryCondition: (error) => {
    if (axiosRetry.isNetworkOrIdempotentRequestError(error)) return true;
    if (error.response?.status === 429 || error.response?.status === 503)
      return true;
    return false;
  },
});

/**
 * Request page HTML from Crawlbase Crawling API with automatic retries.
 *
 * @param {string} url - Target URL to fetch
 * @param {Object} options - Optional parameters
 * @param {string} [options.token] - API token (default: from env)
 * @param {number} [options.pageWait] - Milliseconds to wait for dynamic content
 * @param {string} [options.country] - Two-letter country code (e.g., "US")
 * @param {boolean} [options.useJs=true] - Use JavaScript token
 * @returns {Promise<string>} Raw HTML string
 */
export async function fetchPage(url, options = {}) {
  const { token, pageWait, country, useJs = true } = options;
  const apiToken = token ?? getToken(useJs);

  const params = {
    token: apiToken,
    url,
  };
  if (pageWait != null) params.page_wait = pageWait;
  if (country) params.country = country.toUpperCase();

  const start = Date.now();
  const response = await client.get("", { params, responseType: "text" });

  const durationMs = Date.now() - start;
  const originalStatus = response.headers["original_status"] ?? "N/A";
  const pcStatus = response.headers["pc_status"] ?? "N/A";

  const text = response.data;
  if (!text || String(text).trim().length < MIN_RESPONSE_LENGTH) {
    throw new Error(`Empty or too small response for ${url.slice(0, 80)}`);
  }

  console.info(
    `Fetched ${url.slice(0, 80)} in ${durationMs}ms (original_status=${originalStatus}, pc_status=${pcStatus})`
  );
  return typeof text === "string" ? text : String(text);
}

/**
 * Push URL to Crawlbase Enterprise Crawler (async, webhook delivery).
 *
 * @param {string} url - Target URL to crawl
 * @param {string} crawlerName - Name of your Enterprise Crawler
 * @param {Object} options - Optional parameters
 * @param {string} [options.token] - API token (default: from env)
 * @param {number} [options.pageWait] - Milliseconds to wait for dynamic content
 * @param {string} [options.country] - Two-letter country code
 * @param {boolean} [options.useJs=true] - Use JavaScript token
 * @returns {Promise<Object>} JSON response with rid and status
 */
export async function fetchPageEnterpriseCrawler(url, crawlerName, options = {}) {
  const { token, pageWait, country, useJs = true } = options;
  const apiToken = token ?? getToken(useJs);

  const params = {
    token: apiToken,
    url,
    callback: true,
    crawler: crawlerName,
  };
  if (pageWait != null) params.page_wait = pageWait;
  if (country) params.country = country.toUpperCase();

  console.info(`Pushing URL to Enterprise Crawler ${crawlerName}: ${url.slice(0, 80)}`);

  const response = await client.get("", { params, responseType: "json" });
  const data = response.data;
  console.info("Pushed to crawler, rid=%s", data.rid ?? "N/A");
  return data;
}
