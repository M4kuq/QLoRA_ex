# Evaluation Report

このファイルは、base model / prompt-only baseline / QLoRA fine-tuned model の
評価結果を記録する場所です。

現時点では、LM Studio上での実推論はまだ実行していません。LM Studioで
`Qwen3.5:4b` をロードしてサーバーを起動した後、次のコマンドで更新できます。

```powershell
python scripts/evaluate_lmstudio.py --model qwen3.5:4b --prompt-mode base --limit 20
python scripts/evaluate_lmstudio.py --model qwen3.5:4b --prompt-mode prompt-only --limit 20
```
