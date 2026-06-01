# Experiment Log

## 2026-06-01: LM Studio baseline and QLoRA checkpoint evaluation

### Environment

- OS: WSL Ubuntu 24.04
- GPU: NVIDIA GeForce RTX 4070 12GB
- Python: 3.12.3
- PyTorch: 2.12.0+cu130
- bitsandbytes: 0.49.2
- Base LM Studio model ID: `qwen3.5-4b`
- QLoRA base model: `Qwen/Qwen3.5-4B`

### Baseline Evaluation

LM Studio was served from Windows and accessed from WSL through:

```text
http://172.30.176.1:1234/v1
```

Evaluation used the first 20 examples from `data/generated/test.jsonl`.

| run | json_parse_rate | schema_valid_rate | exact_match_rate |
| --- | ---: | ---: | ---: |
| LM Studio base | 0.0000 | 0.0000 | 0.0000 |
| LM Studio prompt-only | 0.3500 | 0.2000 | 0.1000 |
| QLoRA adapter checkpoint-100 | 1.0000 | 0.9500 | 0.3000 |

Full comparison:

- `reports/baseline_comparison.md`
- `reports/lmstudio_base_eval.md`
- `reports/lmstudio_prompt_only_eval.md`
- `reports/adapter_checkpoint100_eval.md`

### Training Notes

QLoRA training was started with:

```text
python scripts/train_qlora.py --config configs/qlora_qwen.yaml
```

The long-running command timed out at the shell wrapper level after 30 minutes, but the training
process continued and produced `outputs/qwen35-4b-qlora/checkpoint-100`.

Checkpoint-100 was copied to the ignored adapter path:

```text
adapters/qwen35-4b-json-plan
```

The adapter and checkpoint files are intentionally not tracked by Git.

### Observations

- The base LM Studio prompt rarely emitted parseable JSON.
- Prompt-only improved the JSON format but still often emitted reasoning before JSON.
- The QLoRA checkpoint strongly improved parseability and schema validity on the 20-example sample.
- Exact match remains limited, mostly because some filter values and `limit` fields are still wrong.

### Next Steps

- Evaluate the adapter on the full 200-example test split.
- Improve training so only assistant completion tokens contribute to the loss.
- Add stricter generation settings or stop sequences to reduce repeated chat fragments.
