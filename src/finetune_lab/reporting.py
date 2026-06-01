from __future__ import annotations

from pathlib import Path

from finetune_lab.evaluator import EvaluationSummary, PredictionResult


def format_evaluation_report(
    *,
    title: str,
    summary: EvaluationSummary,
    metadata: dict[str, str],
    failures: list[PredictionResult],
) -> str:
    lines = [f"# {title}", ""]
    if metadata:
        lines.append("## Metadata")
        lines.append("")
        for key, metadata_value in metadata.items():
            lines.append(f"- {key}: `{metadata_value}`")
        lines.append("")

    lines.extend(
        [
            "## Metrics",
            "",
            "| metric | value |",
            "| --- | ---: |",
        ]
    )
    for key, value in summary.as_dict().items():
        if isinstance(value, float):
            lines.append(f"| {key} | {value:.4f} |")
        else:
            lines.append(f"| {key} | {value} |")

    lines.extend(["", "## Failure Examples", ""])
    if not failures:
        lines.append("No failures in the evaluated sample.")
    else:
        for failure in failures[:5]:
            lines.append(f"### Example {failure.index}")
            lines.append("")
            lines.append(f"- user: {failure.user}")
            lines.append(f"- error: {failure.error or 'schema mismatch'}")
            lines.append("")
            lines.append("```text")
            lines.append(failure.raw_output)
            lines.append("```")
            lines.append("")
    lines.append("")
    return "\n".join(lines)


def write_evaluation_report(
    *,
    path: Path,
    title: str,
    summary: EvaluationSummary,
    metadata: dict[str, str],
    failures: list[PredictionResult],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        format_evaluation_report(
            title=title,
            summary=summary,
            metadata=metadata,
            failures=failures,
        ),
        encoding="utf-8",
    )
