import pytest

from finetune_lab.training_data import to_prompt_completion


def test_to_prompt_completion_splits_last_assistant_message() -> None:
    example = {
        "messages": [
            {"role": "system", "content": "system"},
            {"role": "user", "content": "user"},
            {"role": "assistant", "content": '{"intent":"search_tasks"}'},
        ]
    }

    converted = to_prompt_completion(example)

    assert converted == {
        "prompt": [
            {"role": "system", "content": "system"},
            {"role": "user", "content": "user"},
        ],
        "completion": [{"role": "assistant", "content": '{"intent":"search_tasks"}'}],
    }


def test_to_prompt_completion_rejects_non_assistant_last_message() -> None:
    with pytest.raises(ValueError, match="last message must be an assistant message"):
        to_prompt_completion(
            {
                "messages": [
                    {"role": "system", "content": "system"},
                    {"role": "user", "content": "user"},
                ]
            }
        )
