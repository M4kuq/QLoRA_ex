import json

import pytest

from finetune_lab.schemas import OperationPlan, SFTRecord, parse_operation_json


def test_valid_operation_plan_accepts_expected_json() -> None:
    plan = OperationPlan.model_validate(
        {
            "intent": "search_tasks",
            "target": "tasks",
            "filters": {"status": "not_done", "due": "overdue", "priority": "high"},
            "sort": ["due_date_asc"],
            "limit": 20,
        }
    )

    assert plan.intent == "search_tasks"
    assert plan.target == "tasks"
    assert plan.filters.status == "not_done"


def test_intent_target_mismatch_is_rejected() -> None:
    with pytest.raises(ValueError, match="requires target"):
        OperationPlan.model_validate(
            {
                "intent": "search_tasks",
                "target": "documents",
                "filters": {"status": "not_done"},
                "sort": ["created_at_desc"],
                "limit": 20,
            }
        )


def test_disallowed_filter_for_target_is_rejected() -> None:
    with pytest.raises(ValueError, match="filters not allowed"):
        OperationPlan.model_validate(
            {
                "intent": "search_documents",
                "target": "documents",
                "filters": {"assignee": "田中", "status": "not_archived"},
                "sort": ["created_at_desc"],
                "limit": 20,
            }
        )


def test_disallowed_sort_for_target_is_rejected() -> None:
    with pytest.raises(ValueError, match="sort keys not allowed"):
        OperationPlan.model_validate(
            {
                "intent": "search_jobs",
                "target": "jobs",
                "filters": {"status": "failed", "created": "yesterday"},
                "sort": ["score_desc"],
                "limit": 20,
            }
        )


def test_sft_record_validates_assistant_json() -> None:
    assistant_payload = {
        "intent": "search_tasks",
        "target": "tasks",
        "filters": {"status": "not_done", "due": "overdue"},
        "sort": ["due_date_asc"],
        "limit": 20,
    }
    record = SFTRecord.model_validate(
        {
            "messages": [
                {"role": "system", "content": "JSONのみを返してください。"},
                {"role": "user", "content": "期限切れの未完了タスクを出して"},
                {"role": "assistant", "content": json.dumps(assistant_payload, ensure_ascii=False)},
            ]
        }
    )

    assert record.user_content == "期限切れの未完了タスクを出して"
    assert record.assistant_plan.intent == "search_tasks"


def test_parse_operation_json_rejects_non_json_text() -> None:
    with pytest.raises(ValueError, match="not valid JSON"):
        parse_operation_json("こちらがJSONです: {}")
