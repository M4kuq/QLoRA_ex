# QLoRA Adapter Evaluation (prompt-only)

## Metadata

- model: `Qwen/Qwen3.5-4B`
- adapter_path: `adapters/qwen35-4b-json-plan-assistant-only`
- dataset: `data/generated/test.jsonl`
- prompt_mode: `prompt-only`

## Metrics

| metric | value |
| --- | ---: |
| total | 200 |
| json_parse_rate | 0.9050 |
| schema_valid_rate | 0.5800 |
| intent_accuracy | 0.5750 |
| target_accuracy | 0.5750 |
| filter_exact_match_rate | 0.5450 |
| filter_key_precision | 0.5708 |
| filter_key_recall | 0.5692 |
| sort_accuracy | 0.5600 |
| limit_accuracy | 0.4600 |
| exact_match_rate | 0.4200 |

## Failure Examples

### Example 0

- user: まだ着手していない佐藤さんに割り当てられている中優先度の期限切れのタスクを締切が近い順で10件だけリストアップして
- error: assistant content is not valid JSON: Expecting value: line 1 column 1 (char 0)

```text
The user wants me to search for tasks with specific criteria and return them in JSON format only.

Criteria:
- Assignee: 佐藤 (Sato)
- Status: not done (まだ着手していない)
- Priority: medium (中優先度)
- Due: due (期限切れ)
- Sort: by due date ascending (締切が近い順)
- Limit: 10

I need to construct a JSON object with the specified intent, target, filters, sort, and limit.

Looking at the filters available:
- project
- status
- assignee
- priority
- due
- created
- score_lt

For "status", I need to represent "not done" - likely "todo" or "not_done"
For "assignee", I need "佐藤"
For "priority", I need "medium" or "中"
For "due", I need to indicate tasks that are due (likely "due" or "overdue")
For "sort", I need ["due_date_asc"]
For "limit", I need 10

Let me construct the JSON:
{"intent":"search_tasks","target":"tasks","filters":{"project":null,"
```

### Example 1

- user: アーカイブ済みではない基盤改善関連のドキュメントを作成日時の降順で見せて
- error: schema mismatch

```text
The user wants to search for documents related to "基盤改善" (circuit board improvement) project, excluding those that are archived, and sort them by creation date descending.

I need to construct a JSON object with the following fields:
- intent: "search_documents"
- target: "documents"
- filters: {"project":"基盤改善","status":"not_archived"}
- sort: ["created_at_desc"]
- limit: 20 (default)

Wait, I need to check the available filters. The user mentioned "アーカイブ済みではない" (not archived). The available filters are: project, status, assignee, priority, due, created, score_lt.

"status" could be used to filter for non-archived documents. I'll use status:"not_archived" or similar.

Let me construct the JSON properly.
</think>

{"intent":"search_documents","target":"documents","filters":{"project":"基盤改善","status":"not_archived"},"sort":["created_at_desc"],"limit":20}

```

### Example 2

- user: 高橋さんに割り当てられている終わっていない緊急のタスクを締切が遅い順で10件だけリストアップして
- error: assistant content is not valid JSON: Expecting value: line 1 column 1 (char 0)

```text
The user wants me to search for tasks with specific criteria:
- Assignee: 高橋 (Takahashi)
- Status: not done (終わっていない)
- Priority: urgent (緊急)
- Sort: by due date ascending (締切が遅い順)
- Limit: 10 tasks

I need to output only JSON in the specified format, without any markdown, code fences, or explanations.

Looking at the filters available:
- project
- status
- assignee
- priority
- due
- created
- score_lt

For "status", I need to use a value that represents "not done". Common values might be "todo", "not_done", "in_progress", etc. Since the user said "終わっていない" (not done), I'll use "todo" or "not_done". Let me use "todo" as it's more common.

For "priority", "緊急" would be "urgent".

For "assignee", "高橋" is the name.

For "sort", "due_date_asc" matches "締切が遅い順" (earlier due dates first).

For "limit", 10.

Let me construct the JSON:

```

### Example 4

- user: アーカイブ済みのドキュメントを作成日時の昇順で見せて
- error: schema mismatch

```text
The user wants to search for documents with the status "archived" and sort them by creation date ascending. I need to convert this into a JSON search_tasks request.

Looking at the intent options, the user is asking for documents, so the intent should be "search_documents" and target should be "documents".

Filters needed:
- status: "archived" (アーカイブ済み)
- created_asc for sorting

Wait, I need to check the sort options available:
- due_date_asc
- due_date_desc
- priority_desc
- priority_asc
- created_at_desc
- created_at_asc
- score_asc
- score_desc

For "created_at_asc" I can use "created_at_asc" for ascending order by creation date.

The user said "アーカイブ済みのドキュメント" which means documents with status "archived".

Let me construct the JSON:
{"intent":"search_documents","target":"documents","filters":{"status":"archived"},"sort":["created_at_asc"],"limit":20}

Wait, I need to check if there's a "created" filter key. Looking at the filters options:
- project
- status
- assignee
- priority
- due
```

### Example 7

- user: 期限切れの終わっていない山本さんに割り当てられている採用サイトのタスクを重要度が高い順でリストアップして
- error: assistant content does not match OperationPlan: 6 validation errors for OperationPlan
intent
  Field required [type=missing, input_value={'project': '採用サイ...'山本', 'due': 'true'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.13/v/missing
target
  Field required [type=missing, input_value={'project': '採用サイ...'山本', 'due': 'true'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.13/v/missing
project
  Extra inputs are not permitted [type=extra_forbidden, input_value='採用サイト', input_type=str]
    For further information visit https://errors.pydantic.dev/2.13/v/extra_forbidden
status
  Extra inputs are not permitted [type=extra_forbidden, input_value='not_done', input_type=str]
    For further information visit https://errors.pydantic.dev/2.13/v/extra_forbidden
assignee
  Extra inputs are not permitted [type=extra_forbidden, input_value='山本', input_type=str]
    For further information visit https://errors.pydantic.dev/2.13/v/extra_forbidden
due
  Extra inputs are not permitted [type=extra_forbidden, input_value='true', input_type=str]
    For further information visit https://errors.pydantic.dev/2.13/v/extra_forbidden

```text
The user wants me to search for tasks with specific criteria:
- Project: 採用サイト (Adoption Site)
- Status: not done (終わっていない)
- Assignee: 山本 (Yamamoto)
- Priority: due (期限切れ)
- Sort: priority_desc (重要度が高い順)
- Target: tasks

I need to output only JSON without any markdown, explanations, or code fences.

Let me construct the JSON based on the user's request:
- intent: "search_tasks"
- target: "tasks"
- filters: {"project":"採用サイト","status":"not_done","assignee":"山本","due":"true"}
- sort: ["priority_desc"]
- limit: 20 (default)

Wait, I need to check the available filter keys: project, status, assignee, priority, due, created, score_lt

For "due" (期限切れ), I should use "due":"true" or similar.
For "status" (終わっていない), I should use "status":"not_done" or "status":"todo".
For "priority_desc" (重要度が高い順), I need to use the sort option "priority_desc".


```

