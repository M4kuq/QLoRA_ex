from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from finetune_lab.comparison import load_evaluation_summary, write_comparison_report  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare evaluation summary JSON files.")
    parser.add_argument("summaries", type=Path, nargs="+")
    parser.add_argument("--output", type=Path, default=ROOT / "reports" / "eval_comparison.md")
    args = parser.parse_args()

    runs = [load_evaluation_summary(path) for path in args.summaries]
    write_comparison_report(runs, args.output)
    print(f"comparison: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
