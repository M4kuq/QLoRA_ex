from __future__ import annotations

import json
import random
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from finetune_lab.schemas import OperationFilters, OperationPlan, SFTRecord, SortKey

SYSTEM_PROMPT = (
    "あなたは日本語の業務指示をJSON操作計画に変換するアシスタントです。"
    "出力はJSONのみ。許可されたintent、target、filters、sort、limitだけを使ってください。"
)

PROJECTS = ["Aプロジェクト", "RAG改善", "基盤改善", "採用サイト", "社内ポータル"]
ASSIGNEES = ["田中", "佐藤", "鈴木", "高橋", "山本"]

TRAIN_VERBS = ["出して", "表示して", "探して", "一覧にして"]
EVAL_VERBS = ["見せて", "抽出して", "リストアップして", "確認したい"]


@dataclass(frozen=True)
class DatasetSizes:
    train: int = 1000
    valid: int = 200
    test: int = 200


def create_dataset(
    sizes: DatasetSizes | None = None,
    *,
    seed: int = 42,
) -> dict[str, list[dict[str, Any]]]:
    sizes = sizes or DatasetSizes()
    return {
        "train": generate_records(sizes.train, split="train", seed=seed),
        "valid": generate_records(sizes.valid, split="valid", seed=seed + 1),
        "test": generate_records(sizes.test, split="test", seed=seed + 2),
    }


def generate_records(count: int, *, split: str, seed: int = 42) -> list[dict[str, Any]]:
    if count < 0:
        raise ValueError("count must be non-negative")
    if split not in {"train", "valid", "test"}:
        raise ValueError("split must be train, valid, or test")

    rng = random.Random(seed)
    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    max_attempts = max(1000, count * 30)

    for _ in range(max_attempts):
        if len(records) >= count:
            break

        plan = _random_plan(rng)
        user_text = _instruction_for_plan(plan, rng, split=split)
        assistant_text = plan.to_json_string()
        signature = f"{user_text}\n{assistant_text}"
        if signature in seen:
            continue

        record = {
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_text},
                {"role": "assistant", "content": assistant_text},
            ]
        }
        SFTRecord.model_validate(record)
        records.append(record)
        seen.add(signature)

    if len(records) < count:
        raise RuntimeError(f"only generated {len(records)} unique records out of {count}")
    return records


