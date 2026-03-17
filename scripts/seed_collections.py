#!/usr/bin/env python3
"""
Seed sample collections, portfolio history, price alerts, and expand card price history.

This gives the Portfolio, Analytics, and Dashboard tabs real data to display.

Usage: python3 scripts/seed_collections.py
"""
import sys
import random
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db.connection import get_connection, init_db


CONDITIONS = ["Mint", "NM", "NM", "NM", "EX", "LP"]  # weighted toward NM


def seed_collection() -> int:
    """Seed a sample card collection for the 'default' user."""
    print("[collection] Seeding sample collection for 'default' user...")
    conn = get_connection()
    total = 0
    try:
        # Clear existing collection for default user
        conn.execute("DELETE FROM user_collections WHERE user_id = 'default'")

        # Get high-value cards across multiple sets for a realistic collection
        cards = conn.execute(
            """SELECT id, name, set_id, rarity, tcgplayer_market
               FROM cards
               WHERE tcgplayer_market IS NOT NULL AND tcgplayer_market > 0
               ORDER BY tcgplayer_market DESC"""
        ).fetchall()

        if not cards:
            print("  No cards found — run seed_database.py first")
            return 0

        # Build a realistic collection:
        # - Top 15 most valuable cards (chase cards you pulled)
        # - 25 random mid-value cards ($2-$50)
        # - 40 random common/uncommon cards (< $2)
        selected = []

        # Top chase cards
        top_cards = cards[:30]
        chase_picks = random.sample(top_cards, min(15, len(top_cards)))
        selected.extend(chase_picks)

        # Mid-value cards
        mid_cards = [c for c in cards if 2 <= (c[4] or 0) <= 50]
        if mid_cards:
            mid_picks = random.sample(mid_cards, min(25, len(mid_cards)))
            selected.extend(mid_picks)

        # Budget cards
        budget_cards = [c for c in cards if 0 < (c[4] or 0) < 2]
        if budget_cards:
            budget_picks = random.sample(budget_cards, min(40, len(budget_cards)))
            selected.extend(budget_picks)

        now = datetime.utcnow()
        for card in selected:
            card_id = card[0]
            market_price = card[4] or 1.0
            condition = random.choice(CONDITIONS)
            quantity = random.choices([1, 2, 3, 4], weights=[60, 25, 10, 5])[0]

            # Purchase price: usually slightly below or above current market
            price_variance = random.uniform(0.6, 1.1)
            purchase_price = round(market_price * price_variance, 2)

            # Purchase date: random within last 180 days
            days_ago = random.randint(1, 180)
            purchase_date = (now - timedelta(days=days_ago)).strftime("%Y-%m-%d")

            try:
                conn.execute(
                    """INSERT OR REPLACE INTO user_collections
                       (user_id, card_id, quantity, condition, purchase_price, purchase_date, notes)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    ("default", card_id, quantity, condition, purchase_price, purchase_date, None),
                )
                total += 1
            except Exception:
                continue

        conn.commit()
        print(f"[collection] Done — {total} cards added to default collection.\n")
    except Exception as e:
        print(f"  ! Error: {e}")
        conn.rollback()
    finally:
        conn.close()
    return total


def seed_portfolio_history(days: int = 90) -> int:
    """Seed portfolio value history for the default user."""
    print(f"[portfolio-history] Generating {days}-day portfolio history...")
    conn = get_connection()
    total = 0
    try:
        # Clear existing
        conn.execute("DELETE FROM portfolio_history WHERE user_id = 'default'")

        # Calculate current portfolio value
        rows = conn.execute(
            """SELECT SUM(uc.quantity * COALESCE(c.tcgplayer_market, 0)),
                      SUM(uc.quantity)
               FROM user_collections uc
               LEFT JOIN cards c ON uc.card_id = c.id
               WHERE uc.user_id = 'default'"""
        ).fetchone()

        current_value = rows[0] or 500.0
        current_cards = int(rows[1] or 20)

        # Generate history trending upward to current value
        # Start at 60-80% of current value
        start_value = current_value * random.uniform(0.6, 0.8)
        start_cards = max(5, int(current_cards * 0.4))

        daily_value_trend = (current_value - start_value) / days
        daily_card_trend = (current_cards - start_cards) / days
        noise_pct = 0.02

        value = start_value
        cards_count = float(start_cards)
        now = datetime.utcnow()

        for day_offset in range(days, 0, -1):
            record_date = now - timedelta(days=day_offset)
            timestamp = record_date.strftime("%Y-%m-%d %H:%M:%S")

            # Add trend + noise
            value += daily_value_trend + random.gauss(0, value * noise_pct)
            value = max(value, start_value * 0.5)
            cards_count += daily_card_trend + random.gauss(0, 0.3)
            cards_count = max(cards_count, start_cards)

            conn.execute(
                """INSERT INTO portfolio_history (user_id, total_value, total_cards, recorded_at)
                   VALUES (?, ?, ?, ?)""",
                ("default", round(value, 2), int(cards_count), timestamp),
            )
            total += 1

        # Today's value
        conn.execute(
            """INSERT INTO portfolio_history (user_id, total_value, total_cards, recorded_at)
               VALUES (?, ?, ?, ?)""",
            ("default", round(current_value, 2), current_cards, now.strftime("%Y-%m-%d %H:%M:%S")),
        )
        total += 1

        conn.commit()
        print(f"[portfolio-history] Done — {total} portfolio snapshots.\n")
    except Exception as e:
        print(f"  ! Error: {e}")
        conn.rollback()
    finally:
        conn.close()
    return total


def seed_price_alerts() -> int:
    """Seed sample price alerts for the default user."""
    print("[price-alerts] Seeding sample price alerts...")
    conn = get_connection()
    total = 0
    try:
        # Clear existing alerts for default user
        conn.execute("DELETE FROM price_alerts WHERE user_id = 'default'")

        # Get some high-value cards to set alerts on
        cards = conn.execute(
            """SELECT id, name, tcgplayer_market FROM cards
               WHERE tcgplayer_market IS NOT NULL AND tcgplayer_market > 10
               ORDER BY tcgplayer_market DESC
               LIMIT 50"""
        ).fetchall()

        if not cards:
            print("  No cards to set alerts on")
            return 0

        # Pick 8-12 cards for alerts
        alert_cards = random.sample(cards, min(10, len(cards)))

        for card in alert_cards:
            card_id = card[0]
            market = card[2]

            # Randomly choose alert type
            alert_type = random.choice(["below", "below", "above", "change_percent"])

            if alert_type == "below":
                # Alert when price drops below a threshold (10-30% below current)
                threshold = round(market * random.uniform(0.7, 0.9), 2)
            elif alert_type == "above":
                # Alert when price rises above threshold (10-50% above current)
                threshold = round(market * random.uniform(1.1, 1.5), 2)
            else:
                # Alert on percent change
                threshold = random.choice([5.0, 10.0, 15.0, 20.0])

            is_active = random.choice([1, 1, 1, 0])  # 75% active

            try:
                conn.execute(
                    """INSERT INTO price_alerts (user_id, card_id, condition, threshold, is_active)
                       VALUES (?, ?, ?, ?, ?)""",
                    ("default", card_id, alert_type, threshold, is_active),
                )
                total += 1
            except Exception:
                continue

        conn.commit()
        print(f"[price-alerts] Done — {total} alerts created.\n")
    except Exception as e:
        print(f"  ! Error: {e}")
        conn.rollback()
    finally:
        conn.close()
    return total


def expand_card_price_history(days: int = 90) -> int:
    """Expand card price history to cover more cards and more days.

    The initial seed only covered 30 days. This expands to 90 days
    and covers cards that were missed.
    """
    print(f"[card-history-expand] Expanding card price history to {days} days...")
    conn = get_connection()
    total = 0
    try:
        # Find cards that have market prices but no/little history
        cards = conn.execute(
            """SELECT c.id, c.tcgplayer_market
               FROM cards c
               WHERE c.tcgplayer_market IS NOT NULL AND c.tcgplayer_market > 0
               AND c.id NOT IN (
                   SELECT DISTINCT card_id FROM card_price_history
                   WHERE recorded_at < datetime('now', '-31 days')
               )"""
        ).fetchall()

        if not cards:
            print("  All cards already have extended history")
            return 0

        print(f"  Expanding history for {len(cards)} cards...")

        now = datetime.utcnow()
        batch = []

        for card in cards:
            card_id = card[0]
            market = card[1]
            noise_pct = 0.015

            price = market
            for day_offset in range(days, 30, -1):  # Only fill days 31-90 (30 already done)
                record_date = now - timedelta(days=day_offset)
                timestamp = record_date.strftime("%Y-%m-%d %H:%M:%S")

                daily_change = random.gauss(0, price * noise_pct)
                price = price - daily_change
                price = max(price, 0.01)

                batch.append((
                    card_id, "tcgplayer", round(price, 2),
                    None, None, None, None, None, None, None, None, None,
                    timestamp,
                ))

        if batch:
            print(f"  Inserting {len(batch)} extended history rows...")
            conn.executemany(
                """INSERT INTO card_price_history
                   (card_id, source, price_raw, price_psa10, price_psa9, price_psa8,
                    price_cgc10, price_cgc95, price_cgc9, price_bgs10, price_bgs95, price_bgs9,
                    recorded_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                batch,
            )
            conn.commit()
            total = len(batch)

        print(f"[card-history-expand] Done — {total} extended price history rows.\n")
    except Exception as e:
        print(f"  ! Error: {e}")
        conn.rollback()
    finally:
        conn.close()
    return total


def main():
    print("=" * 60)
    print("  Pokemon TCG Collection & Portfolio Seeder")
    print("=" * 60)
    print()

    init_db()

    # Initialize alerts table
    from alerts.tracker import init_alerts_table
    init_alerts_table()

    seed_collection()
    seed_portfolio_history(days=90)
    seed_price_alerts()
    expand_card_price_history(days=90)

    # Final summary
    conn = get_connection()
    tables = {
        "user_collections": "SELECT COUNT(*) FROM user_collections",
        "portfolio_history": "SELECT COUNT(*) FROM portfolio_history",
        "price_alerts": "SELECT COUNT(*) FROM price_alerts",
        "card_price_history": "SELECT COUNT(*) FROM card_price_history",
    }
    print("=" * 60)
    print("  Final counts:")
    for name, sql in tables.items():
        count = conn.execute(sql).fetchone()[0]
        print(f"    {name}: {count}")
    conn.close()
    print("=" * 60)


if __name__ == "__main__":
    main()
