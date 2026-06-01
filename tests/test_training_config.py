from pathlib import Path

from finetune_lab.training_config import load_qlora_settings


def test_load_qlora_settings_from_yaml() -> None:
    config_path = Path("configs/qlora_qwen.yaml")

    settings = load_qlora_settings(config_path)

    assert settings.model.model_name_or_path == "Qwen/Qwen3.5-4B"
    assert settings.lora.r == 16
    assert settings.quantization.load_in_4bit is True
    assert settings.dataset.train_path == Path("data/generated/train.jsonl")
