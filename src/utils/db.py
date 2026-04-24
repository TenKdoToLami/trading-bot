import sqlite3
import pandas as pd
import os

class BotDB:
    def __init__(self, db_path="data/bot_data.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.init_db()

    def init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            # Market History
            conn.execute("""
                CREATE TABLE IF NOT EXISTS market_history (
                    date TEXT PRIMARY KEY,
                    spy_price REAL,
                    vix REAL
                )
            """)
            # Persistent State
            conn.execute("""
                CREATE TABLE IF NOT EXISTS bot_state (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            # Default State if empty
            defaults = [
                ('panic_mode', '0'),
                ('days_in_regime', '0'),
                ('current_tier', '-1'),
                ('tier_timer', '0')
            ]
            for k, v in defaults:
                conn.execute("INSERT OR IGNORE INTO bot_state (key, value) VALUES (?, ?)", (k, v))

    def add_daily_data(self, date, spy, vix):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT OR REPLACE INTO market_history VALUES (?, ?, ?)", (date, spy, vix))

    def get_history(self, limit=1000):
        with sqlite3.connect(self.db_path) as conn:
            return pd.read_sql(f"SELECT * FROM market_history ORDER BY date DESC LIMIT {limit}", conn).iloc[::-1]

    def get_state(self, key):
        with sqlite3.connect(self.db_path) as conn:
            res = conn.execute("SELECT value FROM bot_state WHERE key = ?", (key,)).fetchone()
            return res[0] if res else None

    def set_state(self, key, value):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT OR REPLACE INTO bot_state (key, value) VALUES (?, ?)", (key, str(value)))
