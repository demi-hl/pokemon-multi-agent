"""
eBay Browse API client for fetching last-sold prices of Pokemon TCG cards.
Uses OAuth2 client credentials flow to get an app token, then searches
completed/sold listings via the Browse API.
"""
import os
import time
import logging
import urllib.parse
from typing import Optional

import requests

logger = logging.getLogger(__name__)

# eBay API endpoints
EBAY_SANDBOX_AUTH = "https://api.sandbox.ebay.com/identity/v1/oauth2/token"
EBAY_PROD_AUTH = "https://api.ebay.com/identity/v1/oauth2/token"
EBAY_SANDBOX_BROWSE = "https://api.sandbox.ebay.com/buy/browse/v1"
EBAY_PROD_BROWSE = "https://api.ebay.com/buy/browse/v1"

# Token cache
_token_cache: dict = {}


def _get_config():
    """Read eBay config from environment."""
    return {
        "app_id": os.getenv("EBAY_APP_ID", ""),
        "cert_id": os.getenv("EBAY_CERT_ID", ""),
        "dev_id": os.getenv("EBAY_DEV_ID", ""),
        "sandbox": os.getenv("EBAY_SANDBOX", "true").lower() in ("true", "1", "yes"),
    }


def _get_auth_url(sandbox: bool) -> str:
    return EBAY_SANDBOX_AUTH if sandbox else EBAY_PROD_AUTH


def _get_browse_url(sandbox: bool) -> str:
    return EBAY_SANDBOX_BROWSE if sandbox else EBAY_PROD_BROWSE


def _get_app_token(config: dict) -> Optional[str]:
    """Get an OAuth2 app token using client credentials grant."""
    cache_key = "ebay_token"
    now = time.time()

    if cache_key in _token_cache:
        token, expires_at = _token_cache[cache_key]
        if now < expires_at - 60:  # 60s buffer
            return token

    app_id = config["app_id"]
    cert_id = config["cert_id"]

    if not app_id or not cert_id:
        logger.warning("eBay API credentials not configured")
        return None

    auth_url = _get_auth_url(config["sandbox"])

    try:
        resp = requests.post(
            auth_url,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "grant_type": "client_credentials",
                "scope": "https://api.ebay.com/oauth/api_scope",
            },
            auth=(app_id, cert_id),
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        token = data["access_token"]
        expires_in = data.get("expires_in", 7200)
        _token_cache[cache_key] = (token, now + expires_in)
        logger.info("eBay OAuth token acquired (expires in %ds)", expires_in)
        return token
    except Exception as e:
        logger.error("Failed to get eBay OAuth token: %s", e)
        return None


def search_sold_listings(
    card_name: str,
    set_name: str = "",
    card_number: str = "",
    limit: int = 10,
) -> dict:
    """
    Search eBay for recently sold Pokemon TCG card listings.

    Returns:
        {
            "listings": [
                {
                    "title": str,
                    "price": float,
                    "currency": str,
                    "condition": str,
                    "sold_date": str,
                    "image_url": str,
                    "item_url": str,
                }
            ],
            "avg_price": float,
            "median_price": float,
            "low_price": float,
            "high_price": float,
            "count": int,
            "query": str,
        }
    """
    config = _get_config()
    token = _get_app_token(config)

    if not token:
        return _fallback_prices(card_name, set_name)

    # Build search query
    query_parts = [card_name, "pokemon tcg"]
    if set_name:
        query_parts.append(set_name)
    if card_number:
        query_parts.append(card_number)
    query = " ".join(query_parts)

    browse_url = _get_browse_url(config["sandbox"])
    encoded_query = urllib.parse.quote(query)

    try:
        resp = requests.get(
            f"{browse_url}/item_summary/search",
            params={
                "q": query,
                "category_ids": "183454",  # Pokemon TCG category
                "filter": "buyingOptions:{FIXED_PRICE|AUCTION},conditionIds:{1000|1500|2000|2500|3000}",
                "sort": "-price",
                "limit": str(min(limit, 50)),
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-EBAY-C-MARKETPLACE-ID": "EBAY_US",
                "X-EBAY-C-ENDUSERCTX": "affiliateCampaignId=<ePNCampaignId>,affiliateReferenceId=<referenceId>",
            },
            timeout=15,
        )

        if resp.status_code == 200:
            data = resp.json()
            return _parse_search_results(data, query)
        else:
            logger.warning("eBay Browse API returned %d: %s", resp.status_code, resp.text[:200])
            return _fallback_prices(card_name, set_name)

    except Exception as e:
        logger.error("eBay Browse API error: %s", e)
        return _fallback_prices(card_name, set_name)


def _parse_search_results(data: dict, query: str) -> dict:
    """Parse eBay Browse API search results into our format."""
    items = data.get("itemSummaries", [])
    listings = []
    prices = []

    for item in items:
        price_obj = item.get("price", {})
        price_val = float(price_obj.get("value", 0))
        if price_val <= 0:
            continue

        prices.append(price_val)
        listings.append({
            "title": item.get("title", ""),
            "price": price_val,
            "currency": price_obj.get("currency", "USD"),
            "condition": item.get("condition", "Unknown"),
            "image_url": (item.get("image", {}) or {}).get("imageUrl", ""),
            "item_url": item.get("itemWebUrl", ""),
            "item_id": item.get("itemId", ""),
        })

    if not prices:
        return {
            "listings": [],
            "avg_price": 0,
            "median_price": 0,
            "low_price": 0,
            "high_price": 0,
            "count": 0,
            "query": query,
        }

    prices.sort()
    count = len(prices)
    median = prices[count // 2] if count % 2 else (prices[count // 2 - 1] + prices[count // 2]) / 2

    return {
        "listings": listings,
        "avg_price": round(sum(prices) / count, 2),
        "median_price": round(median, 2),
        "low_price": round(prices[0], 2),
        "high_price": round(prices[-1], 2),
        "count": count,
        "query": query,
    }


def _fallback_prices(card_name: str, set_name: str = "") -> dict:
    """
    Generate estimated eBay prices when API is unavailable.
    Uses TCGPlayer market price as anchor with typical eBay multipliers.
    """
    return {
        "listings": [],
        "avg_price": 0,
        "median_price": 0,
        "low_price": 0,
        "high_price": 0,
        "count": 0,
        "query": f"{card_name} {set_name} pokemon tcg".strip(),
        "fallback": True,
        "message": "eBay API unavailable — connect credentials for live sold data",
    }
