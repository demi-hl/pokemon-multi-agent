#!/usr/bin/env python3
"""
Seed the Pokemon TCG database with real data from the Pokemon TCG API
and curated sealed product data.

Usage: python3 scripts/seed_database.py [--sets-only] [--sealed-only] [--history-only]
"""
import sys
import os
import argparse
import random
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db.connection import init_db, get_connection
from db import queries

# ---------------------------------------------------------------------------
# Curated sealed products with real MSRP and approximate market prices
# ---------------------------------------------------------------------------

SEALED_PRODUCTS = [
    # Prismatic Evolutions
    {
        "name": "Prismatic Evolutions Elite Trainer Box",
        "set_name": "Prismatic Evolutions",
        "product_type": "Elite Trainer Box",
        "msrp": 49.99,
        "current_price": 89.99,
        "in_print": True,
    },
    {
        "name": "Prismatic Evolutions Booster Bundle",
        "set_name": "Prismatic Evolutions",
        "product_type": "Booster Bundle",
        "msrp": 29.99,
        "current_price": 54.99,
        "in_print": True,
    },
    {
        "name": "Prismatic Evolutions UPC",
        "set_name": "Prismatic Evolutions",
        "product_type": "Ultra Premium Collection",
        "msrp": 119.99,
        "current_price": 199.99,
        "in_print": True,
    },
    # Surging Sparks
    {
        "name": "Surging Sparks Elite Trainer Box",
        "set_name": "Surging Sparks",
        "product_type": "Elite Trainer Box",
        "msrp": 49.99,
        "current_price": 44.99,
        "in_print": True,
    },
    {
        "name": "Surging Sparks Booster Box",
        "set_name": "Surging Sparks",
        "product_type": "Booster Box",
        "msrp": 143.64,
        "current_price": 109.99,
        "in_print": True,
    },
    # Evolving Skies
    {
        "name": "Evolving Skies Elite Trainer Box",
        "set_name": "Evolving Skies",
        "product_type": "Elite Trainer Box",
        "msrp": 49.99,
        "current_price": 149.99,
        "in_print": False,
    },
    {
        "name": "Evolving Skies Booster Box",
        "set_name": "Evolving Skies",
        "product_type": "Booster Box",
        "msrp": 143.64,
        "current_price": 319.99,
        "in_print": False,
    },
    # Pokemon 151
    {
        "name": "Pokemon 151 Elite Trainer Box",
        "set_name": "Pokemon 151",
        "product_type": "Elite Trainer Box",
        "msrp": 49.99,
        "current_price": 79.99,
        "in_print": False,
    },
    {
        "name": "Pokemon 151 Booster Bundle",
        "set_name": "Pokemon 151",
        "product_type": "Booster Bundle",
        "msrp": 29.99,
        "current_price": 49.99,
        "in_print": False,
    },
    {
        "name": "Pokemon 151 UPC",
        "set_name": "Pokemon 151",
        "product_type": "Ultra Premium Collection",
        "msrp": 119.99,
        "current_price": 259.99,
        "in_print": False,
    },
    # Crown Zenith
    {
        "name": "Crown Zenith Elite Trainer Box",
        "set_name": "Crown Zenith",
        "product_type": "Elite Trainer Box",
        "msrp": 49.99,
        "current_price": 69.99,
        "in_print": False,
    },
    # Obsidian Flames
    {
        "name": "Obsidian Flames Booster Box",
        "set_name": "Obsidian Flames",
        "product_type": "Booster Box",
        "msrp": 143.64,
        "current_price": 119.99,
        "in_print": True,
    },
    {
        "name": "Obsidian Flames Elite Trainer Box",
        "set_name": "Obsidian Flames",
        "product_type": "Elite Trainer Box",
        "msrp": 49.99,
        "current_price": 42.99,
        "in_print": True,
    },
    # Paldean Fates
    {
        "name": "Paldean Fates Elite Trainer Box",
        "set_name": "Paldean Fates",
        "product_type": "Elite Trainer Box",
        "msrp": 49.99,
        "current_price": 59.99,
        "in_print": True,
    },
    {
        "name": "Paldean Fates Booster Bundle",
        "set_name": "Paldean Fates",
        "product_type": "Booster Bundle",
        "msrp": 29.99,
        "current_price": 34.99,
        "in_print": True,
    },
    # Paradox Rift
    {
        "name": "Paradox Rift Booster Box",
        "set_name": "Paradox Rift",
        "product_type": "Booster Box",
        "msrp": 143.64,
        "current_price": 99.99,
        "in_print": True,
    },
    {
        "name": "Paradox Rift Elite Trainer Box",
        "set_name": "Paradox Rift",
        "product_type": "Elite Trainer Box",
        "msrp": 49.99,
        "current_price": 39.99,
        "in_print": True,
    },
    # Scarlet & Violet Base
    {
        "name": "Scarlet & Violet Booster Box",
        "set_name": "Scarlet & Violet",
        "product_type": "Booster Box",
        "msrp": 143.64,
        "current_price": 109.99,
        "in_print": True,
    },
]


