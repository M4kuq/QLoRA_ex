# QLoRA Adapter Evaluation (prompt-only)

## Metadata

- model: `Qwen/Qwen3.5-4B`
- adapter_path: `adapters/qwen35-4b-json-plan-completion-only`
- dataset: `data/generated/test.jsonl`
- prompt_mode: `prompt-only`

## Metrics

| metric | value |
| --- | ---: |
| total | 200 |
| json_parse_rate | 0.9550 |
| schema_valid_rate | 0.7650 |
| intent_accuracy | 0.7650 |
| target_accuracy | 0.7650 |
| filter_exact_match_rate | 0.7100 |
| filter_key_precision | 0.7429 |
| filter_key_recall | 0.7396 |
| sort_accuracy | 0.7350 |
| limit_accuracy | 0.5950 |
| exact_match_rate | 0.5300 |

## Failure Examples

### Example 0

- user: まだ着手していない佐藤さんに割り当てられている中優先度の期限切れのタスクを締切が近い順で10件だけリストアップして
- error: assistant content is not valid JSON: Expecting value: line 1 column 1 (char 0)

```text
The user wants to search for tasks with specific criteria:
- Status: not done (まだ着手していない)
- Assignee: 佐藤
- Priority: medium (中優先度)
- Due: due (期限切れ)
- Sort: by due date ascending (締切が近い順)
- Limit: 10

I need to output only JSON in the specified format without any explanation, markdown, or code fences.

Looking at the filters available:
- project
- status
- assignee
- priority
- due
- created
- score_lt

For "not done", I should use status="not_done" or similar. In Japanese context, "まだ着手していない" means tasks that are not yet done, so status="not_done" or status!="done".

For "medium priority", I need to check if there's a priority value. The available sort includes priority_desc, priority_asc, so there must be priority values. "中優先度" likely means "medium".

For "due", I need to specify due date. "期限切れ" means due date is in the past or due soon. I'll use due="overdue" or due="due".

Let me construct the
```

### Example 1

- user: アーカイブ済みではない基盤改善関連のドキュメントを作成日時の降順で見せて
- error: schema mismatch

```text
The user wants to search for documents related to "基盤改善" (base improvement project) that are not archived, sorted by creation date descending.

I need to construct a JSON object with:
- intent: "search_documents"
- target: "documents"
- filters: {"project":"基盤改善","status":"not_archived"}
- sort: ["created_at_desc"]
- limit: 20 (default)

Wait, I need to check the available filters. The user mentioned "not archived" which might be "status":"not_archived" or similar. Looking at the filters list: project, status, assignee, priority, due, created, score_lt. "status":"not_archived" seems reasonable.

Let me construct the JSON properly.
</think>

{"intent":"search_documents","target":"documents","filters":{"project":"基盤改善","status":"not_archived"},"sort":["created_at_desc"],"limit":20}

```

### Example 2

- user: 高橋さんに割り当てられている終わっていない緊急のタスクを締切が遅い順で10件だけリストアップして
- error: assistant content is not valid JSON: Expecting value: line 1 column 1 (char 0)

```text
The user wants to search for tasks with specific criteria:
- Assignee: 高橋 (Takahashi)
- Status: not done (unfinished)
- Priority: urgent (緊急)
- Sort: by due date ascending (締切が遅い順)
- Limit: 10 items

I need to output only JSON in the specified format without any explanations, markdown, or code fences.

Looking at the filters available:
- project
- status
- assignee
- priority
- due
- created
- score_lt

For "not done" status, I should use status="not_done" or similar. In Japanese context, "終わっていない" means not done, so status="not_done" or status!="done".

For "urgent" priority, I should use priority="urgent".

For "assignee", I should use assignee="高橋".

For sorting, "締切が遅い順" means due_date_asc (ascending by due date).

For limit, I should set limit=10.

Let me construct the JSON:
{"intent":"search_tasks","target":"tasks","filters":{"project":null,"status":"not_done","assignee":"高橋","priority":"
```

### Example 4

- user: アーカイブ済みのドキュメントを作成日時の昇順で見せて
- error: schema mismatch

```text
The user wants to search for documents with status "archived" and sort them by creation date ascending. I need to output only JSON without any explanation, markdown, or code fences.

Looking at the intent options, "search_documents" is the appropriate one.
Target is "documents".
Filters should include status="archived".
Sort should be ["created_at_asc"].
Limit is 20 (default).

Let me construct the JSON properly.
</think>

{"intent":"search_documents","target":"documents","filters":{"status":"archived"},"sort":["created_at_asc"],"limit":20}

```

### Example 8

- user: 名前に基盤改善を含む高優先度のアーカイブされていないプロジェクトを作成日時の昇順で見せて
- error: assistant content does not match OperationPlan: 5 validation errors for OperationPlan
intent
  Field required [type=missing, input_value={'project': '基盤改善...ed', 'priority': 'high'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.13/v/missing
target
  Field required [type=missing, input_value={'project': '基盤改善...ed', 'priority': 'high'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.13/v/missing
project
  Extra inputs are not permitted [type=extra_forbidden, input_value='基盤改善', input_type=str]
    For further information visit https://errors.pydantic.dev/2.13/v/extra_forbidden
status
  Extra inputs are not permitted [type=extra_forbidden, input_value='not_archived', input_type=str]
    For further information visit https://errors.pydantic.dev/2.13/v/extra_forbidden
priority
  Extra inputs are not permitted [type=extra_forbidden, input_value='high', input_type=str]
    For further information visit https://errors.pydantic.dev/2.13/v/extra_forbidden

```text
The user wants to search for projects with the name "基盤改善" (base improvement), that are not archived, with high priority, sorted by creation date ascending.

I need to construct a JSON object with the following fields:
- intent: "search_projects"
- target: "projects"
- filters: {"project":"基盤改善","status":"not_archived","priority":"high"}
- sort: ["created_at_asc"]
- limit: 20 (default)

Wait, I need to check the available filters. The user mentioned "project name contains 基盤改善", "not archived", "high priority", and "sort by created_at_asc".

Looking at the filters available:
- project
- status
- assignee
- priority
- due
- created
- score_lt

So I can use:
- project: "基盤改善"
- status: "not_archived" (or maybe "not_archived" is not a valid status, I should check what statuses are available. The user said "not archived", so I'll use "not_archived" as the status value)
- priority: "high"
- sort: ["created_at_asc"]

The
```

