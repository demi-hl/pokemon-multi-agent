#!/usr/bin/env python3
"""
Seed pull rates and graded prices into the Pokemon TCG database.

Pull rates are community-estimated rates per pack for each rarity tier.
Graded prices are synthetic PSA/CGC/BGS multipliers based on raw card prices.

Usage: python3 scripts/seed_pull_rates.py
"""
import sys
import random
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db.connection import get_connection, init_db


# ── Standard pull rates for modern Pokemon TCG sets (per pack, as %) ──
# These are community-estimated averages across Scarlet & Violet era sets.

MODERN_PULL_RATES = [
    # (category, label, rate_per_pack, notes)
    ("common", "Common", 45.0, "3-4 commons per pack"),
    ("uncommon", "Uncommon", 30.0, "2-3 uncommons per pack"),
    ("rare", "Rare", 15.0, "~1 rare per pack on average"),
    ("holo", "Holo Rare", 8.0, "~1 in 12 packs"),
    ("double_rare", "Double Rare", 4.5, "~1 in 22 packs"),
    ("ultra_rare", "Ultra Rare ex", 3.5, "~1 in 29 packs"),
    ("full_art", "Full Art", 2.2, "~1 in 45 packs"),
    ("illustration_rare", "Illustration Rare", 1.8, "~1 in 55 packs"),
    ("special_art", "Special Art Rare", 0.6, "~1 in 167 packs"),
    ("hyper_rare", "Hyper Rare / Gold", 0.4, "~1 in 250 packs"),
]

# Older sets had different pull rate structures
SWSH_PULL_RATES = [
    ("common", "Common", 45.0, "3-4 commons per pack"),
    ("uncommon", "Uncommon", 30.0, "2-3 uncommons per pack"),
    ("rare", "Rare", 16.0, "~1 rare per pack"),
    ("holo", "Holo Rare", 9.0, "~1 in 11 packs"),
    ("ultra_rare", "V / VMAX", 5.0, "~1 in 20 packs"),
    ("full_art", "Full Art V", 2.5, "~1 in 40 packs"),
    ("alt_art", "Alternate Art", 0.8, "~1 in 125 packs"),
    ("secret_rare", "Secret Rare / Rainbow", 0.5, "~1 in 200 packs"),
    ("trainer_gallery", "Trainer Gallery", 1.2, "~1 in 83 packs (subset sets)"),
]

LEGACY_PULL_RATES = [
    ("common", "Common", 50.0, "4-5 commons per pack"),
    ("uncommon", "Uncommon", 30.0, "2-3 uncommons per pack"),
    ("rare", "Rare", 12.0, "~1 rare per pack"),
    ("holo", "Holo Rare", 5.0, "~1 in 20 packs"),
    ("ultra_rare", "Ultra Rare EX/GX", 3.0, "~1 in 33 packs"),
    ("full_art", "Full Art", 1.5, "~1 in 67 packs"),
    ("secret_rare", "Secret Rare", 0.5, "~1 in 200 packs"),
]

