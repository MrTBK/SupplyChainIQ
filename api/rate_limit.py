"""In-memory sliding-window rate limiter (per-key). Single-process demo scale.

For multi-worker production, replace _buckets with Redis (same function shapes).
"""

from __future__ import annotations

import os
import threading
import time
from collections import deque

MAX_ATTEMPTS = int(os.environ.get("SCI_LOGIN_MAX_ATTEMPTS", "5"))
WINDOW_S = int(os.environ.get("SCI_LOGIN_WINDOW_S", "300"))

_buckets: dict[str, deque[float]] = {}
_lock = threading.Lock()


def _now() -> float:
    return time.monotonic()


def _prune(key: str, now: float) -> deque[float]:
    q = _buckets.get(key)
    if q is None:
        q = _buckets[key] = deque()
    while q and now - q[0] > WINDOW_S:
        q.popleft()
    return q


def login_allowed(key: str) -> tuple[bool, int]:
    """Returns (allowed, retry_after_seconds). Counts failures only."""
    now = _now()
    with _lock:
        q = _prune(key, now)
        if len(q) >= MAX_ATTEMPTS:
            return False, max(1, int(WINDOW_S - (now - q[0])))
        return True, 0


def record_login_failure(key: str) -> None:
    with _lock:
        _prune(key, _now()).append(_now())


def clear_login(key: str) -> None:
    with _lock:
        _buckets.pop(key, None)


def reset_all() -> None:
    """Tests only."""
    with _lock:
        _buckets.clear()
