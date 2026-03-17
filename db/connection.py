"""
Database connection and schema.
Uses SQLite; DB file is in project root: pokemon_tcg.db
Connection pooling via a thread-local reusable connection.
"""
import sqlite3
import threading
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "pokemon_tcg.db"

# Thread-local storage for connection reuse (simple connection pooling)
_local = threading.local()

SCHEMA = """
-- Agent settings for autonomous purchasing rules
CREATE TABLE IF NOT EXISTS agent_settings (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    autonomy_level INTEGER NOT NULL DEFAULT 0,
    daily_budget REAL DEFAULT 0,
    per_card_max REAL DEFAULT 0,
    deal_threshold_percent REAL DEFAULT 15,
    psa10_only INTEGER DEFAULT 1,
    raw_allowed INTEGER DEFAULT 0,
    modern_only INTEGER DEFAULT 1,
    ebay_allowed INTEGER DEFAULT 1,
    tcgplayer_allowed INTEGER DEFAULT 1,
    facebook_allowed INTEGER DEFAULT 0,
    notification_discord INTEGER DEFAULT 1,
    notification_telegram INTEGER DEFAULT 0,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Insert default settings if not exists
INSERT OR IGNORE INTO agent_settings (id, autonomy_level, daily_budget, per_card_max, deal_threshold_percent)
VALUES (1, 0, 500, 200, 15);

-- Sets from Pokémon TCG API (id, name, series, releaseDate, images.logo, total, value_index)
CREATE TABLE IF NOT EXISTS sets (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    series TEXT,
    release_date TEXT,
    logo_url TEXT,
    total INTEGER,
    value_index REAL,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Cards: id, name, set_id, rarity, images, tcgplayer prices
CREATE TABLE IF NOT EXISTS cards (
    id TEXT PRIMARY KEY,
    set_id TEXT NOT NULL,
    name TEXT NOT NULL,
    rarity TEXT,
    supertype TEXT,
    subtype TEXT,
    image_url TEXT,
    small_image_url TEXT,
    tcgplayer_market REAL,
    tcgplayer_low REAL,
    tcgplayer_mid REAL,
    tcgplayer_high REAL,
    raw_json TEXT,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (set_id) REFERENCES sets(id)
);

CREATE INDEX IF NOT EXISTS idx_cards_set_id ON cards(set_id);
CREATE INDEX IF NOT EXISTS idx_cards_rarity ON cards(rarity);
CREATE INDEX IF NOT EXISTS idx_cards_tcgplayer_market ON cards(tcgplayer_market DESC);
-- Chase cards per set: fast "top N by price for this set"
CREATE INDEX IF NOT EXISTS idx_cards_set_market ON cards(set_id, tcgplayer_market DESC);

-- Pull rates per pack (community estimates): set_id, rarity/card_type, rate, source
CREATE TABLE IF NOT EXISTS pull_rates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    set_id TEXT NOT NULL,
    category TEXT NOT NULL,
    label TEXT,
    rate_per_pack REAL,
    notes TEXT,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (set_id) REFERENCES sets(id)
);

CREATE INDEX IF NOT EXISTS idx_pull_rates_set_id ON pull_rates(set_id);

-- Graded prices (PSA, CGC, Beckett/BGS) per card — PriceCharting/eBay style
CREATE TABLE IF NOT EXISTS graded_prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    card_id TEXT NOT NULL,
    grader TEXT NOT NULL,
    grade TEXT NOT NULL,
    grade_label TEXT,
    market REAL,
    low REAL,
    high REAL,
    source TEXT,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(card_id, grader, grade),
    FOREIGN KEY (card_id) REFERENCES cards(id)
);

CREATE INDEX IF NOT EXISTS idx_graded_prices_card_id ON graded_prices(card_id);

-- Price history for charts (raw + graded over time)
CREATE TABLE IF NOT EXISTS card_price_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    card_id TEXT NOT NULL,
    source TEXT DEFAULT 'tcgplayer',
    price_raw REAL,
    price_psa10 REAL,
    price_psa9 REAL,
    price_psa8 REAL,
    price_cgc10 REAL,
    price_cgc95 REAL,
    price_cgc9 REAL,
    price_bgs10 REAL,
    price_bgs95 REAL,
    price_bgs9 REAL,
    recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (card_id) REFERENCES cards(id)
);

CREATE INDEX IF NOT EXISTS idx_card_price_history_card_date ON card_price_history(card_id, recorded_at DESC);

-- Sealed products (ETBs, Booster Boxes, etc.)
CREATE TABLE IF NOT EXISTS sealed_products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    set_name TEXT,
    product_type TEXT,
    msrp REAL,
    current_price REAL,
    image_url TEXT,
    in_print INTEGER DEFAULT 1,
    notes TEXT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_sealed_products_set ON sealed_products(set_name);
CREATE INDEX IF NOT EXISTS idx_sealed_products_type ON sealed_products(product_type);

-- Sealed product price history for charts
CREATE TABLE IF NOT EXISTS sealed_price_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sealed_product_id INTEGER NOT NULL,
    price REAL NOT NULL,
    source TEXT DEFAULT 'manual',
    recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sealed_product_id) REFERENCES sealed_products(id)
);

CREATE INDEX IF NOT EXISTS idx_sealed_price_history_product_date ON sealed_price_history(sealed_product_id, recorded_at DESC);

-- User collections (card portfolio tracking)
CREATE TABLE IF NOT EXISTS user_collections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    card_id TEXT NOT NULL,
    quantity INTEGER DEFAULT 1,
    condition TEXT DEFAULT 'NM',
    purchase_price REAL,
    purchase_date TEXT,
    notes TEXT,
    date_added TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (card_id) REFERENCES cards(id),
    UNIQUE(user_id, card_id, condition)
);

CREATE INDEX IF NOT EXISTS idx_collection_user ON user_collections(user_id);
CREATE INDEX IF NOT EXISTS idx_collection_card ON user_collections(card_id);

-- Portfolio value history for charts
CREATE TABLE IF NOT EXISTS portfolio_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    total_value REAL NOT NULL,
    total_cards INTEGER NOT NULL,
    recorded_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_portfolio_user ON portfolio_history(user_id);
CREATE INDEX IF NOT EXISTS idx_portfolio_user_date ON portfolio_history(user_id, recorded_at DESC);

-- Card name index for search
CREATE INDEX IF NOT EXISTS idx_cards_name ON cards(name);

-- Compound index for sealed product filtering
CREATE INDEX IF NOT EXISTS idx_sealed_products_set_type ON sealed_products(set_name, product_type);
"""


def get_connection() -> sqlite3.Connection:
    """Return a thread-local reusable connection to the SQLite DB."""
    conn = getattr(_local, 'conn', None)
    if conn is not None:
        try:
            conn.execute("SELECT 1")
            return conn
        except (sqlite3.ProgrammingError, sqlite3.OperationalError):
            pass
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    _local.conn = conn
    return conn


def init_db() -> None:
    """Create DB file and tables if they do not exist. Runs migrations for existing DBs."""
    conn = get_connection()
    conn.executescript(SCHEMA)
    conn.commit()
    _run_migrations(conn)


def _run_migrations(conn: sqlite3.Connection) -> None:
    """Run safe ALTER TABLE migrations for existing databases."""
    migrations = [
        "ALTER TABLE sets ADD COLUMN value_index REAL",
        "ALTER TABLE sealed_products ADD COLUMN notes TEXT",
    ]
    for sql in migrations:
        try:
            conn.execute(sql)
            conn.commit()
        except sqlite3.OperationalError as e:
            if "duplicate column" not in str(e).lower():
                raise
