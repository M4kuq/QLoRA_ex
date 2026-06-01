from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from finetune_lab.schemas import OperationPlan, SFTRecord, parse_operation_json


@dataclass(frozen=True)
class PredictionResult:
    index: int
    user: str
    gold: OperationPlan
    raw_output: str
    parsed: OperationPlan | None
    error: str | None = None

    @property
    def schema_valid(self) -> bool:
        return self.parsed is not None


@dataclass(frozen=True)
class EvaluationSummary:
    total: int
    json_parse_rate: float
    schema_valid_rate: float
    intent_accuracy: float
    target_accuracy: float
    filter_exact_match_rate: float
    filter_key_precision: float
    filter_key_recall: float
    sort_accuracy: float
    limit_accuracy: float
    exact_match_rate: float

    def as_dict(self) -> dict[str, float | int]:
        return {
            "total": self.total,
            "json_parse_rate": self.json_parse_rate,
            "schema_valid_rate": self.schema_valid_rate,
            "intent_accuracy": self.intent_accuracy,
            "target_accuracy": self.target_accuracy,
            "filter_exact_match_rate": self.filter_exact_match_rate,
            "filter_key_precision": self.filter_key_precision,
            "filter_key_recall": self.filter_key_recall,
            "sort_accuracy": self.sort_accuracy,
            "limit_accuracy": self.limit_accuracy,
            "exact_match_rate": self.exact_match_rate,
        }


def load_sft_records(path: Path, *, limit: int | None = None) -> list[SFTRecord]:
    records: list[SFTRecord] = []
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            stripped = line.strip()
            if not stripped:
                continue
            records.append(SFTRecord.model_validate_json(stripped))
            if limit is not None and len(records) >= limit:
                break
    return records


def extract_json_candidate(raw_output: str) -> str:
    candidates = extract_json_candidates(raw_output)
    if candidates:
        return candidates[0]

    stripped = raw_output.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()

    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1 or end < start:
        return stripped
    return stripped[start : end + 1]


def extract_json_candidates(raw_output: str) -> list[str]:
    stripped = raw_output.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()

    decoder = json.JSONDecoder()
    candidates: list[str] = []
    for start, char in enumerate(stripped):
        if char != "{":
            continue
        try:
            _, end = decoder.raw_decode(stripped[start:])
        except json.JSONDecodeError:
            continue
        candidates.append(stripped[start : start + end])
    return candidates


def build_prediction_result(
    *,
    index: int,
    record: SFTRecord,
    raw_output: str,
) -> PredictionResult:
    parsed: OperationPlan | None = None
    error: str | None = None
    candidates = extract_json_candidates(raw_output) or [extract_json_candidate(raw_output)]
    for candidate in candidates:
        try:
            parsed = parse_operation_json(candidate)
            error = None
            break
        except ValueError as exc:
            error = str(exc)

    return PredictionResult(
        index=index,
        user=record.user_content,
        gold=record.assistant_plan,
        raw_output=raw_output,
        parsed=parsed,
        error=error,
    )


def evaluate_predictions(results: list[PredictionResult]) -> EvaluationSummary:
    total = len(results)
    if total == 0:
        return EvaluationSummary(
            total=0,
            json_parse_rate=0.0,
            schema_valid_rate=0.0,
            intent_accuracy=0.0,
            target_accuracy=0.0,
            filter_exact_match_rate=0.0,
            filter_key_precision=0.0,
            filter_key_recall=0.0,
            sort_accuracy=0.0,
            limit_accuracy=0.0,
            exact_match_rate=0.0,
        )

    json_parse_count = 0
    schema_valid_count = 0
    intent_correct = 0
    target_correct = 0
    filter_exact = 0
    filter_precision_total = 0.0
    filter_recall_total = 0.0
    sort_correct = 0
    limit_correct = 0
    exact_match = 0

    for result in results:
        if extract_json_candidates(result.raw_output):
            json_parse_count += 1

        if result.parsed is None:
            continue

        schema_valid_count += 1
        gold = _plan_dict(result.gold)
        predicted = _plan_dict(result.parsed)

        if result.parsed.intent == result.gold.intent:
            intent_correct += 1
        if result.parsed.target == result.gold.target:
            target_correct += 1
        if result.parsed.sort == result.gold.sort:
            sort_correct += 1
        if result.parsed.limit == result.gold.limit:
            limit_correct += 1
        if predicted == gold:
            exact_match += 1

        gold_filters = result.gold.filters.model_dump(exclude_none=True)
        predicted_filters = result.parsed.filters.model_dump(exclude_none=True)
        if predicted_filters == gold_filters:
            filter_exact += 1
        precision, recall = _filter_key_scores(gold_filters, predicted_filters)
        filter_precision_total += precision
        filter_recall_total += recall

    return EvaluationSummary(
        total=total,
        json_parse_rate=json_parse_count / total,
        schema_valid_rate=schema_valid_count / total,
        intent_accuracy=intent_correct / total,
        target_accuracy=target_correct / total,
        filter_exact_match_rate=filter_exact / total,
        filter_key_precision=filter_precision_total / total,
        filter_key_recall=filter_recall_total / total,
        sort_accuracy=sort_correct / total,
        limit_accuracy=limit_correct / total,
        exact_match_rate=exact_match / total,
    )


def result_to_jsonl_row(result: PredictionResult) -> dict[str, Any]:
    return {
        "index": result.index,
        "user": result.user,
        "gold": _plan_dict(result.gold),
        "raw_output": result.raw_output,
        "parsed": _plan_dict(result.parsed) if result.parsed is not None else None,
        "error": result.error,
    }


def write_prediction_results(results: list[PredictionResult], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as file:
        for result in results:
            file.write(json.dumps(result_to_jsonl_row(result), ensure_ascii=False))
            file.write("\n")


def _plan_dict(plan: OperationPlan | None) -> dict[str, Any] | None:
    if plan is None:
        return None
    return plan.model_dump(mode="json", exclude_none=True)


def _filter_key_scores(
    gold_filters: dict[str, Any],
    predicted_filters: dict[str, Any],
) -> tuple[float, float]:
    gold_items = set(gold_filters.items())
    predicted_items = set(predicted_filters.items())
    if not gold_items and not predicted_items:
        return 1.0, 1.0
    true_positive = len(gold_items & predicted_items)
    precision = true_positive / len(predicted_items) if predicted_items else 0.0
    recall = true_positive / len(gold_items) if gold_items else 0.0
    return precision, recall
