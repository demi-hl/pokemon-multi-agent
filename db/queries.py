"""
Query helpers for sets, cards, pull rates, chase cards, price history, and sealed products.
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Optional

from db.connection import get_connection


def _slug(s: str) -> str:
    """Normalize to slug: lowercase, non-alnum to hyphen, collapse hyphens."""
    if not s:
        return ""
    s = re.sub(r"[^a-z0-9]+", "-", s.strip().lower())
    return re.sub(r"-+", "-", s).strip("-")


def resolve_set_id(identifier: str) -> Optional[str]:
    """
    Resolve a set identifier to canonical set_id so prices and chase cards are always for the correct set.
    Uses a single query with CASE-based priority to check exact id, case-insensitive id, exact name,
    case-insensitive name — all in one round trip. Falls back to slug matching only if needed.
    Returns canonical set_id or None if not found.
    """
    if not identifier or not identifier.strip():
        return None
    raw = identifier.strip()
    conn = get_connection()
    # Single query: prioritize exact id > ci id > exact name > ci name
    row = conn.execute(
        """SELECT id FROM sets
           WHERE id = ? OR LOWER(id) = LOWER(?) OR name = ? OR LOWER(name) = LOWER(?)
           ORDER BY
             CASE
               WHEN id = ? THEN 1
               WHEN LOWER(id) = LOWER(?) THEN 2
               WHEN name = ? THEN 3
               ELSE 4
             END
           LIMIT 1""",
        (raw, raw, raw, raw, raw, raw, raw),
    ).fetchone()
    if row:
        return row[0]
    # Slug fallback (rare — only if no direct match)
    slug_raw = _slug(raw)
    if slug_raw:
        for row in conn.execute("SELECT id, name FROM sets").fetchall():
            if _slug(row[1]) == slug_raw:
                return row[0]
    return None


def get_sets(series_filter: Optional[str] = None) -> list:
    """Return all sets, optionally filtered by series. For SELECT SET dropdown."""
    conn = get_connection()
    try:
        if series_filter and series_filter.lower() != "all series":
            cur = conn.execute(
                "SELECT id, name, series, release_date, logo_url, total, value_index FROM sets WHERE series = ? ORDER BY release_date DESC",
                (series_filter,),
            )
        else:
            cur = conn.execute(
                "SELECT id, name, series, release_date, logo_url, total, value_index FROM sets ORDER BY release_date DESC"
            )
        return [dict(row) for row in cur.fetchall()]
    finally:
        pass  # Connection reused via pooling


def get_set_by_id(set_id: str) -> Optional[dict]:
    """Return one set by id, or None."""
    conn = get_connection()
    try:
        cur = conn.execute(
            "SELECT id, name, series, release_date, logo_url, total, value_index FROM sets WHERE id = ?",
            (set_id,),
        )
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        pass  # Connection reused via pooling


def get_cards_by_set(set_id: str) -> list[dict]:
    """Return all cards for a set."""
    conn = get_connection()
    try:
        cur = conn.execute(
            """SELECT id, set_id, name, rarity, supertype, subtype, image_url, small_image_url,
                      tcgplayer_market, tcgplayer_low, tcgplayer_mid, tcgplayer_high
               FROM cards WHERE set_id = ? ORDER BY tcgplayer_market DESC, name""",
            (set_id,),
        )
        return [dict(row) for row in cur.fetchall()]
    finally:
        pass  # Connection reused via pooling


def get_pull_rates(set_id: str) -> list[dict]:
    """Return pull rates (per pack) for a set. For Pull Rates (Per Pack) section."""
    conn = get_connection()
    try:
        cur = conn.execute(
            "SELECT id, set_id, category, label, rate_per_pack, notes FROM pull_rates WHERE set_id = ? ORDER BY category, id",
            (set_id,),
        )
        return [dict(row) for row in cur.fetchall()]
    finally:
        pass  # Connection reused via pooling


def get_chase_cards(
    set_id: str,
    rarity_filter: Optional[str] = None,
    limit: int = 24,
) -> list:
    """
    Return high-value (chase) cards for a set only. Uses set_id strictly so prices are correct for that set.
    rarity_filter: 'All' | 'Illustration Rare' | 'Special Art' | 'Holo' etc. Uses simple LIKE so filters work like before.
    """
    conn = get_connection()
    try:
        if rarity_filter and rarity_filter.strip().lower() != "all":
            r = rarity_filter.strip()
            cur = conn.execute(
                """SELECT id, set_id, name, rarity, image_url, small_image_url,
                          tcgplayer_market, tcgplayer_low, tcgplayer_mid, tcgplayer_high
                   FROM cards
                   WHERE set_id = ? AND (tcgplayer_market IS NOT NULL OR tcgplayer_mid IS NOT NULL)
                     AND (rarity LIKE ? OR rarity = ?)
                   ORDER BY COALESCE(tcgplayer_market, tcgplayer_mid) DESC
                   LIMIT ?""",
                (set_id, f"%{r}%", r, limit),
            )
        else:
            cur = conn.execute(
                """SELECT id, set_id, name, rarity, image_url, small_image_url,
                          tcgplayer_market, tcgplayer_low, tcgplayer_mid, tcgplayer_high
                   FROM cards
                   WHERE set_id = ? AND (tcgplayer_market IS NOT NULL OR tcgplayer_mid IS NOT NULL)
                   ORDER BY COALESCE(tcgplayer_market, tcgplayer_mid) DESC
                   LIMIT ?""",
                (set_id, limit),
            )
        return [dict(row) for row in cur.fetchall()]
    finally:
        pass  # Connection reused via pooling


def get_graded_prices(card_id: str) -> list:
    """Return graded prices (PSA, CGC, BGS) for a card, including all grade levels per grader."""
    conn = get_connection()
    try:
        cur = conn.execute(
            """SELECT grader, grade, grade_label, market, low, high, source, updated_at
               FROM graded_prices WHERE card_id = ? ORDER BY grader, grade DESC""",
            (card_id,),
        )
        return [dict(row) for row in cur.fetchall()]
    finally:
        pass  # Connection reused via pooling


# ===== Card Price History =====


def insert_card_price_history(card_id: str, prices: dict) -> bool:
    """
    Record a price snapshot for a card (max once per day per card to prevent duplicates).
    prices: {raw, psa10, psa9, psa8, cgc10, cgc95, cgc9, bgs10, bgs95, bgs9}
    """
    conn = get_connection()
    try:
        # Skip if already recorded today
        today = datetime.utcnow().strftime("%Y-%m-%d")
        existing = conn.execute(
            "SELECT 1 FROM card_price_history WHERE card_id = ? AND DATE(recorded_at) = ?",
            (card_id, today),
        ).fetchone()
        if existing:
            return False
        conn.execute(
            """INSERT INTO card_price_history
               (card_id, source, price_raw, price_psa10, price_psa9, price_psa8,
                price_cgc10, price_cgc95, price_cgc9, price_bgs10, price_bgs95, price_bgs9)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                card_id,
                prices.get("source", "tcgplayer"),
                prices.get("raw"),
                prices.get("psa10"),
                prices.get("psa9"),
                prices.get("psa8"),
                prices.get("cgc10"),
                prices.get("cgc95"),
                prices.get("cgc9"),
                prices.get("bgs10"),
                prices.get("bgs95"),
                prices.get("bgs9"),
            ),
        )
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        pass  # Connection reused via pooling


