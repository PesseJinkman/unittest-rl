from __future__ import annotations

import csv
import logging
import sys
from pathlib import Path
from typing import Any


def get_logger(name: str = "unittest-rl", level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(level)
    h = logging.StreamHandler(sys.stdout)
    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s", "%H:%M:%S")
    h.setFormatter(fmt)
    logger.addHandler(h)
    logger.propagate = False
    return logger


class CSVLogger:
    """Append-only CSV logger with automatic header + backfill for new columns."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._columns: list[str] | None = None
        if self.path.exists():
            try:
                with open(self.path, "r", newline="", encoding="utf-8") as f:
                    r = csv.reader(f)
                    header = next(r, None)
                    if header:
                        self._columns = header
            except Exception:
                self._columns = None

    def log(self, row: dict[str, Any]) -> None:
        keys = list(row.keys())
        if self._columns is None:
            self._columns = keys
            with open(self.path, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(self._columns)
                w.writerow([row.get(k, "") for k in self._columns])
            return
        # extend columns if new keys appear
        new_cols = [k for k in keys if k not in self._columns]
        if new_cols:
            self._columns = self._columns + new_cols
            # rewrite with extended header
            existing = []
            with open(self.path, "r", newline="", encoding="utf-8") as f:
                r = csv.DictReader(f)
                for rec in r:
                    existing.append(rec)
            with open(self.path, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=self._columns)
                w.writeheader()
                for rec in existing:
                    w.writerow({k: rec.get(k, "") for k in self._columns})
        with open(self.path, "a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=self._columns)
            w.writerow({k: row.get(k, "") for k in self._columns})
