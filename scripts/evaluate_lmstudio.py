from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import cast

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from finetune_lab.evaluator import (  # noqa: E402
    build_prediction_result,
    evaluate_predictions,
    load_sft_records,
    write_prediction_results,
)
from finetune_lab.lmstudio_client import LMStudioClient, LMStudioConfig  # noqa: E402
from finetune_lab.prompts import PromptMode, build_prompt_messages  # noqa: E402
from finetune_lab.reporting import write_evaluation_report, write_summary_json  # noqa: E402
from finetune_lab.schemas import SFTRecord  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate LM Studio model outputs on SFT data.")
    parser.add_argument("--dataset", type=Path, default=ROOT / "data" / "generated" / "test.jsonl")
    parser.add_argument("--output", type=Path, default=ROOT / "outputs" / "lmstudio_base.jsonl")
    parser.add_argument("--report", type=Path, default=ROOT / "reports" / "eval_report.md")
    parser.add_argument("--summary-output", type=Path, default=None)
    parser.add_argument("--base-url", default="http://localhost:1234/v1")
    parser.add_argument("--model", default="qwen3.5:4b")
    parser.add_argument("--prompt-mode", choices=["base", "prompt-only"], default="base")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-tokens", type=int, default=256)
    parser.add_argument("--timeout-seconds", type=float, default=60.0)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    prompt_mode = cast(PromptMode, args.prompt_mode)
    records = load_sft_records(args.dataset, limit=args.limit)
    if args.dry_run:
        _print_dry_run(records, prompt_mode)
        return 0

    config = LMStudioConfig(
        base_url=args.base_url,
        model=args.model,
        timeout_seconds=args.timeout_seconds,
    )
    client = LMStudioClient(config)
    results = []
    for index, record in enumerate(records):
        raw_output = client.chat_completion(
            build_prompt_messages(record, prompt_mode),
            temperature=args.temperature,
            max_tokens=args.max_tokens,
        )
        results.append(build_prediction_result(index=index, record=record, raw_output=raw_output))
        print(f"[{index + 1}/{len(records)}] {record.user_content}")

    summary = evaluate_predictions(results)
    write_prediction_results(results, args.output)
    summary_output = args.summary_output or args.output.with_suffix(".summary.json")
    failures = [
        result for result in results if result.parsed is None or result.parsed != result.gold
    ]
    metadata = {
        "model": args.model,
        "base_url": args.base_url,
        "dataset": str(args.dataset),
        "predictions": str(args.output),
        "prompt_mode": prompt_mode,
    }
    write_evaluation_report(
        path=args.report,
        title=f"LM Studio Evaluation ({prompt_mode})",
        summary=summary,
        metadata=metadata,
        failures=failures,
    )
    write_summary_json(
        path=summary_output,
        name=f"lmstudio-{prompt_mode}",
        summary=summary,
        metadata=metadata,
    )
    print(summary.as_dict())
    print(f"predictions: {args.output}")
    print(f"summary: {summary_output}")
    print(f"report: {args.report}")
    return 0


def _print_dry_run(records: list[SFTRecord], prompt_mode: PromptMode) -> None:
    if not records:
        print("No records found.")
        return
    print("Dry run prompt:")
    for message in build_prompt_messages(records[0], prompt_mode):
        print(f"{message['role']}: {message['content']}")


if __name__ == "__main__":
    raise SystemExit(main())