def get_card_price_history(card_id: str, days: int = 90) -> list[dict]:
    """Fetch price history for a card for chart rendering."""
    conn = get_connection()
    try:
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        cur = conn.execute(
            """SELECT card_id, price_raw, price_psa10, price_psa9, price_psa8,
                      price_cgc10, price_cgc95, price_cgc9,
                      price_bgs10, price_bgs95, price_bgs9,
                      recorded_at
               FROM card_price_history
               WHERE card_id = ? AND recorded_at >= ?
               ORDER BY recorded_at ASC""",
            (card_id, cutoff),
        )
        return [dict(row) for row in cur.fetchall()]
    finally:
        pass  # Connection reused via pooling


def batch_insert_card_price_history(records: list[dict]) -> int:
    """
    Batch insert price history records using executemany for efficiency.
    Each record: {card_id, source, raw, psa10, psa9, ...}
    Returns count of inserted rows.
    """
    if not records:
        return 0
    conn = get_connection()
    try:
        params = [
            (
                r["card_id"],
                r.get("source", "tcgplayer"),
                r.get("raw"),
                r.get("psa10"),
                r.get("psa9"),
                r.get("psa8"),
                r.get("cgc10"),
                r.get("cgc95"),
                r.get("cgc9"),
                r.get("bgs10"),
                r.get("bgs95"),
                r.get("bgs9"),
            )
            for r in records
        ]
        conn.executemany(
            """INSERT INTO card_price_history
               (card_id, source, price_raw, price_psa10, price_psa9, price_psa8,
                price_cgc10, price_cgc95, price_cgc9, price_bgs10, price_bgs95, price_bgs9)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            params,
        )
        conn.commit()
        return len(params)
    except Exception:
        return 0


# ===== Sealed Products =====


def insert_sealed_product(
    name: str,
    set_name: str,
    product_type: str,
    msrp: float,
    image_url: Optional[str] = None,
    current_price: Optional[float] = None,
    in_print: bool = True,
    notes: Optional[str] = None,
) -> Optional[int]:
    """Insert a sealed product. Returns the row ID or None on failure."""
    conn = get_connection()
    try:
        cur = conn.execute(
            """INSERT INTO sealed_products (name, set_name, product_type, msrp, current_price, image_url, in_print, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (name, set_name, product_type, msrp, current_price or msrp, image_url, 1 if in_print else 0, notes),
        )
        conn.commit()
        return cur.lastrowid
    except Exception:
        return None
    finally:
        pass  # Connection reused via pooling


def upsert_sealed_product(
    name: str,
    set_name: str,
    product_type: str,
    msrp: float,
    image_url: Optional[str] = None,
    current_price: Optional[float] = None,
    in_print: bool = True,
    notes: Optional[str] = None,
) -> Optional[int]:
    """Insert or update a sealed product by name + set_name. Returns the row ID."""
    conn = get_connection()
    try:
        # Check if exists
        row = conn.execute(
            "SELECT id FROM sealed_products WHERE name = ? AND set_name = ?",
            (name, set_name),
        ).fetchone()
        if row:
            conn.execute(
                """UPDATE sealed_products SET product_type = ?, msrp = ?, current_price = ?,
                   image_url = COALESCE(?, image_url), in_print = ?, notes = COALESCE(?, notes),
                   updated_at = CURRENT_TIMESTAMP
                   WHERE id = ?""",
                (product_type, msrp, current_price or msrp, image_url, 1 if in_print else 0, notes, row[0]),
            )
            conn.commit()
            return row[0]
        else:
            return insert_sealed_product(name, set_name, product_type, msrp, image_url, current_price, in_print, notes)
    except Exception:
        return None
    finally:
        pass  # Connection reused via pooling


def get_sealed_products(
    set_name: Optional[str] = None,
    product_type: Optional[str] = None,
) -> list[dict]:
    """List sealed products with optional filters."""
    conn = get_connection()
    try:
        sql = "SELECT * FROM sealed_products WHERE 1=1"
        params: list = []
        if set_name:
            sql += " AND set_name = ?"
            params.append(set_name)
        if product_type:
            sql += " AND product_type = ?"
            params.append(product_type)
        sql += " ORDER BY set_name, product_type, name"
        cur = conn.execute(sql, params)
        rows = [dict(row) for row in cur.fetchall()]
        # Add computed premium_pct
        for r in rows:
            if r.get("msrp") and r.get("current_price") and r["msrp"] > 0:
                r["premium_pct"] = round(((r["current_price"] - r["msrp"]) / r["msrp"]) * 100, 1)
            else:
                r["premium_pct"] = 0
        return rows
    finally:
        pass  # Connection reused via pooling


def get_sealed_product_by_id(product_id: int) -> Optional[dict]:
    """Get a single sealed product by ID."""
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM sealed_products WHERE id = ?", (product_id,)).fetchone()
        if not row:
            return None
        r = dict(row)
        if r.get("msrp") and r.get("current_price") and r["msrp"] > 0:
            r["premium_pct"] = round(((r["current_price"] - r["msrp"]) / r["msrp"]) * 100, 1)
        else:
            r["premium_pct"] = 0
        return r
    finally:
        pass  # Connection reused via pooling


def update_sealed_price(product_id: int, price: float) -> bool:
    """Update current price for a sealed product."""
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE sealed_products SET current_price = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (price, product_id),
        )
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        pass  # Connection reused via pooling


