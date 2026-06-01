from pathlib import Path

from finetune_lab.training_config import load_qlora_settings


def test_load_qlora_settings_from_yaml() -> None:
    config_path = Path("configs/qlora_qwen.yaml")

    settings = load_qlora_settings(config_path)

    assert settings.model.model_name_or_path == "Qwen/Qwen3.5-4B"
    assert settings.lora.r == 16
    assert settings.training.loss_mode == "full_sequence"
    assert settings.training.max_steps == 100
    assert settings.quantization.load_in_4bit is True
    assert settings.dataset.train_path == Path("data/generated/train.jsonl")


def test_load_completion_only_qlora_settings() -> None:
    config_path = Path("configs/qlora_qwen_completion_only.yaml")

    settings = load_qlora_settings(config_path)

    assert settings.training.loss_mode == "completion_only"
    assert settings.training.output_dir == Path("outputs/qwen35-4b-qlora-completion-only")
    assert settings.training.adapter_output_dir == Path(
        "adapters/qwen35-4b-json-plan-completion-only"
    )


def test_load_assistant_only_qlora_settings() -> None:
    config_path = Path("configs/qlora_qwen_assistant_only.yaml")

    settings = load_qlora_settings(config_path)

    assert settings.training.loss_mode == "assistant_only"
    assert settings.training.output_dir == Path("outputs/qwen35-4b-qlora-assistant-only")
    assert settings.training.adapter_output_dir == Path(
        "adapters/qwen35-4b-json-plan-assistant-only"
    )
