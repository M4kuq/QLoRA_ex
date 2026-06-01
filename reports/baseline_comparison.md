# Evaluation Comparison

| metric | lmstudio-base | lmstudio-prompt-only | qlora-adapter-checkpoint-100 | qlora-full-sequence-200 | qlora-completion-only-200 |
| --- | ---: | ---: | ---: | ---: | ---: |
| total | 20 | 20 | 20 | 200 | 200 |
| json_parse_rate | 0.0000 | 0.3500 | 1.0000 | 0.9700 | 0.9550 |
| schema_valid_rate | 0.0000 | 0.2000 | 0.9500 | 0.9450 | 0.7650 |
| intent_accuracy | 0.0000 | 0.2000 | 0.9000 | 0.8600 | 0.7650 |
| target_accuracy | 0.0000 | 0.2000 | 0.9000 | 0.8600 | 0.7650 |
| filter_exact_match_rate | 0.0000 | 0.2000 | 0.5000 | 0.5950 | 0.7100 |
| filter_key_precision | 0.0000 | 0.2000 | 0.9125 | 0.8254 | 0.7429 |
| filter_key_recall | 0.0000 | 0.2000 | 0.8208 | 0.7594 | 0.7396 |
| sort_accuracy | 0.0000 | 0.2000 | 0.8500 | 0.7700 | 0.7350 |
| limit_accuracy | 0.0000 | 0.1000 | 0.6000 | 0.6050 | 0.5950 |
| exact_match_rate | 0.0000 | 0.1000 | 0.3000 | 0.3300 | 0.5300 |