# ===== Sealed Price History =====


def insert_sealed_price_history(sealed_product_id: int, price: float, source: str = "manual") -> bool:
    """Record a price snapshot for a sealed product."""
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO sealed_price_history (sealed_product_id, price, source) VALUES (?, ?, ?)",
            (sealed_product_id, price, source),
        )
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        pass  # Connection reused via pooling


def get_sealed_price_history(sealed_product_id: int, days: int = 90) -> list[dict]:
    """Fetch price history for a sealed product for chart rendering."""
    conn = get_connection()
    try:
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        cur = conn.execute(
            """SELECT sealed_product_id, price, source, recorded_at
               FROM sealed_price_history
               WHERE sealed_product_id = ? AND recorded_at >= ?
               ORDER BY recorded_at ASC""",
            (sealed_product_id, cutoff),
        )
        return [dict(row) for row in cur.fetchall()]
    finally:
        pass  # Connection reused via pooling


# ===== Graded Prices (Updated) =====


def upsert_graded_price(
    card_id: str,
    grader: str,
    grade: str,
    market: Optional[float] = None,
    low: Optional[float] = None,
    high: Optional[float] = None,
    grade_label: Optional[str] = None,
    source: Optional[str] = None,
) -> bool:
    """Insert or update a graded price entry. Uses UNIQUE(card_id, grader, grade)."""
    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO graded_prices (card_id, grader, grade, grade_label, market, low, high, source)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(card_id, grader, grade) DO UPDATE SET
                 market = COALESCE(excluded.market, market),
                 low = COALESCE(excluded.low, low),
                 high = COALESCE(excluded.high, high),
                 grade_label = COALESCE(excluded.grade_label, grade_label),
                 source = COALESCE(excluded.source, source),
                 updated_at = CURRENT_TIMESTAMP""",
            (card_id, grader, grade, grade_label, market, low, high, source),
        )
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        pass  # Connection reused via pooling


def get_graded_prices_structured(card_id: str) -> dict:
    """
    Return graded prices structured by grader and grade.
    Returns: {"PSA": {"10": {"market": 150, "low": 120, "high": 200}, "9": {...}}, "CGC": {...}, "BGS": {...}}
    """
    conn = get_connection()
    try:
        cur = conn.execute(
            """SELECT grader, grade, grade_label, market, low, high, source, updated_at
               FROM graded_prices WHERE card_id = ? ORDER BY grader, grade DESC""",
            (card_id,),
        )
        result: dict = {}
        for row in cur.fetchall():
            r = dict(row)
            grader = r["grader"].upper()
            grade = r["grade"]
            if grader not in result:
                result[grader] = {}
            result[grader][grade] = {
                "market": r["market"],
                "low": r["low"],
                "high": r["high"],
                "grade_label": r.get("grade_label"),
                "source": r.get("source"),
                "updated_at": r.get("updated_at"),
            }
        return result
    finally:
        pass  # Connection reused via pooling


# ===== Trending Cards =====


def get_trending_cards(limit: int = 20) -> list[dict]:
    """
    Return cards with highest price, ordered by market price.
    Uses bulk queries instead of per-card lookups for price change data.
    """
    conn = get_connection()
    try:
        cur = conn.execute(
            """SELECT c.id, c.name, c.set_id, c.rarity, c.image_url, c.small_image_url,
                      c.tcgplayer_market, c.tcgplayer_low, c.tcgplayer_mid, c.tcgplayer_high,
                      s.name as set_name
               FROM cards c
               LEFT JOIN sets s ON c.set_id = s.id
               WHERE c.tcgplayer_market IS NOT NULL AND c.tcgplayer_market > 0
               ORDER BY c.tcgplayer_market DESC
               LIMIT ?""",
            (limit,),
        )
        cards = [dict(row) for row in cur.fetchall()]
        if not cards:
            return cards

        card_ids = [c["id"] for c in cards]
        placeholders = ",".join("?" * len(card_ids))

        # Bulk fetch 7-day and 30-day old prices in 2 queries instead of 2*N
        week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
        month_ago = (datetime.utcnow() - timedelta(days=30)).isoformat()

        # 7-day: get the most recent price_raw at or before 7 days ago per card
        prices_7d: dict[str, float] = {}
        rows_7d = conn.execute(
            f"""SELECT card_id, price_raw FROM card_price_history
                WHERE card_id IN ({placeholders}) AND recorded_at <= ?
                ORDER BY card_id, recorded_at DESC""",
            (*card_ids, week_ago),
        ).fetchall()
        for row in rows_7d:
            cid = row[0]
            if cid not in prices_7d and row[1]:
                prices_7d[cid] = row[1]

        # 30-day: same approach
        prices_30d: dict[str, float] = {}
        rows_30d = conn.execute(
            f"""SELECT card_id, price_raw FROM card_price_history
                WHERE card_id IN ({placeholders}) AND recorded_at <= ?
                ORDER BY card_id, recorded_at DESC""",
            (*card_ids, month_ago),
        ).fetchall()
        for row in rows_30d:
            cid = row[0]
            if cid not in prices_30d and row[1]:
                prices_30d[cid] = row[1]

        # Attach change metrics
        for card in cards:
            cid = card["id"]
            mkt = card["tcgplayer_market"]
            old7 = prices_7d.get(cid)
            card["change_7d"] = round(((mkt - old7) / old7) * 100, 1) if old7 and mkt else 0
            old30 = prices_30d.get(cid)
            card["change_30d"] = round(((mkt - old30) / old30) * 100, 1) if old30 and mkt else 0

        return cards
    finally:
        pass  # Connection reused via pooling
