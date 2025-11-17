# tarot_cache.py
import os
import json
import lmdb
import requests
import datetime
from typing import List, Dict, Any

TAROT_API = "https://tarotapi.dev/api/v1/cards/random?n=3"
DEFAULT_DIR = os.path.join(".", "tarot", "data", "tarot_cache")
DEFAULT_MAP_SIZE = 10 * 1024 * 1024  # 10 MB

class TarotStore:
    def __init__(self, path: str = DEFAULT_DIR, map_size: int = DEFAULT_MAP_SIZE, db_name: str = "cards"):
        os.makedirs(path, exist_ok=True)
        self.env = lmdb.open(
            path,
            map_size=map_size,
            max_dbs=2,
            subdir=True,
            create=True,
            lock=True,
            readahead=False,  # small random I/O
        )
        self.db = self.env.open_db(db_name.encode("utf-8"))

    def close(self):
        self.env.close()

    @staticmethod
    def _today_key(user_id: int, tzinfo: datetime.tzinfo) -> bytes:
        today = datetime.datetime.now(tzinfo).date().isoformat()
        return f"{today}:{user_id}".encode("utf-8")

    def get_cached_cards(self, user_id: int, tzinfo: datetime.tzinfo) -> List[Dict[str, Any]] | None:
        key = self._today_key(user_id, tzinfo)
        with self.env.begin(db=self.db) as txn:
            raw = txn.get(key)
        if not raw:
            return None
        try:
            return json.loads(raw.decode("utf-8"))
        except Exception:
            return None

    def _fetch_three_cards(self, timeout: float = 10.0) -> List[Dict[str, Any]]:
        # Raises requests exceptions on failure; caller handles
        resp = requests.get(TAROT_API, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        cards = data.get("cards", [])
        if not isinstance(cards, list) or len(cards) == 0:
            raise ValueError("Empty or invalid cards payload")
        return cards[:3]

    def get_or_create_today_cards(self, user_id: int, tzinfo: datetime.tzinfo) -> List[Dict[str, Any]]:
        cached = self.get_cached_cards(user_id, tzinfo)
        if cached:
            return cached
        cards = self._fetch_three_cards()
        payload = json.dumps(cards, separators=(",", ":")).encode("utf-8")
        key = self._today_key(user_id, tzinfo)
        with self.env.begin(write=True, db=self.db) as txn:
            txn.put(key, payload)
        return cards

    def clear_all(self):
        # Remove all keys in the sub-db (daily scheduled)
        with self.env.begin(write=True, db=self.db) as txn:
            with txn.cursor() as cur:
                if cur.first():
                    do_delete = True
                    while do_delete:
                        cur.delete()
                        do_delete = cur.next()
