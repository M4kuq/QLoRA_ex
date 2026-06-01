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

## 2026-06-01: Full 200-example adapter evaluation

The checkpoint-100 adapter was evaluated on the full `data/generated/test.jsonl` split.

| metric | value |
| --- | ---: |
| total | 200 |
| json_parse_rate | 0.9700 |
| schema_valid_rate | 0.9450 |
| intent_accuracy | 0.8600 |
| target_accuracy | 0.8600 |
| filter_exact_match_rate | 0.5950 |
| filter_key_precision | 0.8254 |
| filter_key_recall | 0.7594 |
| sort_accuracy | 0.7700 |
| limit_accuracy | 0.6050 |
| exact_match_rate | 0.3300 |

### Error Pattern Summary

- 11 / 200 outputs could not be parsed into a valid `OperationPlan`.
- 66 / 200 outputs were exact matches.
- Most common target/intent confusion: `search_projects` was predicted as `search_tasks` 7 times.
- Most common sort confusion: `created_at_asc` was predicted as `created_at_desc` 8 times.
- Most common limit error: expected `20`, predicted `10` 36 times.
- Most common missing filters: `due` 27 times, `created` 13 times, `priority` 12 times.

### Interpretation

This is a clear improvement over LM Studio base and prompt-only baselines. The adapter learned
the JSON shape and most task routing behavior, but is not yet production-grade because exact
filter and limit extraction still fail often enough to change query results.

### Recommended Next Improvements

- Train with assistant-only completion loss to avoid learning user/system text continuation.
- Add more contrastive examples for `projects` versus `tasks`.
- Oversample `limit` values and date bucket filters such as `due` and `created`.
- Add targeted evaluation slices for sort direction and limit extraction.

## 2026-06-01: Completion-only loss adapter evaluation

The previous checkpoint-100 adapter was kept as a Git tag and a local adapter backup:

```text
git tag: qlora-checkpoint100-full-seq
local backup: adapters/backups/qwen35-4b-json-plan-checkpoint100-full-seq-20260601
```

A second 100-step QLoRA run was trained with `loss_mode: completion_only`:

```text
python scripts/train_qlora.py --config configs/qlora_qwen_completion_only.yaml
```

The trained adapter was saved to:

```text
adapters/qwen35-4b-json-plan-completion-only
```

It was evaluated on the full `data/generated/test.jsonl` split.

| metric | full-sequence checkpoint-100 | completion-only checkpoint-100 |
| --- | ---: | ---: |
| total | 200 | 200 |
| json_parse_rate | 0.9700 | 0.9550 |
| schema_valid_rate | 0.9450 | 0.7650 |
| intent_accuracy | 0.8600 | 0.7650 |
| target_accuracy | 0.8600 | 0.7650 |
| filter_exact_match_rate | 0.5950 | 0.7100 |
| filter_key_precision | 0.8254 | 0.7429 |
| filter_key_recall | 0.7594 | 0.7396 |
| sort_accuracy | 0.7700 | 0.7350 |
| limit_accuracy | 0.6050 | 0.5950 |
| exact_match_rate | 0.3300 | 0.5300 |

### Interpretation

Completion-only loss improved exact match from 33.0% to 53.0%, mainly because more successful
responses match the full expected JSON exactly. However, schema validity dropped from 94.5% to
76.5% because the model more often generated explanatory text before JSON. During training, TRL
also emitted repeated prompt/completion tokenization mismatch warnings, so this run should be
treated as promising but not clean.

### Next Step

Try `loss_mode: assistant_only` with the original conversational `messages` dataset. That should
avoid the prompt/completion conversion path that produced tokenization mismatch warnings while
still masking user/system tokens out of the loss.
