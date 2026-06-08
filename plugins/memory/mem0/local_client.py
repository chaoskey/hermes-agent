"""Local Mem0 REST client compatible with the Mem0 MemoryClient surface.

This adapter targets self-hosted Mem0 REST servers (for example
http://localhost:8888) whose routes differ from the hosted Mem0 API.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional


class LocalMemoryClient:
    """Drop-in replacement for mem0.MemoryClient against local REST endpoints."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        endpoint: Optional[str] = "http://localhost:8888",
        timeout: float = 30.0,
    ):
        self.api_key = api_key or os.getenv("MEM0_API_KEY")
        self.host = (endpoint or os.getenv("MEM0_ENDPOINT")).rstrip("/")
        self.timeout = timeout
        # print("self.api_key:", self.api_key, flush=True)
        # print("self.host:", self.host, flush=True)
        # print("self.timeout:", self.timeout, flush=True)


    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            # Local deployments may accept either of these headers.
            headers["X-API-Key"] = self.api_key
            headers["Authorization"] = f"Token {self.api_key}"
        return headers

    def _request(
        self,
        method: str,
        path: str,
        *,
        json_body: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Any:
        url = f"{self.host}{path}"
        if params:
            clean_params = {k: v for k, v in params.items() if v is not None}
            if clean_params:
                url = f"{url}?{urllib.parse.urlencode(clean_params, doseq=True)}"

        data = None
        if json_body is not None:
            data = json.dumps(json_body).encode("utf-8")

        req = urllib.request.Request(
            url=url,
            data=data,
            headers=self._headers(),
            method=method,
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                body = resp.read().decode("utf-8")
                return json.loads(body) if body else {}
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace") if exc.fp else str(exc)
            raise RuntimeError(f"Mem0 local API error {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Mem0 local API request failed: {exc}") from exc

    @staticmethod
    def _normalize_options(options: Optional[Any], kwargs: Dict[str, Any]) -> Dict[str, Any]:
        payload = dict(kwargs)
        if options is None:
            return payload
        if hasattr(options, "model_dump"):
            payload.update(options.model_dump(exclude_unset=True))
        elif isinstance(options, dict):
            payload.update(options)
        return payload

    @staticmethod
    def _normalize_messages(messages: Any) -> List[Dict[str, Any]]:
        if isinstance(messages, str):
            return [{"role": "user", "content": messages}]
        if isinstance(messages, dict):
            return [messages]
        if isinstance(messages, list):
            return messages
        raise ValueError(f"messages must be str, dict, or list[dict], got {type(messages).__name__}")

    @staticmethod
    def _extract_entity_params(payload: Dict[str, Any]) -> Dict[str, Any]:
        out = dict(payload)
        filters = out.pop("filters", None)
        if isinstance(filters, dict):
            for key in ("user_id", "agent_id", "run_id"):
                if key in filters and key not in out:
                    out[key] = filters[key]
        return out

    def add(self, messages, options: Optional[Any] = None, **kwargs) -> Dict[str, Any]:
        payload = self._normalize_options(options, kwargs)
        payload = self._extract_entity_params(payload)
        payload["messages"] = self._normalize_messages(messages)
        return self._request("POST", "/memories", json_body=payload)

    def get(self, memory_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/memories/{memory_id}")

    def get_all(self, options: Optional[Any] = None, **kwargs) -> Dict[str, Any]:
        params = self._normalize_options(options, kwargs)
        params = self._extract_entity_params(params)
        return self._request("GET", "/memories", params=params)

    def search(self, query: str, options: Optional[Any] = None, **kwargs) -> Dict[str, Any]:
        payload = self._normalize_options(options, kwargs)
        # 不再调用 _extract_entity_params，避免 user_id 泄漏到顶层
        payload["query"] = query
        return self._request("POST", "/search", json_body=payload)

    def update(self, memory_id: str, options: Optional[Any] = None, **kwargs) -> Dict[str, Any]:
        payload = self._normalize_options(options, kwargs)
        if "data" in payload and "text" not in payload:
            payload["text"] = payload.pop("data")
        return self._request("PUT", f"/memories/{memory_id}", json_body=payload)

    def delete(self, memory_id: str) -> Dict[str, Any]:
        return self._request("DELETE", f"/memories/{memory_id}")

    def delete_all(self, options: Optional[Any] = None, **kwargs) -> Dict[str, Any]:
        params = self._normalize_options(options, kwargs)
        params = self._extract_entity_params(params)
        return self._request("DELETE", "/memories", params=params)

    def history(self, memory_id: str) -> List[Dict[str, Any]]:
        return self._request("GET", f"/memories/{memory_id}/history")

    def reset(self) -> Dict[str, Any]:
        return self._request("POST", "/reset")
