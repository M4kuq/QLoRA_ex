from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from finetune_lab.evaluator import load_sft_records  # noqa: E402
from finetune_lab.training_config import QLoRASettings, load_qlora_settings  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Train a QLoRA adapter with TRL SFTTrainer.")
    parser.add_argument("--config", type=Path, default=ROOT / "configs" / "qlora_qwen.yaml")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    settings = load_qlora_settings(args.config)
    train_path = _resolve_path(settings.dataset.train_path)
    valid_path = _resolve_path(settings.dataset.valid_path)
    train_records = load_sft_records(train_path)
    valid_records = load_sft_records(valid_path)

    if args.dry_run:
        print(f"model: {settings.model.model_name_or_path}")
        print(f"train records: {len(train_records)}")
        print(f"valid records: {len(valid_records)}")
        print(f"max_steps: {settings.training.max_steps}")
        print(f"output_dir: {_resolve_path(settings.training.output_dir)}")
        print(f"adapter_output_dir: {_resolve_path(settings.training.adapter_output_dir)}")
        return 0

    _train(settings)
    return 0


def _train(settings: QLoRASettings) -> None:
    try:
        import torch  # type: ignore[import-not-found]
        from datasets import load_dataset  # type: ignore[import-not-found,import-untyped]
        from peft import LoraConfig  # type: ignore[import-not-found]
        from transformers import (  # type: ignore[import-not-found]
            AutoModelForCausalLM,
            AutoTokenizer,
            BitsAndBytesConfig,
        )
        from trl import SFTConfig, SFTTrainer  # type: ignore[import-not-found]
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Training dependencies are missing. Install them with: "
            "python -m pip install -e \".[train]\""
        ) from exc

    torch_dtype = _torch_dtype(torch, settings.model.torch_dtype)
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=settings.quantization.load_in_4bit,
        bnb_4bit_quant_type=settings.quantization.bnb_4bit_quant_type,
        bnb_4bit_use_double_quant=settings.quantization.bnb_4bit_use_double_quant,
        bnb_4bit_compute_dtype=_torch_dtype(
            torch,
            settings.quantization.bnb_4bit_compute_dtype,
        ),
    )
    model = AutoModelForCausalLM.from_pretrained(
        settings.model.model_name_or_path,
        quantization_config=bnb_config,
        device_map=settings.model.device_map,
        trust_remote_code=settings.model.trust_remote_code,
        dtype=torch_dtype,
    )
    tokenizer = AutoTokenizer.from_pretrained(
        settings.model.model_name_or_path,
        trust_remote_code=settings.model.trust_remote_code,
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    peft_config = LoraConfig(
        r=settings.lora.r,
        lora_alpha=settings.lora.lora_alpha,
        lora_dropout=settings.lora.lora_dropout,
        target_modules=settings.lora.target_modules,
        bias=settings.lora.bias,
        task_type=settings.lora.task_type,
    )
    data_files = {
        "train": str(_resolve_path(settings.dataset.train_path)),
        "validation": str(_resolve_path(settings.dataset.valid_path)),
    }
    dataset = load_dataset("json", data_files=data_files)
    sft_config = SFTConfig(
        output_dir=str(_resolve_path(settings.training.output_dir)),
        max_steps=settings.training.max_steps,
        num_train_epochs=settings.training.num_train_epochs,
        per_device_train_batch_size=settings.training.per_device_train_batch_size,
        gradient_accumulation_steps=settings.training.gradient_accumulation_steps,
        learning_rate=settings.training.learning_rate,
        warmup_ratio=settings.training.warmup_ratio,
        logging_steps=settings.training.logging_steps,
        save_steps=settings.training.save_steps,
        eval_steps=settings.training.eval_steps,
        optim=settings.training.optim,
        report_to=settings.training.report_to,
        gradient_checkpointing=settings.training.gradient_checkpointing,
        max_length=settings.dataset.max_length,
    )
    trainer = SFTTrainer(
        model=model,
        args=sft_config,
        train_dataset=dataset["train"],
        eval_dataset=dataset["validation"],
        peft_config=peft_config,
        processing_class=tokenizer,
    )
    trainer.train()
    trainer.save_model(str(_resolve_path(settings.training.adapter_output_dir)))


def _resolve_path(path: Path) -> Path:
    if path.is_absolute():
        return path
    return ROOT / path


def _torch_dtype(torch_module: Any, name: str) -> Any:
    return {
        "bfloat16": torch_module.bfloat16,
        "float16": torch_module.float16,
        "float32": torch_module.float32,
    }[name]


if __name__ == "__main__":
    raise SystemExit(main())