# Special set overrides
SPECIAL_SET_RATES = {
    "sv8pt5": [  # Prismatic Evolutions
        ("common", "Common", 40.0, "3-4 commons per pack"),
        ("uncommon", "Uncommon", 28.0, "2-3 uncommons per pack"),
        ("rare", "Rare", 14.0, "~1 rare per pack"),
        ("holo", "Holo Rare", 7.0, "~1 in 14 packs"),
        ("double_rare", "Double Rare", 4.0, "~1 in 25 packs"),
        ("ultra_rare", "Ultra Rare ex", 3.0, "~1 in 33 packs"),
        ("illustration_rare", "Illustration Rare", 2.5, "~1 in 40 packs — Eeveelution themed"),
        ("special_art", "Special Art Rare", 0.8, "~1 in 125 packs — Eeveelution SARs"),
        ("hyper_rare", "Hyper Rare / Gold", 0.5, "~1 in 200 packs"),
        ("immersive_rare", "Immersive Rare", 0.2, "~1 in 500 packs — chase hits"),
    ],
    "sv3pt5": [  # Paldean Fates (shiny subset)
        ("common", "Common", 40.0, "3-4 commons per pack"),
        ("uncommon", "Uncommon", 28.0, "2-3 uncommons per pack"),
        ("rare", "Rare", 14.0, "~1 rare per pack"),
        ("shiny", "Shiny Rare", 8.0, "~1 in 12 packs — shiny Pokemon"),
        ("shiny_v", "Shiny V / ex", 3.5, "~1 in 29 packs"),
        ("illustration_rare", "Illustration Rare", 2.0, "~1 in 50 packs"),
        ("special_art", "Special Art Rare", 0.7, "~1 in 143 packs"),
        ("hyper_rare", "Hyper Rare / Gold", 0.4, "~1 in 250 packs"),
    ],
    "swsh12pt5": [  # Crown Zenith (Galarian Gallery)
        ("common", "Common", 42.0, "3-4 commons per pack"),
        ("uncommon", "Uncommon", 28.0, "2-3 uncommons per pack"),
        ("rare", "Rare", 14.0, "~1 rare per pack"),
        ("holo", "Holo Rare", 8.0, "~1 in 12 packs"),
        ("ultra_rare", "V / VSTAR / VMAX", 4.5, "~1 in 22 packs"),
        ("galarian_gallery", "Galarian Gallery", 2.5, "~1 in 40 packs — art cards"),
        ("alt_art", "Alternate Art", 0.6, "~1 in 167 packs"),
        ("secret_rare", "Secret Rare / Gold", 0.4, "~1 in 250 packs"),
    ],
}


def get_rates_for_set(set_id: str, series: str) -> list[tuple]:
    """Return the appropriate pull rate template for a set."""
    if set_id in SPECIAL_SET_RATES:
        return SPECIAL_SET_RATES[set_id]
    series_lower = (series or "").lower()
    if "scarlet" in series_lower or "mega" in series_lower:
        return MODERN_PULL_RATES
    if "sword" in series_lower or "shield" in series_lower:
        return SWSH_PULL_RATES
    return LEGACY_PULL_RATES


def add_variance(rate: float) -> float:
    """Add small random variance to a pull rate to make each set slightly unique."""
    variance = rate * random.uniform(-0.08, 0.08)
    return round(max(0.01, rate + variance), 2)


def seed_pull_rates() -> int:
    """Seed pull rates for all sets in the database."""
    print("[pull-rates] Seeding pull rates for all sets...")
    conn = get_connection()
    total = 0
    try:
        # Clear existing pull rates
        conn.execute("DELETE FROM pull_rates")

        sets = conn.execute("SELECT id, name, series FROM sets").fetchall()
        print(f"  Found {len(sets)} sets")

        for s in sets:
            set_id, name, series = s[0], s[1], s[2]
            rates = get_rates_for_set(set_id, series)

            for category, label, base_rate, notes in rates:
                rate = add_variance(base_rate)
                conn.execute(
                    """INSERT INTO pull_rates (set_id, category, label, rate_per_pack, notes)
                       VALUES (?, ?, ?, ?, ?)""",
                    (set_id, category, label, rate, notes),
                )
                total += 1

        conn.commit()
        print(f"[pull-rates] Done — {total} pull rate rows inserted for {len(sets)} sets.\n")
    except Exception as e:
        print(f"  ! Error: {e}")
        conn.rollback()
    finally:
        conn.close()
    return total


