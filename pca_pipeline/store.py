"""Thread-safe, bounded, expiring cache; deliberately single-process."""

from __future__ import annotations

import re
import secrets
import threading
from collections import OrderedDict
from time import monotonic

from .errors import PipelineError


class ResultStore:
    """A result ID is a bearer capability, not a login or an authorization system."""

    def __init__(self, *, ttl_seconds=900, max_items=16, max_bytes=64 * 1024 * 1024, clock=monotonic):
        if ttl_seconds <= 0 or max_items <= 0 or max_bytes <= 0:
            raise ValueError("Cache limits must be positive")
        self.ttl_seconds = ttl_seconds
        self.max_items = max_items
        self.max_bytes = max_bytes
        self._clock = clock
        self._entries: OrderedDict[str, tuple[float, bytes]] = OrderedDict()
        self._bytes = 0
        self._lock = threading.Lock()

    def _remove(self, token):
        _, payload = self._entries.pop(token)
        self._bytes -= len(payload)

    def _purge_expired(self):
        now = self._clock()
        for token, (expires, _) in list(self._entries.items()):
            if now >= expires:
                self._remove(token)

    def put(self, payload: bytes) -> str:
        if len(payload) > self.max_bytes:
            raise PipelineError("RESULT_TOO_LARGE", "The reduced CSV exceeds the result-cache limit.", 413)
        with self._lock:
            self._purge_expired()
            while self._entries and (
                len(self._entries) >= self.max_items or self._bytes + len(payload) > self.max_bytes
            ):
                self._remove(next(iter(self._entries)))
            token = secrets.token_urlsafe(24)  # 192 random bits; 32 URL-safe characters.
            self._entries[token] = (self._clock() + self.ttl_seconds, payload)
            self._bytes += len(payload)
            return token

    def get(self, token: str) -> bytes | None:
        if not re.fullmatch(r"[A-Za-z0-9_-]{32}", token):
            return None
        with self._lock:
            self._purge_expired()
            entry = self._entries.get(token)
            return entry[1] if entry else None

    @property
    def cached_bytes(self):
        with self._lock:
            self._purge_expired()
            return self._bytes
