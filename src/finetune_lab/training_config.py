from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ModelSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model_name_or_path: str
    trust_remote_code: bool = True
    torch_dtype: Literal["bfloat16", "float16", "float32"] = "bfloat16"
    device_map: str = "auto"


class DatasetSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    train_path: Path = Path("data/generated/train.jsonl")
    valid_path: Path = Path("data/generated/valid.jsonl")
    max_length: int = Field(default=1024, ge=128, le=8192)


class LoRASettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    r: int = Field(default=16, ge=1)
    lora_alpha: int = Field(default=32, ge=1)
    lora_dropout: float = Field(default=0.05, ge=0.0, le=1.0)
    target_modules: str | list[str] = "all-linear"
    bias: Literal["none", "all", "lora_only"] = "none"
    task_type: str = "CAUSAL_LM"


class QuantizationSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    load_in_4bit: bool = True
    bnb_4bit_quant_type: Literal["nf4", "fp4"] = "nf4"
    bnb_4bit_use_double_quant: bool = True
    bnb_4bit_compute_dtype: Literal["bfloat16", "float16", "float32"] = "bfloat16"


class TrainingSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    output_dir: Path = Path("outputs/qwen35-4b-qlora")
    adapter_output_dir: Path = Path("adapters/qwen35-4b-json-plan")
    max_steps: int = Field(default=-1, ge=-1)
    num_train_epochs: float = Field(default=2, gt=0)
    per_device_train_batch_size: int = Field(default=1, ge=1)
    gradient_accumulation_steps: int = Field(default=8, ge=1)
    learning_rate: float = Field(default=2e-4, gt=0)
    warmup_ratio: float = Field(default=0.03, ge=0, le=1)
    logging_steps: int = Field(default=10, ge=1)
    save_steps: int = Field(default=100, ge=1)
    eval_steps: int = Field(default=100, ge=1)
    optim: str = "paged_adamw_8bit"
    report_to: str = "none"
    gradient_checkpointing: bool = True


class QLoRASettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model: ModelSettings
    dataset: DatasetSettings = Field(default_factory=DatasetSettings)
    lora: LoRASettings = Field(default_factory=LoRASettings)
    quantization: QuantizationSettings = Field(default_factory=QuantizationSettings)
    training: TrainingSettings = Field(default_factory=TrainingSettings)


def load_qlora_settings(path: Path) -> QLoRASettings:
    try:
        import yaml  # type: ignore[import-untyped]
    except ModuleNotFoundError as exc:
        raise RuntimeError("PyYAML is required to read QLoRA YAML configs.") from exc

    payload: Any = yaml.safe_load(path.read_text(encoding="utf-8"))
    return QLoRASettings.model_validate(payload)