def seed_graded_prices() -> int:
    """Seed graded prices (PSA/CGC/BGS) for top-value cards."""
    print("[graded-prices] Seeding graded prices for top cards...")
    conn = get_connection()
    total = 0
    try:
        # Clear existing
        conn.execute("DELETE FROM graded_prices")

        # Get cards with market price > $1
        cards = conn.execute(
            """SELECT id, name, tcgplayer_market FROM cards
               WHERE tcgplayer_market IS NOT NULL AND tcgplayer_market > 1
               ORDER BY tcgplayer_market DESC"""
        ).fetchall()

        print(f"  Found {len(cards)} cards with prices > $1")

        for card in cards:
            card_id = card[0]
            raw_price = card[2]

            # PSA grades: 10, 9, 8
            psa10_mult = random.uniform(2.5, 5.0) if raw_price > 20 else random.uniform(1.8, 3.0)
            psa9_mult = random.uniform(1.3, 2.0)
            psa8_mult = random.uniform(0.9, 1.3)

            for grade, mult, label in [
                ("10", psa10_mult, "Gem Mint"),
                ("9", psa9_mult, "Mint"),
                ("8", psa8_mult, "NM-MT"),
            ]:
                market = round(raw_price * mult, 2)
                low = round(market * random.uniform(0.75, 0.9), 2)
                high = round(market * random.uniform(1.1, 1.35), 2)
                conn.execute(
                    """INSERT INTO graded_prices (card_id, grader, grade, grade_label, market, low, high, source)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (card_id, "PSA", grade, label, market, low, high, "estimated"),
                )
                total += 1

            # CGC grades: 10, 9.5, 9
            cgc10_mult = psa10_mult * random.uniform(0.7, 0.85)  # CGC 10 < PSA 10 typically
            cgc95_mult = random.uniform(1.2, 1.8)
            cgc9_mult = random.uniform(1.0, 1.4)

            for grade, mult, label in [
                ("10", cgc10_mult, "Pristine"),
                ("9.5", cgc95_mult, "Gem Mint"),
                ("9", cgc9_mult, "Mint"),
            ]:
                market = round(raw_price * mult, 2)
                low = round(market * random.uniform(0.75, 0.9), 2)
                high = round(market * random.uniform(1.1, 1.35), 2)
                conn.execute(
                    """INSERT INTO graded_prices (card_id, grader, grade, grade_label, market, low, high, source)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (card_id, "CGC", grade, label, market, low, high, "estimated"),
                )
                total += 1

            # BGS grades: 10, 9.5, 9
            bgs10_mult = psa10_mult * random.uniform(0.9, 1.1)  # BGS 10 Black Label can exceed PSA 10
            bgs95_mult = random.uniform(1.3, 2.0)
            bgs9_mult = random.uniform(0.9, 1.3)

            for grade, mult, label in [
                ("10", bgs10_mult, "Pristine / Black Label"),
                ("9.5", bgs95_mult, "Gem Mint"),
                ("9", bgs9_mult, "Mint"),
            ]:
                market = round(raw_price * mult, 2)
                low = round(market * random.uniform(0.75, 0.9), 2)
                high = round(market * random.uniform(1.1, 1.35), 2)
                conn.execute(
                    """INSERT INTO graded_prices (card_id, grader, grade, grade_label, market, low, high, source)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (card_id, "BGS", grade, label, market, low, high, "estimated"),
                )
                total += 1

        conn.commit()
        print(f"[graded-prices] Done — {total} graded price rows for {len(cards)} cards.\n")
    except Exception as e:
        print(f"  ! Error: {e}")
        conn.rollback()
    finally:
        conn.close()
    return total


def main():
    print("=" * 60)
    print("  Pokemon TCG Pull Rates & Graded Prices Seeder")
    print("=" * 60)
    print()

    init_db()
    seed_pull_rates()
    seed_graded_prices()

    # Summary
    conn = get_connection()
    pr = conn.execute("SELECT COUNT(*) FROM pull_rates").fetchone()[0]
    gp = conn.execute("SELECT COUNT(*) FROM graded_prices").fetchone()[0]
    conn.close()

    print("=" * 60)
    print(f"  Final counts: {pr} pull rates, {gp} graded prices")
    print("=" * 60)


if __name__ == "__main__":
    main()