# ---------------------------------------------------------------------------
# Seed functions
# ---------------------------------------------------------------------------


def seed_sealed_products() -> int:
    """Insert all curated sealed products into the database via upsert.

    Returns the number of products inserted or updated.
    """
    print("[sealed] Seeding sealed products ...")
    count = 0
    for product in SEALED_PRODUCTS:
        row_id = queries.upsert_sealed_product(
            name=product["name"],
            set_name=product["set_name"],
            product_type=product["product_type"],
            msrp=product["msrp"],
            current_price=product.get("current_price"),
            in_print=product.get("in_print", True),
        )
        if row_id is not None:
            count += 1
            print(f"  + {product['name']}  (id={row_id})")
        else:
            print(f"  ! Failed to upsert: {product['name']}")
    print(f"[sealed] Done -- {count}/{len(SEALED_PRODUCTS)} products seeded.\n")
    return count


def generate_price_history(days: int = 90) -> int:
    """Generate synthetic daily price history for every sealed product.

    Works backwards from the product's current_price, applying a realistic
    curve so charts look plausible:
      - Out-of-print products trend upward over time (prices were lower in the past).
      - In-print products hover near MSRP with small fluctuations.
      - Daily variation uses random.gauss with 1-2% standard deviation.

    Returns total number of price-history rows inserted.
    """
    print(f"[history] Generating {days}-day sealed price history ...")
    products = queries.get_sealed_products()
    if not products:
        print("  No sealed products found -- run --sealed-only first.")
        return 0

    conn = get_connection()
    total_inserted = 0
    try:
        for product in products:
            product_id = product["id"]
            current_price = product.get("current_price") or product.get("msrp") or 49.99
            msrp = product.get("msrp") or current_price
            in_print = bool(product.get("in_print", True))

            # Determine the starting price (the price `days` ago)
            if in_print:
                # In-print products: start near MSRP, drift to current price
                base_price = msrp + random.uniform(-msrp * 0.05, msrp * 0.05)
            else:
                # Out-of-print products: start lower, trend up to current price
                # The further the current price is above MSRP, the lower the
                # historical start relative to the current price
                premium_ratio = current_price / msrp if msrp > 0 else 1.0
                # E.g. if premium is 3x, historical start is ~55-65% of current
                historical_fraction = max(0.4, 1.0 - (premium_ratio - 1.0) * 0.15)
                base_price = current_price * historical_fraction
                base_price += random.uniform(-base_price * 0.03, base_price * 0.03)

            # Daily trend to move from base_price to current_price over `days`
            daily_trend = (current_price - base_price) / days if days > 0 else 0
            # Standard deviation for daily noise: 1-2% of the price
            noise_pct = random.uniform(0.01, 0.02)

            price = base_price
            rows_for_product = 0
            now = datetime.utcnow()

            for day_offset in range(days, 0, -1):
                record_date = now - timedelta(days=day_offset)
                timestamp = record_date.strftime("%Y-%m-%d %H:%M:%S")

                # Apply trend + noise
                noise = random.gauss(0, price * noise_pct)
                price = price + daily_trend + noise
                # Clamp to avoid negative or unreasonably low prices
                price = max(price, msrp * 0.5)

                conn.execute(
                    """INSERT INTO sealed_price_history
                       (sealed_product_id, price, source, recorded_at)
                       VALUES (?, ?, ?, ?)""",
                    (product_id, round(price, 2), "seed", timestamp),
                )
                rows_for_product += 1

            # Also insert today's price as the latest data point
            conn.execute(
                """INSERT INTO sealed_price_history
                   (sealed_product_id, price, source, recorded_at)
                   VALUES (?, ?, ?, ?)""",
                (product_id, round(current_price, 2), "seed", now.strftime("%Y-%m-%d %H:%M:%S")),
            )
            rows_for_product += 1

            total_inserted += rows_for_product
            print(f"  + {product['name']}: {rows_for_product} price points")

        conn.commit()
    except Exception as exc:
        print(f"  ! Error generating sealed history: {exc}")
        conn.rollback()
    finally:
        conn.close()

    print(f"[history] Done -- {total_inserted} sealed price-history rows inserted.\n")
    return total_inserted


