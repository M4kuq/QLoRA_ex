# LM Studio Evaluation (prompt-only)

## Metadata

- model: `qwen3.5-4b`
- base_url: `http://172.30.176.1:1234/v1`
- dataset: `data/generated/test.jsonl`
- predictions: `outputs/lmstudio_prompt_only.jsonl`
- prompt_mode: `prompt-only`

## Metrics

| metric | value |
| --- | ---: |
| total | 20 |
| json_parse_rate | 0.3500 |
| schema_valid_rate | 0.2000 |
| intent_accuracy | 0.2000 |
| target_accuracy | 0.2000 |
| filter_exact_match_rate | 0.2000 |
| filter_key_precision | 0.2000 |
| filter_key_recall | 0.2000 |
| sort_accuracy | 0.2000 |
| limit_accuracy | 0.1000 |
| exact_match_rate | 0.1000 |

## Failure Examples

### Example 0

- user: まだ着手していない佐藤さんに割り当てられている中優先度の期限切れのタスクを締切が近い順で10件だけリストアップして
- error: assistant content does not match OperationPlan: 2 validation errors for OperationPlan
intent
  Field required [type=missing, input_value={}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.13/v/missing
target
  Field required [type=missing, input_value={}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.13/v/missing

```text
Thinking Process:

1.  **Analyze the Request:**
    *   Input: "まだ着手していない佐藤さんに割り当てられている中優先度の期限切れのタスクを締切が近い順で10件だけリストアップして" (List tasks assigned to Sato that are not yet started, medium priority, overdue, sorted by deadline proximity, 10 items.)
    *   Output Format: JSON only. No markdown, no explanations, no code fences.
    *   Schema:
        ```json
        {
          "intent": "...",
          "target": "...",
          "filters": {},
          "sort": [...],
          "limit": ...
        }
        ```

2.  **Determine Intent and Target:**
    *   The user wants to list tasks ("タスク").
    *   Intent: `search_tasks`
    *   Target: `tasks`

3.  **Determine Filters:**
    *   "佐藤さんに割り当てられている" (Assigned to Sato): `assignee` -> "佐藤"
    *   "まだ着手していない" (Not yet started): Usually implies status like 'pending', 'not
```

### Example 1

- user: アーカイブ済みではない基盤改善関連のドキュメントを作成日時の降順で見せて
- error: assistant content is not valid JSON: Expecting value: line 1 column 1 (char 0)

```text
The user wants to search for documents with specific criteria:
1. Not archived (アーカイブ済みではない) - This likely means status should not be "archived" or similar
2. Related to infrastructure improvement (基盤改善関連) - This is a keyword filter, but looking at the available filters, there's no direct text search field in the provided schema. However, I need to check if there are any relevant filters for content filtering. Looking at the filters list: project, status, assignee, priority, due, created, score_lt. There's no "keyword" or "content" filter explicitly listed.
3. Sort by creation date descending (作成日時の降順) - This maps to `created_at_desc`

Since there's no direct content search capability in the provided filters, I'll need to work with what's available. The user is asking for documents related to infrastructure improvement that are not archived, sorted by creation date descending.

Looking at the intent options:
- search_documents seems most appropriate since they want documents (ドキュメント)

For filters:
- status: could filter out archived ones (but I don't know what values represent "not archived")
- There's no direct content/keyword
```

### Example 2

- user: 高橋さんに割り当てられている終わっていない緊急のタスクを締切が遅い順で10件だけリストアップして
- error: assistant content is not valid JSON: Expecting value: line 1 column 1 (char 0)

```text
Thinking Process:

1.  **Analyze the Request:**
    *   Input: "高橋さんに割り当てられている終わっていない緊急のタスクを締切が遅い順で10件だけリストアップして" (List 10 tasks assigned to Takahashi that are not finished and urgent, sorted by due date descending.)
    *   Output Format: JSON only. No markdown, no explanations, no code fences.
    *   Schema Requirements:
        *   `intent`: Must be one of the provided options (`search_tasks`, etc.). Based on "タスク" (tasks), it should be `search_tasks`.
        *   `target`: Must match `intent`'s target. For tasks, it's `tasks`.
        *   `filters`: Object containing conditions.
            *   Assignee: "高橋さん" -> `assignee` key. Value needs to be the name or ID. Usually, names are used directly in these prompts unless specified otherwise. Let's use `"高橋"` or `"高橋さん"`. Given typical API patterns, often just the name is expected. I'll use `"高橋"` as it's more standard for systems, but "高橋
```

### Example 3

- user: レビュー待機中の期限なしのタスクを重要度が高い順で確認したい
- error: assistant content is not valid JSON: Expecting value: line 1 column 1 (char 0)

```text
Thinking Process:

1.  **Analyze the Request:**
    *   Input: "レビュー待機中の期限なしのタスクを重要度が高い順で確認したい" (I want to check tasks that are waiting for review, have no deadline, and are sorted by priority in descending order.)
    *   Task: Convert this Japanese business instruction into a JSON operation plan.
    *   Output Format: JSON only. No markdown, no explanations, no code fences.

2.  **Determine the Intent:**
    *   The user wants to "check" or "search" for tasks.
    *   Intent candidate: `search_tasks` (matches best).

3.  **Determine the Target:**
    *   The object being searched is "tasks".
    *   Target candidate: `tasks`.

4.  **Analyze Filters:**
    *   Condition 1: "レビュー待機中" (Waiting for review). This likely maps to a status filter. In many task management systems, this might be "review_pending", "waiting_review", or similar. However, looking at the provided `filters` keys (`project`, `status`, `assignee`, `priority`, `
```

### Example 4

- user: アーカイブ済みのドキュメントを作成日時の昇順で見せて
- error: schema mismatch

```text
The user wants to search for archived documents, sorted by creation date in ascending order.

Let me analyze the requirements:
1. Target: documents (since they want documents)
2. Intent: search_documents
3. Filter: status should be "archived" or similar - I need to check what filter key is available. Looking at the filters list, there's no specific "status" for archived mentioned, but typically we'd use a status field. However, looking at the provided filters, I see: project, status, assignee, priority, due, created, score_lt
4. Sort: created_at_asc (ascending order by creation date)

For archived documents, I should filter by status with value "archived" or similar. Let me use "status": "archived".

Let me construct the JSON response without any markdown or explanations as instructed.
</think>

{
  "intent": "search_documents",
  "target": "documents",
  "filters": {
    "status": "archived"
  },
  "sort": ["created_at_asc"],
  "limit": 20
}
```

