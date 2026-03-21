"""Base class for database API MCP servers."""
import hashlib
import json
import time
from typing import Any

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
