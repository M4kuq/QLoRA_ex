import json

from finetune_lab.evaluator import (
    build_prediction_result,
    evaluate_predictions,
    extract_json_candidate,
)
from finetune_lab.schemas import SFTRecord


def _record() -> SFTRecord:
    payload = {
        "intent": "search_tasks",
        "target": "tasks",
        "filters": {"status": "not_done", "due": "overdue"},
        "sort": ["due_date_asc"],
        "limit": 20,
    }
    return SFTRecord.model_validate(
        {
            "messages": [
                {"role": "system", "content": "JSONのみ"},
                {"role": "user", "content": "期限切れの未完了タスクを出して"},
                {"role": "assistant", "content": json.dumps(payload, ensure_ascii=False)},
            ]
        }
    )


def test_extract_json_candidate_strips_markdown_fence() -> None:
    raw = """```json
{"intent":"search_tasks"}
```"""

    assert extract_json_candidate(raw) == '{"intent":"search_tasks"}'


def test_evaluate_predictions_counts_exact_match() -> None:
    record = _record()
    result = build_prediction_result(
        index=0,
        record=record,
        raw_output=record.messages[-1].content,
    )

    summary = evaluate_predictions([result])

    assert summary.total == 1
    assert summary.json_parse_rate == 1.0
    assert summary.schema_valid_rate == 1.0
    assert summary.intent_accuracy == 1.0
    assert summary.exact_match_rate == 1.0


def test_evaluate_predictions_keeps_invalid_output_in_denominator() -> None:
    record = _record()
    result = build_prediction_result(index=0, record=record, raw_output="JSONではありません")

    summary = evaluate_predictions([result])

    assert summary.total == 1
    assert summary.json_parse_rate == 0.0
    assert summary.schema_valid_rate == 0.0
    assert summary.intent_accuracy == 0.0
