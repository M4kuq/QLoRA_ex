import json

from finetune_lab.comparison import format_comparison_report, load_evaluation_summary


def test_load_evaluation_summary_and_format_report(tmp_path) -> None:
    path = tmp_path / "base.summary.json"
    path.write_text(
        json.dumps(
            {
                "name": "base",
                "metadata": {"model": "qwen"},
                "metrics": {
                    "total": 10,
                    "json_parse_rate": 0.5,
                    "schema_valid_rate": 0.4,
                    "intent_accuracy": 0.3,
                },
            }
        ),
        encoding="utf-8",
    )

    run = load_evaluation_summary(path)
    report = format_comparison_report([run])

    assert run.name == "base"
    assert "| json_parse_rate | 0.5000 |" in report
    assert "| total | 10 |" in report
