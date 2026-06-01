import json

from finetune_lab.prompts import PROMPT_ONLY_SYSTEM_PROMPT, build_prompt_messages
from finetune_lab.schemas import SFTRecord


def _record() -> SFTRecord:
    payload = {
        "intent": "search_documents",
        "target": "documents",
        "filters": {"status": "not_archived"},
        "sort": ["created_at_desc"],
        "limit": 20,
    }
    return SFTRecord.model_validate(
        {
            "messages": [
                {"role": "system", "content": "JSONのみ"},
                {"role": "user", "content": "アーカイブ済みではないドキュメントを出して"},
                {"role": "assistant", "content": json.dumps(payload, ensure_ascii=False)},
            ]
        }
    )


def test_base_prompt_uses_user_message_only() -> None:
    messages = build_prompt_messages(_record(), "base")

    assert messages == [
        {"role": "user", "content": "アーカイブ済みではないドキュメントを出して"}
    ]


def test_prompt_only_adds_json_system_instruction() -> None:
    messages = build_prompt_messages(_record(), "prompt-only")

    assert messages[0]["role"] == "system"
    assert "出力はJSONのみ" in messages[0]["content"]
    assert "search_documents" in PROMPT_ONLY_SYSTEM_PROMPT
    assert messages[1]["role"] == "user"
