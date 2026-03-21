"""Base class for database API MCP servers."""
import hashlib
import json
from typing import Any

import httpx


class BaseDatabaseServer:
    def __init__(self, name: str, base_url: str = "", api_key: str = ""):
        self.name = name
        self.base_url = base_url
        self.api_key = api_key
        self._cache: dict[str, Any] = {}

    def _cache_key(self, endpoint: str, params: dict) -> str:
        payload = json.dumps({"endpoint": endpoint, "params": params}, sort_keys=True)
        return hashlib.sha256(payload.encode()).hexdigest()

    def get(self, endpoint: str, params: dict | None = None, use_cache: bool = True) -> Any:
        params = params or {}
        key = self._cache_key(endpoint, params)
        if use_cache and key in self._cache:
            return self._cache[key]
        url = self.base_url.rstrip("/") + "/" + endpoint.lstrip("/")
        with httpx.Client() as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            try:
                result = response.json()
            except Exception:
                result = response.text
        if use_cache:
            self._cache[key] = result
        return result
