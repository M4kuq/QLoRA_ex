from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class EvaluationRun:
    name: str
    metrics: dict[str, float | int]
    metadata: dict[str, str]


def load_evaluation_summary(path: Path) -> EvaluationRun:
    payload: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    name = str(payload["name"])
    metrics = {
        key: value
        for key, value in payload["metrics"].items()
        if isinstance(value, int | float)
    }
    metadata = {str(key): str(value) for key, value in payload.get("metadata", {}).items()}
    return EvaluationRun(name=name, metrics=metrics, metadata=metadata)


def format_comparison_report(runs: list[EvaluationRun]) -> str:
    if not runs:
        raise ValueError("at least one evaluation summary is required")

    metric_names = [
        "total",
        "json_parse_rate",
        "schema_valid_rate",
        "intent_accuracy",
        "target_accuracy",
        "filter_exact_match_rate",
        "filter_key_precision",
        "filter_key_recall",
        "sort_accuracy",
        "limit_accuracy",
        "exact_match_rate",
    ]
    lines = [
        "# Evaluation Comparison",
        "",
        "| metric | " + " | ".join(run.name for run in runs) + " |",
        "| --- | " + " | ".join("---:" for _ in runs) + " |",
    ]
    for metric_name in metric_names:
        values = [_format_metric(run.metrics.get(metric_name, 0.0)) for run in runs]
        lines.append(f"| {metric_name} | " + " | ".join(values) + " |")
    lines.append("")
    return "\n".join(lines)


def write_comparison_report(runs: list[EvaluationRun], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(format_comparison_report(runs), encoding="utf-8")


def _format_metric(value: float | int) -> str:
    if isinstance(value, int):
        return str(value)
    return f"{value:.4f}"
