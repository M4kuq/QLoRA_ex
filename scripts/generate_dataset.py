from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from finetune_lab.dataset_generator import DatasetSizes, create_dataset, write_dataset  # noqa: E402
from finetune_lab.schemas import OperationPlan  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate synthetic SFT JSONL data.")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "data" / "generated")
    parser.add_argument(
        "--schema-path",
        type=Path,
        default=ROOT / "data" / "schema" / "operation_schema.json",
    )
    parser.add_argument("--train-size", type=int, default=1000)
    parser.add_argument("--valid-size", type=int, default=200)
    parser.add_argument("--test-size", type=int, default=200)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    sizes = DatasetSizes(train=args.train_size, valid=args.valid_size, test=args.test_size)
    dataset = create_dataset(sizes, seed=args.seed)
    write_dataset(dataset, args.output_dir)

    args.schema_path.parent.mkdir(parents=True, exist_ok=True)
    args.schema_path.write_text(
        json.dumps(OperationPlan.model_json_schema(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    for split, records in dataset.items():
        print(f"{split}: {len(records)} records -> {args.output_dir / f'{split}.jsonl'}")
    print(f"schema: {args.schema_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