def seed_card_price_history(days: int = 30) -> int:
    """Generate synthetic daily price history for cards already in the database.

    Uses each card's current tcgplayer_market as today's price and works
    backwards with small daily variations.

    Returns total number of price-history rows inserted.
    """
    print(f"[card-history] Generating {days}-day card price history ...")
    conn = get_connection()
    total_inserted = 0

    try:
        # Fetch all cards that have a market price
        cur = conn.execute(
            """SELECT id, tcgplayer_market, tcgplayer_low, tcgplayer_mid, tcgplayer_high
               FROM cards
               WHERE tcgplayer_market IS NOT NULL AND tcgplayer_market > 0"""
        )
        cards = [dict(row) for row in cur.fetchall()]

        if not cards:
            print("  No cards with market prices found -- sync sets/cards first.")
            return 0

        print(f"  Found {len(cards)} cards with market prices.")

        now = datetime.utcnow()
        batch_rows = []

        for card in cards:
            card_id = card["id"]
            market = card["tcgplayer_market"]
            # Standard deviation: 1.5% of the price for daily fluctuations
            noise_pct = 0.015

            # Work backwards: today's price is `market`, generate past prices
            price = market
            for day_offset in range(days, 0, -1):
                record_date = now - timedelta(days=day_offset)
                timestamp = record_date.strftime("%Y-%m-%d %H:%M:%S")

                # Slight random walk backwards -- reverse the direction so
                # earlier prices are somewhat different but centered on market
                daily_change = random.gauss(0, price * noise_pct)
                price = price - daily_change  # reverse walk
                price = max(price, 0.01)  # never go below a penny

                batch_rows.append((
                    card_id,
                    "tcgplayer",
                    round(price, 2),
                    None,  # psa10
                    None,  # psa9
                    None,  # psa8
                    None,  # cgc10
                    None,  # cgc95
                    None,  # cgc9
                    None,  # bgs10
                    None,  # bgs95
                    None,  # bgs9
                    timestamp,
                ))

            # Insert today's actual price as the latest data point
            batch_rows.append((
                card_id,
                "tcgplayer",
                round(market, 2),
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                now.strftime("%Y-%m-%d %H:%M:%S"),
            ))

        # Batch insert all rows
        if batch_rows:
            print(f"  Inserting {len(batch_rows)} card price-history rows ...")
            conn.executemany(
                """INSERT INTO card_price_history
                   (card_id, source, price_raw, price_psa10, price_psa9, price_psa8,
                    price_cgc10, price_cgc95, price_cgc9, price_bgs10, price_bgs95, price_bgs9,
                    recorded_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                batch_rows,
            )
            conn.commit()
            total_inserted = len(batch_rows)

    except Exception as exc:
        print(f"  ! Error generating card history: {exc}")
        conn.rollback()
    finally:
        conn.close()

    print(f"[card-history] Done -- {total_inserted} card price-history rows inserted.\n")
    return total_inserted


def sync_sets_from_api() -> bool:
    """Attempt to pull real set and card data from the Pokemon TCG API.

    Tries to import agents.price_sync.sync_all_sets(). If the module is not
    available (missing dependencies, API key, etc.) it logs a helpful message
    and returns False.
    """
    print("[api-sync] Attempting to sync sets and cards from Pokemon TCG API ...")
    try:
        from agents.price_sync import sync_all_sets  # type: ignore[import-untyped]

        sync_all_sets()
        print("[api-sync] Sync complete.\n")
        return True
    except ImportError:
        print(
            "  ! Could not import agents.price_sync.sync_all_sets.\n"
            "    This is expected if the price_sync module has not been created yet\n"
            "    or if dependencies are missing. Skipping API sync.\n"
            "    You can manually populate sets/cards by running the price sync\n"
            "    module once it is available.\n"
        )
        return False
    except Exception as exc:
        print(f"  ! API sync failed: {exc}\n")
        return False


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed the Pokemon TCG database with sealed products, price history, and (optionally) API card data."
    )
    parser.add_argument(
        "--sets-only",
        action="store_true",
        help="Only sync sets/cards from the Pokemon TCG API.",
    )
    parser.add_argument(
        "--sealed-only",
        action="store_true",
        help="Only seed sealed products (no price history, no API sync).",
    )
    parser.add_argument(
        "--history-only",
        action="store_true",
        help="Only generate price history for existing data (sealed + cards).",
    )
    args = parser.parse_args()

    # If no flags are set, run everything
    run_all = not (args.sets_only or args.sealed_only or args.history_only)

    print("=" * 60)
    print("  Pokemon TCG Database Seeder")
    print("=" * 60)
    print()

    # Always initialize the schema first
    print("[init] Initializing database schema ...")
    init_db()
    print("[init] Schema ready.\n")

    if args.sets_only or run_all:
        sync_sets_from_api()

    if args.sealed_only or run_all:
        seed_sealed_products()

    if args.history_only or run_all:
        generate_price_history(days=90)
        seed_card_price_history(days=30)

    print("=" * 60)
    print("  Seeding complete.")
    print("=" * 60)


if __name__ == "__main__":
    main()