def write_jsonl(records: Iterable[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")))
            file.write("\n")


def write_dataset(dataset: dict[str, list[dict[str, Any]]], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for split, records in dataset.items():
        write_jsonl(records, output_dir / f"{split}.jsonl")


def _random_plan(rng: random.Random) -> OperationPlan:
    target = rng.choices(
        ["tasks", "projects", "documents", "jobs", "evaluation_runs"],
        weights=[45, 10, 15, 15, 15],
        k=1,
    )[0]
    if target == "tasks":
        return _random_task_plan(rng)
    if target == "projects":
        return _random_project_plan(rng)
    if target == "documents":
        return _random_document_plan(rng)
    if target == "jobs":
        return _random_job_plan(rng)
    return _random_evaluation_run_plan(rng)


def _random_task_plan(rng: random.Random) -> OperationPlan:
    filters = OperationFilters(
        project=rng.choice(PROJECTS) if rng.random() < 0.45 else None,
        status=rng.choice(["todo", "in_progress", "not_done", "review_waiting"]),
        assignee=rng.choice(ASSIGNEES) if rng.random() < 0.35 else None,
        priority=rng.choice(["low", "medium", "high", "urgent"]) if rng.random() < 0.55 else None,
        due=rng.choice(["overdue", "today", "tomorrow", "this_week", "next_week", "none"])
        if rng.random() < 0.7
        else None,
    )
    sort_options: list[list[SortKey]] = [
        ["due_date_asc"],
        ["due_date_desc"],
        ["priority_desc"],
        ["priority_asc"],
        ["created_at_desc"],
    ]
    sort = rng.choice(sort_options)
    return OperationPlan(
        intent="search_tasks",
        target="tasks",
        filters=filters,
        sort=sort,
        limit=rng.choice([10, 20, 30]),
    )


def _random_project_plan(rng: random.Random) -> OperationPlan:
    filters = OperationFilters(
        project=rng.choice(PROJECTS) if rng.random() < 0.5 else None,
        status=rng.choice(["in_progress", "done", "archived", "not_archived"]),
        priority=rng.choice(["medium", "high", "urgent"]) if rng.random() < 0.35 else None,
    )
    sort_options: list[list[SortKey]] = [
        ["created_at_desc"],
        ["created_at_asc"],
        ["priority_desc"],
    ]
    return OperationPlan(
        intent="search_projects",
        target="projects",
        filters=filters,
        sort=rng.choice(sort_options),
        limit=rng.choice([10, 20]),
    )


def _random_document_plan(rng: random.Random) -> OperationPlan:
    filters = OperationFilters(
        project=rng.choice(PROJECTS) if rng.random() < 0.45 else None,
        status=rng.choice(["archived", "not_archived"]),
        created=rng.choice(["today", "this_week", "last_week"]) if rng.random() < 0.35 else None,
    )
    sort_options: list[list[SortKey]] = [["created_at_desc"], ["created_at_asc"]]
    return OperationPlan(
        intent="search_documents",
        target="documents",
        filters=filters,
        sort=rng.choice(sort_options),
        limit=rng.choice([10, 20, 50]),
    )


def _random_job_plan(rng: random.Random) -> OperationPlan:
    filters = OperationFilters(
        project=rng.choice(PROJECTS) if rng.random() < 0.35 else None,
        status=rng.choice(["failed", "succeeded"]),
        created=rng.choice(["yesterday", "today", "this_week", "last_week"]),
    )
    sort_options: list[list[SortKey]] = [["created_at_desc"], ["created_at_asc"]]
    return OperationPlan(
        intent="search_jobs",
        target="jobs",
        filters=filters,
        sort=rng.choice(sort_options),
        limit=rng.choice([10, 20]),
    )


def _random_evaluation_run_plan(rng: random.Random) -> OperationPlan:
    filters = OperationFilters(
        project=rng.choice(PROJECTS) if rng.random() < 0.4 else None,
        status=rng.choice(["failed", "succeeded"]) if rng.random() < 0.35 else None,
        score_lt=rng.choice([0.7, 0.75, 0.8, 0.85]) if rng.random() < 0.75 else None,
        created=rng.choice(["today", "this_week", "last_week"]) if rng.random() < 0.35 else None,
    )
    sort_options: list[list[SortKey]] = [
        ["score_asc"],
        ["score_desc"],
        ["created_at_desc"],
    ]
    return OperationPlan(
        intent="search_evaluation_runs",
        target="evaluation_runs",
        filters=filters,
        sort=rng.choice(sort_options),
        limit=rng.choice([10, 20, 30]),
    )


def _instruction_for_plan(plan: OperationPlan, rng: random.Random, *, split: str) -> str:
    verb = rng.choice(TRAIN_VERBS if split == "train" else EVAL_VERBS)
    filters = plan.filters.model_dump(exclude_none=True)

    if plan.target == "tasks":
        subject = _join_phrases(_task_filter_phrases(filters, rng, split), "タスク")
    elif plan.target == "projects":
        subject = _join_phrases(_project_filter_phrases(filters, rng, split), "プロジェクト")
    elif plan.target == "documents":
        subject = _join_phrases(_document_filter_phrases(filters, rng, split), "ドキュメント")
    elif plan.target == "jobs":
        subject = _join_phrases(_job_filter_phrases(filters, rng, split), "ジョブ")
    else:
        subject = _join_phrases(_eval_filter_phrases(filters, rng, split), "RAG実行結果")

    sort_phrase = _sort_phrase(plan.sort, rng, split)
    limit_phrase = _limit_phrase(plan.limit, rng)
    if verb == "確認したい":
        return f"{subject}を{sort_phrase}{limit_phrase}確認したい"
    return f"{subject}を{sort_phrase}{limit_phrase}{verb}"


def _task_filter_phrases(filters: dict[str, Any], rng: random.Random, split: str) -> list[str]:
    phrases: list[str] = []
    if project := filters.get("project"):
        phrases.append(f"{project}の")
    if status := filters.get("status"):
        train = {
            "todo": "未着手の",
            "in_progress": "進行中の",
            "not_done": "未完了の",
            "review_waiting": "レビュー待ちの",
        }
        eval_ = {
            "todo": "まだ着手していない",
            "in_progress": "対応中の",
            "not_done": "終わっていない",
            "review_waiting": "レビュー待機中の",
        }
        phrases.append((train if split == "train" else eval_)[status])
    if assignee := filters.get("assignee"):
        phrases.append(f"{assignee}さんに割り当てられている")
    if priority := filters.get("priority"):
        phrases.append(
            {
                "low": "低優先度の",
                "medium": "中優先度の",
                "high": "高優先度の",
                "urgent": "緊急の",
            }[priority]
        )
    if due := filters.get("due"):
        phrases.append(
            {
                "overdue": "期限切れの",
                "today": "今日期限の",
                "tomorrow": "明日期限の",
                "this_week": "今週期限の",
                "next_week": "来週期限の",
                "none": "期限なしの",
            }[due]
        )
    rng.shuffle(phrases)
    return phrases


def _project_filter_phrases(filters: dict[str, Any], rng: random.Random, split: str) -> list[str]:
    phrases: list[str] = []
    if project := filters.get("project"):
        phrases.append(f"名前に{project}を含む")
    if status := filters.get("status"):
        phrases.append(
            {
                "in_progress": "進行中の",
                "done": "完了済みの",
                "archived": "アーカイブ済みの",
                "not_archived": "アーカイブされていない",
            }[status]
        )
    if priority := filters.get("priority"):
        phrases.append(
            {
                "medium": "中優先度の",
                "high": "高優先度の",
                "urgent": "緊急度が高い",
            }[priority]
        )
    rng.shuffle(phrases)
    return phrases


def _document_filter_phrases(filters: dict[str, Any], rng: random.Random, split: str) -> list[str]:
    phrases: list[str] = []
    if project := filters.get("project"):
        phrases.append(f"{project}関連の")
    if status := filters.get("status"):
        phrases.append(
            {
                "archived": "アーカイブ済みの",
                "not_archived": "アーカイブ済みではない",
            }[status]
        )
    if created := filters.get("created"):
        phrases.append(
            {
                "today": "今日作成された",
                "this_week": "今週作成された",
                "last_week": "先週作成された",
            }[created]
        )
    rng.shuffle(phrases)
    return phrases


def _job_filter_phrases(filters: dict[str, Any], rng: random.Random, split: str) -> list[str]:
    phrases: list[str] = []
    if project := filters.get("project"):
        phrases.append(f"{project}の")
    if created := filters.get("created"):
        phrases.append(
            {
                "yesterday": "昨日実行された",
                "today": "今日実行された",
                "this_week": "今週実行された",
                "last_week": "先週実行された",
            }[created]
        )
    if status := filters.get("status"):
        phrases.append({"failed": "失敗した", "succeeded": "成功した"}[status])
    rng.shuffle(phrases)
    return phrases


def _eval_filter_phrases(filters: dict[str, Any], rng: random.Random, split: str) -> list[str]:
    phrases: list[str] = []
    if project := filters.get("project"):
        phrases.append(f"{project}の")
    if score_lt := filters.get("score_lt"):
        phrases.append(f"評価スコアが{score_lt:g}未満の")
    if status := filters.get("status"):
        phrases.append({"failed": "失敗した", "succeeded": "成功した"}[status])
    if created := filters.get("created"):
        phrases.append(
            {
                "today": "今日の",
                "this_week": "今週の",
                "last_week": "先週の",
            }[created]
        )
    rng.shuffle(phrases)
    return phrases


def _sort_phrase(sort: Sequence[str], rng: random.Random, split: str) -> str:
    if not sort:
        return ""
    sort_key = sort[0]
    train = {
        "due_date_asc": "を期限が近い順に",
        "due_date_desc": "を期限が遠い順に",
        "priority_desc": "を優先度が高い順に",
        "priority_asc": "を優先度が低い順に",
        "created_at_desc": "を新しい順に",
        "created_at_asc": "を古い順に",
        "score_asc": "をスコアが低い順に",
        "score_desc": "をスコアが高い順に",
    }
    eval_ = {
        "due_date_asc": "を締切が近い順で",
        "due_date_desc": "を締切が遅い順で",
        "priority_desc": "を重要度が高い順で",
        "priority_asc": "を重要度が低い順で",
        "created_at_desc": "を作成日時の降順で",
        "created_at_asc": "を作成日時の昇順で",
        "score_asc": "を低スコア順で",
        "score_desc": "を高スコア順で",
    }
    phrase = (train if split == "train" else eval_)[sort_key]
    return phrase.removeprefix("を")


def _limit_phrase(limit: int, rng: random.Random) -> str:
    if limit == 20 or rng.random() < 0.35:
        return ""
    return f"{limit}件だけ"


def _join_phrases(phrases: list[str], noun: str) -> str:
    if not phrases:
        return noun
    return "".join(phrases) + noun
