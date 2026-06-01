from __future__ import annotations

import json
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

Intent = Literal[
    "search_tasks",
    "search_projects",
    "search_documents",
    "search_jobs",
    "search_evaluation_runs",
]
Target = Literal["tasks", "projects", "documents", "jobs", "evaluation_runs"]
Status = Literal[
    "todo",
    "in_progress",
    "done",
    "not_done",
    "review_waiting",
    "archived",
    "not_archived",
    "failed",
    "succeeded",
]
Priority = Literal["low", "medium", "high", "urgent"]
Due = Literal["overdue", "today", "tomorrow", "this_week", "next_week", "none"]
Created = Literal["yesterday", "today", "this_week", "last_week"]
SortKey = Literal[
    "due_date_asc",
    "due_date_desc",
    "priority_desc",
    "priority_asc",
    "created_at_desc",
    "created_at_asc",
    "score_asc",
    "score_desc",
]
Role = Literal["system", "user", "assistant"]

TARGET_BY_INTENT: dict[str, str] = {
    "search_tasks": "tasks",
    "search_projects": "projects",
    "search_documents": "documents",
    "search_jobs": "jobs",
    "search_evaluation_runs": "evaluation_runs",
}

ALLOWED_FILTERS_BY_TARGET: dict[str, set[str]] = {
    "tasks": {"project", "status", "assignee", "priority", "due", "created"},
    "projects": {"project", "status", "priority", "created"},
    "documents": {"project", "status", "created"},
    "jobs": {"project", "status", "created"},
    "evaluation_runs": {"project", "status", "score_lt", "created"},
}

ALLOWED_SORTS_BY_TARGET: dict[str, set[str]] = {
    "tasks": {
        "due_date_asc",
        "due_date_desc",
        "priority_desc",
        "priority_asc",
        "created_at_desc",
        "created_at_asc",
    },
    "projects": {"priority_desc", "priority_asc", "created_at_desc", "created_at_asc"},
    "documents": {"created_at_desc", "created_at_asc"},
    "jobs": {"created_at_desc", "created_at_asc"},
    "evaluation_runs": {"score_asc", "score_desc", "created_at_desc", "created_at_asc"},
}


class OperationFilters(BaseModel):
    """Allowed filter fields for safe read-only operation plans."""

    model_config = ConfigDict(extra="forbid")

    project: str | None = Field(default=None, min_length=1, max_length=80)
    status: Status | None = None
    assignee: str | None = Field(default=None, min_length=1, max_length=80)
    priority: Priority | None = None
    due: Due | None = None
    created: Created | None = None
    score_lt: float | None = Field(default=None, ge=0.0, le=1.0)

    @field_validator("project", "assignee")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            raise ValueError("text filters must not be blank")
        return stripped


class OperationPlan(BaseModel):
    """Validated JSON operation plan emitted by the model."""

    model_config = ConfigDict(extra="forbid")

    intent: Intent
    target: Target
    filters: OperationFilters = Field(default_factory=OperationFilters)
    sort: list[SortKey] = Field(default_factory=list, max_length=3)
    limit: int = Field(default=20, ge=1, le=100)

    @model_validator(mode="after")
    def validate_target_contract(self) -> OperationPlan:
        expected_target = TARGET_BY_INTENT[self.intent]
        if self.target != expected_target:
            raise ValueError(f"intent {self.intent!r} requires target {expected_target!r}")

        filter_keys = set(self.filters.model_dump(exclude_none=True))
        allowed_filters = ALLOWED_FILTERS_BY_TARGET[self.target]
        unknown_filters = filter_keys - allowed_filters
        if unknown_filters:
            joined = ", ".join(sorted(unknown_filters))
            raise ValueError(f"filters not allowed for target {self.target!r}: {joined}")

        allowed_sorts = ALLOWED_SORTS_BY_TARGET[self.target]
        unknown_sorts = set(self.sort) - allowed_sorts
        if unknown_sorts:
            joined = ", ".join(sorted(unknown_sorts))
            raise ValueError(f"sort keys not allowed for target {self.target!r}: {joined}")

        return self

    def to_json_string(self) -> str:
        payload = self.model_dump(mode="json", exclude_none=True)
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


class ChatMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Role
    content: str = Field(min_length=1)


class SFTRecord(BaseModel):
    """Single JSONL row in TRL conversational messages format."""

    model_config = ConfigDict(extra="forbid")

    messages: list[ChatMessage] = Field(min_length=3, max_length=3)

    @model_validator(mode="after")
    def validate_message_contract(self) -> SFTRecord:
        roles = [message.role for message in self.messages]
        if roles != ["system", "user", "assistant"]:
            raise ValueError("messages must be exactly system, user, assistant")
        parse_operation_json(self.messages[-1].content)
        return self

    @property
    def user_content(self) -> str:
        return self.messages[1].content

    @property
    def assistant_plan(self) -> OperationPlan:
        return parse_operation_json(self.messages[-1].content)


def parse_operation_json(raw_text: str) -> OperationPlan:
    """Parse and validate a JSON operation plan emitted as assistant text."""

    try:
        payload: Any = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"assistant content is not valid JSON: {exc}") from exc

    try:
        return OperationPlan.model_validate(payload)
    except ValidationError as exc:
        raise ValueError(f"assistant content does not match OperationPlan: {exc}") from exc
