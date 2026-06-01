from __future__ import annotations

from typing import Literal

from finetune_lab.schemas import SFTRecord

PromptMode = Literal["base", "prompt-only"]

PROMPT_ONLY_SYSTEM_PROMPT = """あなたは日本語の業務指示をJSON操作計画に変換するアシスタントです。
出力はJSONのみです。説明文、Markdown、コードフェンスは出力しないでください。

JSON形式:
{
  "intent": "search_tasks",
  "target": "tasks",
  "filters": {},
  "sort": ["created_at_desc"],
  "limit": 20
}

intent候補:
- search_tasks
- search_projects
- search_documents
- search_jobs
- search_evaluation_runs

target候補:
- tasks
- projects
- documents
- jobs
- evaluation_runs

filtersで使える主なキー:
- project
- status
- assignee
- priority
- due
- created
- score_lt

sort候補:
- due_date_asc
- due_date_desc
- priority_desc
- priority_asc
- created_at_desc
- created_at_asc
- score_asc
- score_desc
"""


def build_prompt_messages(record: SFTRecord, mode: PromptMode) -> list[dict[str, str]]:
    if mode == "base":
        return [{"role": "user", "content": record.user_content}]
    if mode == "prompt-only":
        return [
            {"role": "system", "content": PROMPT_ONLY_SYSTEM_PROMPT},
            {"role": "user", "content": record.user_content},
        ]
    raise ValueError(f"unsupported prompt mode: {mode}")
