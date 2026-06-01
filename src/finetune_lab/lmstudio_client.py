from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class LMStudioConfig:
    base_url: str = "http://localhost:1234/v1"
    model: str = "qwen3.5:4b"
    api_key: str = "lm-studio"
    timeout_seconds: float = 60.0


class LMStudioClientError(RuntimeError):
    pass


class LMStudioClient:
    def __init__(self, config: LMStudioConfig) -> None:
        self.config = config

    def chat_completion(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.0,
        max_tokens: int = 256,
    ) -> str:
        url = f"{self.config.base_url.rstrip('/')}/chat/completions"
        payload: dict[str, Any] = {
            "model": self.config.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }
        request = Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urlopen(request, timeout=self.config.timeout_seconds) as response:
                body = response.read().decode("utf-8")
        except URLError as exc:
            raise LMStudioClientError(f"LM Studio request failed: {exc}") from exc

        try:
            data = json.loads(body)
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
            raise LMStudioClientError(f"Unexpected LM Studio response: {body[:500]}") from exc

        if not isinstance(content, str):
            raise LMStudioClientError("LM Studio response content is not a string")
        return content
