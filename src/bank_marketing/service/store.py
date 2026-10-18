"""Local restricted audit store; bounded retention, no names or free-text feedback."""

import json
import sqlite3
import time
from pathlib import Path


class Store:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS predictions (id TEXT PRIMARY KEY, ts REAL, "
                "version TEXT, probability REAL, abstain INTEGER, features TEXT, outcome INTEGER)"
            )
            db.execute(
                "CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, ts REAL, status TEXT, detail TEXT)"
            )
        self.path.chmod(0o600)

    def connect(self):
        return sqlite3.connect(self.path, timeout=10)

    def prediction(self, request_id, version, p, abstain, features):
        with self.connect() as db:
            db.execute("DELETE FROM predictions WHERE ts < ?", (time.time() - 30 * 86400,))
            db.execute(
                "INSERT INTO predictions VALUES (?,?,?,?,?,?,NULL)",
                (request_id, time.time(), version, p, int(abstain), json.dumps(features)),
            )

    def feedback(self, request_id, outcome):
        with self.connect() as db:
            db.execute("DELETE FROM predictions WHERE ts < ?", (time.time() - 30 * 86400,))
            row = db.execute("SELECT outcome FROM predictions WHERE id=?", (request_id,)).fetchone()
            if row is None:
                return "missing"
            if row[0] is not None and row[0] != outcome:
                return "conflict"
            db.execute("UPDATE predictions SET outcome=? WHERE id=?", (outcome, request_id))
        return "ok"

    def rows(self, version):
        with self.connect() as db:
            db.execute("DELETE FROM predictions WHERE ts < ?", (time.time() - 30 * 86400,))
            db.row_factory = sqlite3.Row
            return [
                dict(r) for r in db.execute("SELECT * FROM predictions WHERE version=?", (version,))
            ]

    def job(self, job_id, status, detail):
        with self.connect() as db:
            db.execute(
                "INSERT OR REPLACE INTO jobs VALUES (?,?,?,?)",
                (job_id, time.time(), status, detail),
            )

    def get_job(self, job_id):
        with self.connect() as db:
            db.row_factory = sqlite3.Row
            row = db.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        return dict(row) if row else None
