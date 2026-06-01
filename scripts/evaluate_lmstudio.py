from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from finetune_lab.evaluator import (  # noqa: E402
    build_prediction_result,
    evaluate_predictions,
    load_sft_records,
    write_prediction_results,
)
from finetune_lab.lmstudio_client import LMStudioClient, LMStudioConfig  # noqa: E402
from finetune_lab.schemas import SFTRecord  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate LM Studio model outputs on SFT data.")
    parser.add_argument("--dataset", type=Path, default=ROOT / "data" / "generated" / "test.jsonl")
    parser.add_argument("--output", type=Path, default=ROOT / "outputs" / "lmstudio_base.jsonl")
    parser.add_argument("--base-url", default="http://localhost:1234/v1")
    parser.add_argument("--model", default="qwen3.5:4b")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-tokens", type=int, default=256)
    parser.add_argument("--timeout-seconds", type=float, default=60.0)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    records = load_sft_records(args.dataset, limit=args.limit)
    if args.dry_run:
        _print_dry_run(records)
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
            _base_messages(record),
            temperature=args.temperature,
            max_tokens=args.max_tokens,
        )
        results.append(build_prediction_result(index=index, record=record, raw_output=raw_output))
        print(f"[{index + 1}/{len(records)}] {record.user_content}")

    summary = evaluate_predictions(results)
    write_prediction_results(results, args.output)
    print(summary.as_dict())
    print(f"predictions: {args.output}")
    return 0


def _base_messages(record: SFTRecord) -> list[dict[str, str]]:
    return [{"role": "user", "content": record.user_content}]


def _print_dry_run(records: list[SFTRecord]) -> None:
    if not records:
        print("No records found.")
        return
    print("Dry run prompt:")
    for message in _base_messages(records[0]):
        print(f"{message['role']}: {message['content']}")


if __name__ == "__main__":
    raise SystemExit(main())
