from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from finetune_lab.evaluator import (  # noqa: E402
    build_prediction_result,
    evaluate_predictions,
    load_sft_records,
    write_prediction_results,
)
from finetune_lab.prompts import PromptMode, build_prompt_messages  # noqa: E402
from finetune_lab.reporting import write_evaluation_report, write_summary_json  # noqa: E402
from finetune_lab.schemas import SFTRecord  # noqa: E402
from finetune_lab.training_config import QLoRASettings, load_qlora_settings  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate a trained QLoRA adapter.")
    parser.add_argument("--config", type=Path, default=ROOT / "configs" / "qlora_qwen.yaml")
    parser.add_argument("--dataset", type=Path, default=ROOT / "data" / "generated" / "test.jsonl")
    parser.add_argument("--adapter-path", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=ROOT / "outputs" / "adapter_eval.jsonl")
    parser.add_argument("--report", type=Path, default=ROOT / "reports" / "adapter_eval_report.md")
    parser.add_argument("--summary-output", type=Path, default=None)
    parser.add_argument("--prompt-mode", choices=["base", "prompt-only"], default="prompt-only")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--max-new-tokens", type=int, default=256)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    settings = load_qlora_settings(args.config)
    prompt_mode = cast(PromptMode, args.prompt_mode)
    adapter_path = args.adapter_path or _resolve_path(settings.training.adapter_output_dir)
    records = load_sft_records(args.dataset, limit=args.limit)

    if args.dry_run:
        print(f"model: {settings.model.model_name_or_path}")
        print(f"adapter_path: {adapter_path}")
        print(f"records: {len(records)}")
        print(f"prompt_mode: {prompt_mode}")
        return 0

    _evaluate_adapter(
        settings=settings,
        records=records,
        adapter_path=adapter_path,
        prompt_mode=prompt_mode,
        dataset_path=args.dataset,
        output_path=args.output,
        report_path=args.report,
        summary_path=args.summary_output or args.output.with_suffix(".summary.json"),
        max_new_tokens=args.max_new_tokens,
    )
    return 0


def _evaluate_adapter(
    *,
    settings: QLoRASettings,
    records: list[SFTRecord],
    adapter_path: Path,
    prompt_mode: PromptMode,
    dataset_path: Path,
    output_path: Path,
    report_path: Path,
    summary_path: Path,
    max_new_tokens: int,
) -> None:
    if not records:
        raise RuntimeError("No evaluation records found.")
    if not adapter_path.exists():
        raise RuntimeError(f"Adapter path does not exist: {adapter_path}")

    try:
        import torch
        from peft import PeftModel  # type: ignore[import-not-found]
        from transformers import (  # type: ignore[import-not-found]
            AutoModelForCausalLM,
            AutoTokenizer,
            BitsAndBytesConfig,
        )
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Adapter evaluation dependencies are missing. Install them with: "
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
    model = PeftModel.from_pretrained(model, adapter_path)
    tokenizer = AutoTokenizer.from_pretrained(
        settings.model.model_name_or_path,
        trust_remote_code=settings.model.trust_remote_code,
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    results = []
    for index, record in enumerate(records):
        messages = build_prompt_messages(record, prompt_mode)
        prompt = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        generated_ids = model.generate(**inputs, max_new_tokens=max_new_tokens)
        output_ids = generated_ids[0][len(inputs.input_ids[0]) :]
        raw_output = tokenizer.decode(output_ids, skip_special_tokens=True)
        results.append(build_prediction_result(index=index, record=record, raw_output=raw_output))

    summary = evaluate_predictions(results)
    write_prediction_results(results, output_path)
    failures = [
        result for result in results if result.parsed is None or result.parsed != result.gold
    ]
    metadata = {
        "model": settings.model.model_name_or_path,
        "adapter_path": str(adapter_path),
        "dataset": str(dataset_path),
        "prompt_mode": prompt_mode,
    }
    write_evaluation_report(
        path=report_path,
        title=f"QLoRA Adapter Evaluation ({prompt_mode})",
        summary=summary,
        metadata=metadata,
        failures=failures,
    )
    write_summary_json(
        path=summary_path,
        name="qlora-adapter",
        summary=summary,
        metadata=metadata,
    )


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
