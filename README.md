# finetune-lab

日本語の業務指示を、安全に実行可能なJSON操作計画へ変換する小型LLMの
LoRA / QLoRAファインチューニング実験プロジェクトです。

この初期MVPでは、重い学習処理はまだ実行しません。まずは次の土台を作ります。

- 日本語指示と正解JSONを持つSFT向けJSONLデータの生成
- JSON操作計画のPydanticスキーマ検証
- train / valid / test 分割
- pytestによるスキーマとデータ生成処理の確認

## RAGとの違い

既存のRAGは、外部文書を検索し、根拠付きで回答するための仕組みです。
このプロジェクトは知識検索ではなく、自然文の業務指示を構造化された操作計画に
変換することを目的にします。

想定する役割分担は次のとおりです。

- RAG: 文書検索、根拠付きQA、citation、groundedness評価
- finetune-lab: intent分類、filter抽出、sort抽出、JSON schemaに沿った安定出力

## なぜQLoRAを使うのか

4B前後の小型LLMでも、業務指示から安定したJSONを出すには、プロンプトだけでは
出力ゆれや余計な説明文が残りやすくなります。QLoRAではベースモデルを4bit量子化し、
小さなLoRA adapterだけを学習するため、通常のフルファインチューニングより軽く、
ローカルGPUやColabで実験しやすくなります。

## 今回のモデル想定

今回の推論・ベースライン評価では、LM Studioで `Qwen3.5:4b` を使う前提です。
LM StudioはOpenAI互換APIを提供できるため、Phase 2以降では次のように扱う予定です。

- base model評価: LM Studio上の `Qwen3.5:4b`
- prompt-only baseline: 同じモデルにJSON出力用プロンプトを追加
- QLoRA学習: Hugging Face Transformers形式のQwen系4Bモデルを使用

注意点として、OllamaやLM StudioのGGUF形式モデルは、そのままQLoRA学習の入力には
使いません。QLoRA学習ではTransformers形式のモデル重みを使い、学習後のadapterを
評価・変換・配布の方針に応じて扱います。

## JSON操作計画

初期MVPでは、読み取り系の `search_*` 操作だけを対象にします。SQLはモデルに直接
出力させず、モデルは次のようなJSON操作計画のみを返します。

```json
{
  "intent": "search_tasks",
  "target": "tasks",
  "filters": {
    "status": "not_done",
    "due": "overdue",
    "priority": "high"
  },
  "sort": ["due_date_asc"],
  "limit": 20
}
```

このJSONをPydanticで検証し、将来のバックエンドまたは評価スクリプトで安全な
SQLや内部クエリに変換します。

## セットアップ

```powershell
cd C:\Users\kei01\QLoRA_lab\finetune-lab
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -e ".[dev]"
```

## データ生成

デフォルトでは `data/generated` に train / valid / test を生成します。

```powershell
python scripts/generate_dataset.py
```

件数を指定する場合:

```powershell
python scripts/generate_dataset.py --train-size 1000 --valid-size 200 --test-size 200
```

生成されるJSONLは、TRLの `SFTTrainer` で扱いやすい `messages` 形式です。

```json
{"messages":[{"role":"system","content":"..."},{"role":"user","content":"期限切れで未完了の高優先度タスクを出して"},{"role":"assistant","content":"{\"intent\":\"search_tasks\",\"target\":\"tasks\",\"filters\":{\"status\":\"not_done\",\"due\":\"overdue\",\"priority\":\"high\"},\"sort\":[\"due_date_asc\"],\"limit\":20}"}]}
```

## データ検証

```powershell
python scripts/validate_dataset.py
```

個別ファイルを指定する場合:

```powershell
python scripts/validate_dataset.py data/generated/train.jsonl data/generated/valid.jsonl data/generated/test.jsonl
```

## テスト

```powershell
pytest
```

## 評価方法

Phase 2以降では、同じtestデータに対して次の3つを比較します。

1. base model
2. prompt-only baseline
3. QLoRA fine-tuned model

主な評価指標:

- JSON parse rate
- JSON schema valid rate
- intent accuracy
- target accuracy
- filter accuracy
- sort accuracy
- limit accuracy
- exact match rate
- end-to-end execution success rate

## 実験結果の記録場所

- `reports/eval_report.md`: 評価結果の表と失敗例
- `reports/experiment_log.md`: 学習条件、モデル、データ件数、所感

## デモ実行方針

Phase 5では、自然文入力からJSON操作計画を返す `scripts/run_inference.py` を追加する
予定です。LM Studioを使う場合は、OpenAI互換APIのURLとモデルIDを設定して呼び出す
形にします。

## 今後の拡張案

- LM Studio経由のbase / prompt-only評価スクリプト
- QLoRA学習スクリプト
- LoRAとQLoRAの比較
- rank `r` の違いによる性能比較
- 学習データ件数による性能比較
- SQL直接出力版との比較
- JSON操作計画から安全なSQLへ変換する評価
- RAGプロジェクトのUIから操作計画モデルを呼び出す統合
