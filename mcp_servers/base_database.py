"""Base class for database API MCP servers."""
import hashlib
import json
import logging
import os
import time
from typing import Any

# Suppress noisy logs when running as MCP subprocess
if os.environ.get("GENOMIX_QUIET"):
    logging.basicConfig(level=logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("mcp").setLevel(logging.WARNING)

import httpx


class BaseDatabaseServer:
    def __init__(self, name: str, base_url: str = "", api_key: str = ""):
        self.name = name
        self.base_url = base_url
        self.api_key = api_key
        self._cache: dict[str, Any] = {}
        self._last_request_time: float = 0
        self._min_interval: float = 0.35  # ~3 req/sec (NCBI limit without API key)

    def _cache_key(self, endpoint: str, params: dict) -> str:
        payload = json.dumps({"endpoint": endpoint, "params": params}, sort_keys=True)
        return hashlib.sha256(payload.encode()).hexdigest()

    def _rate_limit(self) -> None:
        """Ensure minimum interval between requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last_request_time = time.time()

    def get(self, endpoint: str, params: dict | None = None, use_cache: bool = True) -> Any:
        params = params or {}
        key = self._cache_key(endpoint, params)
        if use_cache and key in self._cache:
            return self._cache[key]

        self._rate_limit()

        url = self.base_url.rstrip("/") + "/" + endpoint.lstrip("/")
        try:
            with httpx.Client(timeout=30) as client:
                response = client.get(url, params=params)
                response.raise_for_status()
                try:
                    result = response.json()
                except Exception:
                    result = response.text
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                # Rate limited — wait and retry once
                time.sleep(1.0)
                self._last_request_time = time.time()
                with httpx.Client(timeout=30) as client:
                    response = client.get(url, params=params)
                    response.raise_for_status()
                    try:
                        result = response.json()
                    except Exception:
                        result = response.text
            else:
                return json.dumps({"error": str(e)})
        except httpx.HTTPError as e:
            return json.dumps({"error": str(e)})

        if use_cache:
            self._cache[key] = result
        return result

    @staticmethod
    def compact_json(data: Any, max_chars: int = 2000) -> str:
        """Compact a JSON response to fit within token budget.

        Keeps structure but truncates long strings and deep nesting."""
        raw = json.dumps(data) if not isinstance(data, str) else data
        if len(raw) <= max_chars:
            return raw
        # Try to parse and extract key fields
        try:
            obj = json.loads(raw) if isinstance(raw, str) else data
        except (json.JSONDecodeError, TypeError):
            return raw[:max_chars] + "... [truncated]"
        compacted = _compact_value(obj, depth=0, max_depth=3)
        result = json.dumps(compacted, ensure_ascii=False)
        if len(result) > max_chars:
            return result[:max_chars] + "... [truncated]"
        return result


def _compact_value(val: Any, depth: int, max_depth: int) -> Any:
    """Recursively compact a JSON value."""
    if depth > max_depth:
        if isinstance(val, dict):
            return f"{{...{len(val)} keys}}"
        if isinstance(val, list):
            return f"[...{len(val)} items]"
        return val
    if isinstance(val, str):
        return val[:300] + "..." if len(val) > 300 else val
    if isinstance(val, dict):
        return {k: _compact_value(v, depth + 1, max_depth) for k, v in list(val.items())[:20]}
    if isinstance(val, list):
        return [_compact_value(v, depth + 1, max_depth) for v in val[:10]]
    return val
