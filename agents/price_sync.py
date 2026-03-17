"""
Price sync service for the Pokemon TCG multi-agent system.

Pulls card/set prices from the Pokemon TCG API, records price snapshots
for chart data, computes graded price estimates via multipliers, and
syncs sealed-product prices.
"""

import os
import time
import logging
import requests
from datetime import datetime
from typing import Optional

from db.connection import get_connection, init_db
from db import queries

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Pokemon TCG API
TCG_API_BASE = "https://api.pokemontcg.io/v2"
TCG_API_KEY = os.environ.get("POKEMON_TCG_API_KEY", "")

# External price tracker API
PRICE_API_URL = os.environ.get("POKEMON_PRICE_API_URL", "")
PRICE_API_KEY = os.environ.get("POKEMON_PRICE_API_KEY", "")

# Timeouts and rate limiting
REQUEST_TIMEOUT = 10  # seconds
RATE_LIMIT_DELAY = 0.5  # seconds between API requests

# Grade multipliers applied to raw market price when real graded data is
# unavailable.  Keys match the column names in card_price_history.
GRADE_MULTIPLIERS = {
    "psa10": 2.5,
    "psa9": 1.5,
    "psa8": 1.1,
    "cgc10": 2.2,
    "cgc95": 1.6,
    "cgc9": 1.3,
    "bgs10": 3.0,
    "bgs95": 1.8,
    "bgs9": 1.4,
}

