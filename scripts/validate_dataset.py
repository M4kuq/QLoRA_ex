from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pydantic import ValidationError  # noqa: E402

from finetune_lab.schemas import SFTRecord  # noqa: E402


def validate_jsonl(path: Path) -> tuple[int, list[str]]:
    errors: list[str] = []
    count = 0
    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            count += 1
            try:
                payload = json.loads(stripped)
                SFTRecord.model_validate(payload)
            except (json.JSONDecodeError, ValidationError, ValueError) as exc:
                errors.append(f"{path}:{line_number}: {exc}")
    return count, errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate generated SFT JSONL data.")
    parser.add_argument(
        "paths",
        type=Path,
        nargs="*",
        default=[
            ROOT / "data" / "generated" / "train.jsonl",
            ROOT / "data" / "generated" / "valid.jsonl",
            ROOT / "data" / "generated" / "test.jsonl",
        ],
    )
    args = parser.parse_args()

    all_errors: list[str] = []
    for path in args.paths:
        if not path.exists():
            all_errors.append(f"{path}: file does not exist")
            continue
        count, errors = validate_jsonl(path)
        all_errors.extend(errors)
        print(f"{path}: {count} records, {len(errors)} errors")

    if all_errors:
        print("\nValidation failed:", file=sys.stderr)
        for error in all_errors[:20]:
            print(error, file=sys.stderr)
        if len(all_errors) > 20:
            print(f"... and {len(all_errors) - 20} more errors", file=sys.stderr)
        return 1

    print("Validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
