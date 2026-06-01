from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


def to_prompt_completion(example: Mapping[str, Any]) -> dict[str, Any]:
    messages = example.get("messages")
    if not isinstance(messages, Sequence) or isinstance(messages, str):
        raise ValueError("example must contain a messages sequence")
    if len(messages) < 2:
        raise ValueError(
            "messages must contain at least one prompt message and one assistant message"
        )

    assistant_message = messages[-1]
    if not isinstance(assistant_message, Mapping):
        raise ValueError("last message must be a mapping")
    if assistant_message.get("role") != "assistant":
        raise ValueError("last message must be an assistant message")

    prompt_messages = list(messages[:-1])
    if not prompt_messages:
        raise ValueError("prompt messages must not be empty")

    return {
        "prompt": prompt_messages,
        "completion": [dict(assistant_message)],
    }
