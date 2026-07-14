"""AOS Partner Runtime - Partner memory (PRJ-012). SQLite, standard library only.

Memory rules come from the Partner definition:
  remember_outcomes  - store workflow outcomes
  no_secrets         - refuse values that look like credentials (always on)
  retention_days     - optional cleanup horizon
"""

import datetime
import os
import sqlite3

SECRET_MARKERS = ("api_key", "apikey", "password", "secret", "token", "credential")


class MemoryError_(Exception):
    pass


class MemoryStore:
    def __init__(self, db_path):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS memory ("
            " partner TEXT, key TEXT, value TEXT, created TEXT,"
            " PRIMARY KEY (partner, key))")
        self.conn.commit()

    def remember(self, partner_id, key, value):
        blob = "%s %s" % (key, value)
        if any(m in blob.lower() for m in SECRET_MARKERS):
            raise MemoryError_("Refusing to store what looks like a credential")
        self.conn.execute(
            "INSERT OR REPLACE INTO memory (partner, key, value, created)"
            " VALUES (?, ?, ?, ?)",
            (partner_id, key, str(value),
             datetime.datetime.now().isoformat(timespec="seconds")))
        self.conn.commit()

    def recall(self, partner_id, key, default=None):
        row = self.conn.execute(
            "SELECT value FROM memory WHERE partner = ? AND key = ?",
            (partner_id, key)).fetchone()
        return row[0] if row else default

    def forget_older_than(self, partner_id, days):
        cutoff = (datetime.datetime.now()
                  - datetime.timedelta(days=days)).isoformat(timespec="seconds")
        self.conn.execute(
            "DELETE FROM memory WHERE partner = ? AND created < ?",
            (partner_id, cutoff))
        self.conn.commit()

    def close(self):
        self.conn.close()
