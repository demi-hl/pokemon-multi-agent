"""
Firecrawl-powered stock scanner for Pokemon TCG products across retailers.

Uses Firecrawl to scrape retailer search pages and extract real-time
stock/price data from Target, Walmart, Best Buy, GameStop, and Pokemon Center.
"""
import os
import re
import logging
from typing import Optional
from firecrawl import FirecrawlApp

logger = logging.getLogger(__name__)

FIRECRAWL_API_KEY = os.environ.get("FIRECRAWL_API_KEY", "")

# Retailer search URL templates
RETAILER_URLS = {
    "target": "https://www.target.com/s?searchTerm={query}+pokemon+tcg",
    "walmart": "https://www.walmart.com/search?q={query}+pokemon+tcg",
    "bestbuy": "https://www.bestbuy.com/site/searchpage.jsp?st={query}+pokemon+tcg",
    "gamestop": "https://www.gamestop.com/search/?q={query}+pokemon+tcg",
    "pokemoncenter": "https://www.pokemoncenter.com/search/{query}%20pokemon%20tcg",
}

RETAILER_DISPLAY = {
    "target": "Target",
    "walmart": "Walmart",
    "bestbuy": "Best Buy",
    "gamestop": "GameStop",
    "pokemoncenter": "Pokemon Center",
}


def _get_client() -> Optional[FirecrawlApp]:
    """Return a Firecrawl client or None if no API key is configured."""
    if not FIRECRAWL_API_KEY:
        return None
    return FirecrawlApp(api_key=FIRECRAWL_API_KEY)


def _extract_products_from_markdown(markdown: str, retailer: str) -> list[dict]:
    """Parse Firecrawl markdown output into structured product results.

    Uses regex patterns to find product names, prices, and stock indicators
    from the scraped markdown content.
    """
    products = []

    # Find price patterns like $49.99, $143.64
    price_pattern = re.compile(r'\$(\d+\.?\d*)')

    # Split into chunks that look like product listings
    # Look for lines with prices and pokemon-related keywords
    lines = markdown.split('\n')

    current_product: dict = {}

    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            if current_product.get('name'):
                products.append(current_product)
                current_product = {}
            continue

        # Skip navigation, footer, cookie banners
        skip_keywords = ['sign in', 'log in', 'cookie', 'privacy', 'cart', 'menu',
                        'footer', 'copyright', 'customer service', 'help center',
                        'terms', 'accessibility']
        if any(kw in line_stripped.lower() for kw in skip_keywords):
            continue

        # Look for pokemon TCG product names
        pokemon_keywords = ['pokemon', 'booster', 'elite trainer', 'etb', 'collection',
                          'bundle', 'tin', 'blister', 'pack', 'box', 'premium',
                          'ultra premium', 'upc', 'scarlet', 'violet', 'paldean',
                          'prismatic', 'surging', 'obsidian', 'paradox', 'temporal',
                          'journey', 'crown', 'evolving', 'celebrations', 'fusion',
                          'brilliant', 'astral', 'lost origin', 'silver tempest']

        has_pokemon = any(kw in line_stripped.lower() for kw in pokemon_keywords)
        price_match = price_pattern.search(line_stripped)

        if has_pokemon and len(line_stripped) > 10 and not current_product.get('name'):
            # Clean up markdown formatting
            name = re.sub(r'[\[\]#*`]', '', line_stripped).strip()
            # Remove URL parts
            name = re.sub(r'\(https?://[^\)]+\)', '', name).strip()
            if len(name) > 5:
                current_product['name'] = name
                current_product['retailer'] = RETAILER_DISPLAY.get(retailer, retailer)
                current_product['retailer_id'] = retailer

        if price_match and current_product.get('name') and not current_product.get('price'):
            price_val = float(price_match.group(1))
            if 1.0 < price_val < 1000.0:  # Reasonable Pokemon TCG price range
                current_product['price'] = price_val

        # Stock indicators
        stock_positive = ['add to cart', 'in stock', 'available', 'buy now',
                         'ship', 'pickup', 'delivery']
        stock_negative = ['out of stock', 'sold out', 'unavailable', 'not available',
                         'coming soon', 'pre-order']

        lower = line_stripped.lower()
        if current_product.get('name'):
            if any(kw in lower for kw in stock_negative):
                current_product['in_stock'] = False
            elif any(kw in lower for kw in stock_positive):
                current_product['in_stock'] = True

    # Don't forget the last product
    if current_product.get('name'):
        products.append(current_product)

    # Deduplicate and clean
    seen_names: set[str] = set()
    unique_products = []
    for p in products:
        name_key = p['name'][:50].lower()
        if name_key not in seen_names:
            seen_names.add(name_key)
            # Default stock to True if we couldn't determine
            if 'in_stock' not in p:
                p['in_stock'] = True
            if 'price' not in p:
                p['price'] = None
            unique_products.append(p)

    return unique_products[:20]  # Cap at 20 results per retailer


def scan_retailer(query: str, retailer: str) -> dict:
    """Scan a single retailer for Pokemon TCG products matching the query.

    Returns {"retailer": str, "products": list, "error": str|None}
    """
    client = _get_client()
    if not client:
        return {
            "retailer": RETAILER_DISPLAY.get(retailer, retailer),
            "retailer_id": retailer,
            "products": [],
            "error": "Firecrawl API key not configured. Set FIRECRAWL_API_KEY env var.",
        }

    url_template = RETAILER_URLS.get(retailer)
    if not url_template:
        return {
            "retailer": retailer,
            "retailer_id": retailer,
            "products": [],
            "error": f"Unknown retailer: {retailer}",
        }

    url = url_template.format(query=query.replace(' ', '+'))

    try:
        result = client.scrape_url(
            url,
            params={
                "formats": ["markdown"],
                "waitFor": 3000,  # Wait for JS rendering
                "timeout": 15000,
            },
        )

        markdown = result.get("markdown", "") if isinstance(result, dict) else getattr(result, 'markdown', '')
        if not markdown:
            return {
                "retailer": RETAILER_DISPLAY.get(retailer, retailer),
                "retailer_id": retailer,
                "products": [],
                "error": "No content returned from scrape",
            }

        products = _extract_products_from_markdown(markdown, retailer)

        return {
            "retailer": RETAILER_DISPLAY.get(retailer, retailer),
            "retailer_id": retailer,
            "products": products,
            "error": None,
        }

    except Exception as exc:
        logger.error("scan_retailer: %s failed for query '%s': %s", retailer, query, exc)
        return {
            "retailer": RETAILER_DISPLAY.get(retailer, retailer),
            "retailer_id": retailer,
            "products": [],
            "error": str(exc),
        }


def scan_all_retailers(query: str, retailers: Optional[list[str]] = None) -> list[dict]:
    """Scan multiple retailers in sequence.

    If retailers is None, scans all supported retailers.
    Returns a list of retailer result dicts.
    """
    if retailers is None:
        retailers = list(RETAILER_URLS.keys())

    results = []
    for retailer in retailers:
        result = scan_retailer(query, retailer)
        results.append(result)

    return results
