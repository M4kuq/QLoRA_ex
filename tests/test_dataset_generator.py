import json

from finetune_lab.dataset_generator import (
    DatasetSizes,
    create_dataset,
    generate_records,
    write_jsonl,
)
from finetune_lab.schemas import SFTRecord


def test_generate_records_returns_valid_sft_records() -> None:
    records = generate_records(25, split="train", seed=123)

    assert len(records) == 25
    for record in records:
        parsed = SFTRecord.model_validate(record)
        assert parsed.messages[0].role == "system"
        assert parsed.messages[1].role == "user"
        assert parsed.messages[2].role == "assistant"


def test_create_dataset_splits_requested_sizes() -> None:
    dataset = create_dataset(DatasetSizes(train=12, valid=5, test=7), seed=99)

    assert {split: len(records) for split, records in dataset.items()} == {
        "train": 12,
        "valid": 5,
        "test": 7,
    }


def test_generated_user_instructions_are_unique_within_split() -> None:
    records = generate_records(50, split="test", seed=456)
    users = [record["messages"][1]["content"] for record in records]

    assert len(users) == len(set(users))


def test_write_jsonl_round_trips_records(tmp_path) -> None:
    records = generate_records(3, split="valid", seed=789)
    path = tmp_path / "sample.jsonl"

    write_jsonl(records, path)

    loaded = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert loaded == records
    for record in loaded:
        SFTRecord.model_validate(record)