# Maps multiplier keys to (grader, grade, grade_label) for upsert_graded_price
_GRADE_KEY_MAP = {
    "psa10": ("PSA", "10", "Gem Mint"),
    "psa9":  ("PSA", "9", "Mint"),
    "psa8":  ("PSA", "8", "NM-MT"),
    "cgc10": ("CGC", "10", "Pristine"),
    "cgc95": ("CGC", "9.5", "Gem Mint"),
    "cgc9":  ("CGC", "9", "Mint"),
    "bgs10": ("BGS", "10", "Black Label"),
    "bgs95": ("BGS", "9.5", "Gem Mint"),
    "bgs9":  ("BGS", "9", "Mint"),
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _tcg_headers() -> dict:
    """Return headers for the Pokemon TCG API, including the API key when set."""
    headers = {"Accept": "application/json"}
    if TCG_API_KEY:
        headers["X-Api-Key"] = TCG_API_KEY
    return headers


def _extract_market_price(tcgplayer_prices: dict) -> Optional[float]:
    """Pick the best available market price from a tcgplayer.prices dict.

    Tries holofoil -> reverseHolofoil -> normal in order of collector
    preference, returning the first ``market`` value found.
    """
    for variant in ("holofoil", "reverseHolofoil", "normal"):
        variant_data = tcgplayer_prices.get(variant)
        if variant_data and variant_data.get("market") is not None:
            return float(variant_data["market"])
    return None


def _extract_price_fields(tcgplayer_prices: dict) -> dict:
    """Return a dict with market/low/mid/high extracted from tcgplayer prices."""
    result: dict = {
        "market": None,
        "low": None,
        "mid": None,
        "high": None,
    }
    for variant in ("holofoil", "reverseHolofoil", "normal"):
        vd = tcgplayer_prices.get(variant)
        if vd and vd.get("market") is not None:
            result["market"] = vd.get("market")
            result["low"] = vd.get("low")
            result["mid"] = vd.get("mid")
            result["high"] = vd.get("high")
            break
    return result


# ---------------------------------------------------------------------------
# 1. sync_set_cards
# ---------------------------------------------------------------------------


def sync_set_cards(set_id: str) -> int:
    """Fetch all cards for *set_id* from the Pokemon TCG API and upsert them
    into the ``cards`` table.

    Handles pagination (``pageSize=250``) and respects rate limits.
    Returns the number of cards updated.
    """
    logger.info("sync_set_cards: fetching cards for set %s", set_id)
    updated = 0
    page = 1

    while True:
        try:
            resp = requests.get(
                f"{TCG_API_BASE}/cards",
                params={"q": f"set.id:{set_id}", "page": page, "pageSize": 250},
                headers=_tcg_headers(),
                timeout=REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
            payload = resp.json()
        except requests.RequestException as exc:
            logger.error("sync_set_cards: API error on page %d for set %s: %s", page, set_id, exc)
            break

        cards = payload.get("data", [])
        if not cards:
            break

        conn = get_connection()
        try:
            for card in cards:
                card_id = card.get("id", "")
                name = card.get("name", "")
                rarity = card.get("rarity")
                supertype = card.get("supertype")
                subtypes = card.get("subtypes") or []
                subtype = ", ".join(subtypes) if subtypes else None
                images = card.get("images") or {}
                image_url = images.get("large")
                small_image_url = images.get("small")

                # Extract tcgplayer prices
                tcgplayer = card.get("tcgplayer") or {}
                prices = tcgplayer.get("prices") or {}
                pf = _extract_price_fields(prices)

                conn.execute(
                    """INSERT INTO cards
                           (id, set_id, name, rarity, supertype, subtype,
                            image_url, small_image_url,
                            tcgplayer_market, tcgplayer_low, tcgplayer_mid, tcgplayer_high,
                            updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                       ON CONFLICT(id) DO UPDATE SET
                           name = excluded.name,
                           rarity = excluded.rarity,
                           supertype = excluded.supertype,
                           subtype = excluded.subtype,
                           image_url = COALESCE(excluded.image_url, image_url),
                           small_image_url = COALESCE(excluded.small_image_url, small_image_url),
                           tcgplayer_market = excluded.tcgplayer_market,
                           tcgplayer_low = excluded.tcgplayer_low,
                           tcgplayer_mid = excluded.tcgplayer_mid,
                           tcgplayer_high = excluded.tcgplayer_high,
                           updated_at = CURRENT_TIMESTAMP""",
                    (
                        card_id, set_id, name, rarity, supertype, subtype,
                        image_url, small_image_url,
                        pf["market"], pf["low"], pf["mid"], pf["high"],
                    ),
                )
                updated += 1

            conn.commit()
        except Exception as exc:
            logger.error("sync_set_cards: DB error for set %s page %d: %s", set_id, page, exc)
        finally:
            conn.close()

        # Check if there are more pages
        total_count = payload.get("totalCount", 0)
        page_size = payload.get("pageSize", 250)
        if page * page_size >= total_count:
            break

        page += 1
        time.sleep(RATE_LIMIT_DELAY)

    logger.info("sync_set_cards: updated %d cards for set %s", updated, set_id)
    return updated


# ---------------------------------------------------------------------------
# 2. sync_all_sets
# ---------------------------------------------------------------------------


def sync_all_sets() -> dict:
    """Fetch every set from the Pokemon TCG API, upsert into the ``sets``
    table, then sync cards for each set.

    Returns ``{"sets_updated": int, "cards_updated": int}``.
    """
    logger.info("sync_all_sets: starting full set sync")
    sets_updated = 0
    cards_updated = 0

    try:
        resp = requests.get(
            f"{TCG_API_BASE}/sets",
            headers=_tcg_headers(),
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        payload = resp.json()
    except requests.RequestException as exc:
        logger.error("sync_all_sets: failed to fetch sets: %s", exc)
        return {"sets_updated": 0, "cards_updated": 0}

    sets_data = payload.get("data", [])

    conn = get_connection()
    try:
        for s in sets_data:
            set_id = s.get("id", "")
            name = s.get("name", "")
            series = s.get("series")
            release_date = s.get("releaseDate")
            images = s.get("images") or {}
            logo_url = images.get("logo")
            total = s.get("total")

            conn.execute(
                """INSERT INTO sets (id, name, series, release_date, logo_url, total, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                   ON CONFLICT(id) DO UPDATE SET
                       name = excluded.name,
                       series = excluded.series,
                       release_date = excluded.release_date,
                       logo_url = COALESCE(excluded.logo_url, logo_url),
                       total = excluded.total,
                       updated_at = CURRENT_TIMESTAMP""",
                (set_id, name, series, release_date, logo_url, total),
            )
            sets_updated += 1

        conn.commit()
    except Exception as exc:
        logger.error("sync_all_sets: DB error inserting sets: %s", exc)
    finally:
        conn.close()

    logger.info("sync_all_sets: upserted %d sets, syncing cards...", sets_updated)

    # Sync cards for every set (rate limited)
    for s in sets_data:
        set_id = s.get("id", "")
        if not set_id:
            continue
        cards_updated += sync_set_cards(set_id)
        time.sleep(RATE_LIMIT_DELAY)

    logger.info(
        "sync_all_sets: complete. sets=%d cards=%d",
        sets_updated,
        cards_updated,
    )
    return {"sets_updated": sets_updated, "cards_updated": cards_updated}


# ---------------------------------------------------------------------------
# 3. record_price_snapshots
# ---------------------------------------------------------------------------


def record_price_snapshots(set_id: Optional[str] = None) -> int:
    """Read current card prices from the ``cards`` table and write them to
    ``card_price_history``.

    For each card, graded prices are calculated from the raw market price
    using :data:`GRADE_MULTIPLIERS` when no real graded data already exists
    in the ``graded_prices`` table.

    If *set_id* is provided, only cards in that set are processed; otherwise
    all cards with a non-null market price are included.

    Returns the count of snapshots recorded.
    """
    logger.info("record_price_snapshots: set_id=%s", set_id or "ALL")
    conn = get_connection()
    try:
        if set_id:
            cur = conn.execute(
                """SELECT id, tcgplayer_market FROM cards
                   WHERE set_id = ? AND tcgplayer_market IS NOT NULL""",
                (set_id,),
            )
        else:
            cur = conn.execute(
                "SELECT id, tcgplayer_market FROM cards WHERE tcgplayer_market IS NOT NULL"
            )

        rows = cur.fetchall()
    finally:
        conn.close()

    records: list[dict] = []
    for row in rows:
        card_id = row["id"]
        raw_price = float(row["tcgplayer_market"])

        # Check for existing real graded data
        existing_graded = queries.get_graded_prices(card_id)
        has_real = len(existing_graded) > 0

        graded: dict = {}
        if has_real:
            # Use real graded data to populate history columns
            for entry in existing_graded:
                key = f"{entry['grader'].lower()}{entry['grade'].replace('.', '')}"
                if key in GRADE_MULTIPLIERS:
                    graded[key] = entry.get("market")
        else:
            # Fallback: derive graded estimates from multipliers
            for key, mult in GRADE_MULTIPLIERS.items():
                graded[key] = round(raw_price * mult, 2)

        records.append(
            {
                "card_id": card_id,
                "source": "tcgplayer",
                "raw": raw_price,
                **graded,
            }
        )

    count = queries.batch_insert_card_price_history(records)
    logger.info("record_price_snapshots: recorded %d snapshots", count)
    return count


# ---------------------------------------------------------------------------
# 4. sync_graded_prices
# ---------------------------------------------------------------------------


def sync_graded_prices(card_id: str, raw_price: float) -> bool:
    """Try to fetch real graded prices from the external price API for
    *card_id*.  When the API is unavailable or returns no data, fall back to
    multiplier-based estimates and upsert them into ``graded_prices``.

    Returns ``True`` if at least one graded price was written.
    """
    wrote_any = False

    # Attempt external API first
    if PRICE_API_URL and PRICE_API_KEY:
        try:
            resp = requests.get(
                PRICE_API_URL,
                params={"card_id": card_id, "type": "graded"},
                headers={
                    "Authorization": f"Bearer {PRICE_API_KEY}",
                    "Accept": "application/json",
                },
                timeout=REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
            data = resp.json()
            graded_list = data.get("graded_prices") or data.get("data") or []

            for entry in graded_list:
                grader = entry.get("grader", "").upper()
                grade = str(entry.get("grade", ""))
                market = entry.get("market")
                low = entry.get("low")
                high = entry.get("high")
                label = entry.get("grade_label")
                if grader and grade:
                    queries.upsert_graded_price(
                        card_id=card_id,
                        grader=grader,
                        grade=grade,
                        market=market,
                        low=low,
                        high=high,
                        grade_label=label,
                        source="price_api",
                    )
                    wrote_any = True

            if wrote_any:
                logger.debug(
                    "sync_graded_prices: wrote real graded data for %s", card_id
                )
                return True

        except requests.RequestException as exc:
            logger.warning(
                "sync_graded_prices: external API failed for %s: %s", card_id, exc
            )

    # Fallback: multiplier-based estimates
    if raw_price is None or raw_price <= 0:
        return False

    for key, mult in GRADE_MULTIPLIERS.items():
        info = _GRADE_KEY_MAP.get(key)
        if not info:
            continue
        grader, grade, label = info
        estimated_market = round(raw_price * mult, 2)
        queries.upsert_graded_price(
            card_id=card_id,
            grader=grader,
            grade=grade,
            market=estimated_market,
            grade_label=label,
            source="multiplier",
        )
        wrote_any = True

    if wrote_any:
        logger.debug(
            "sync_graded_prices: wrote multiplier estimates for %s", card_id
        )
    return wrote_any


# ---------------------------------------------------------------------------
# 5. sync_sealed_prices
# ---------------------------------------------------------------------------


def sync_sealed_prices() -> int:
    """Read all sealed products from the database, record the current price
    into ``sealed_price_history``, and refresh ``current_price`` on each row.

    Returns the number of products updated.
    """
    logger.info("sync_sealed_prices: starting sealed price sync")
    products = queries.get_sealed_products()
    updated = 0

    for product in products:
        product_id = product.get("id")
        current_price = product.get("current_price")
        if product_id is None or current_price is None:
            continue

        # Record history snapshot
        ok = queries.insert_sealed_price_history(
            sealed_product_id=product_id,
            price=current_price,
            source="sync",
        )
        if ok:
            # Touch the updated_at timestamp via update_sealed_price
            queries.update_sealed_price(product_id, current_price)
            updated += 1

    logger.info("sync_sealed_prices: recorded %d sealed price snapshots", updated)
    return updated


# ---------------------------------------------------------------------------
# 6. run_full_sync
# ---------------------------------------------------------------------------


def run_full_sync() -> dict:
    """Execute every sync operation in the correct order:

    1. Ensure the database schema is up to date.
    2. Sync sets and cards from the Pokemon TCG API.
    3. Record card price snapshots (including graded estimates).
    4. Sync sealed product prices.

    Returns a summary dict.
    """
    started = datetime.utcnow().isoformat()
    logger.info("run_full_sync: starting at %s", started)

    # 1. Ensure schema
    init_db()

    # 2. Sync sets + cards
    set_result = sync_all_sets()

    # 3. Price snapshots
    snapshots = record_price_snapshots()

    # 4. Sealed products
    sealed = sync_sealed_prices()

    finished = datetime.utcnow().isoformat()
    summary = {
        "started_at": started,
        "finished_at": finished,
        "sets_updated": set_result.get("sets_updated", 0),
        "cards_updated": set_result.get("cards_updated", 0),
        "price_snapshots": snapshots,
        "sealed_updated": sealed,
    }

    logger.info("run_full_sync: complete -- %s", summary)
    return summary


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    result = run_full_sync()
    print(f"Sync complete: {result}")
