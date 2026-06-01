from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from finetune_lab.schemas import OperationPlan

SQLParam = str | int | float

TABLE_BY_TARGET: dict[str, str] = {
    "tasks": "tasks",
    "projects": "projects",
    "documents": "documents",
    "jobs": "jobs",
    "evaluation_runs": "evaluation_runs",
}

COLUMN_BY_FILTER: dict[str, str] = {
    "project": "project_name",
    "status": "status",
    "assignee": "assignee_name",
    "priority": "priority",
    "due": "due_bucket",
    "created": "created_bucket",
    "score_lt": "score",
}

ORDER_BY_SORT: dict[str, str] = {
    "due_date_asc": "due_date ASC",
    "due_date_desc": "due_date DESC",
    "priority_desc": "priority_rank DESC",
    "priority_asc": "priority_rank ASC",
    "created_at_desc": "created_at DESC",
    "created_at_asc": "created_at ASC",
    "score_asc": "score ASC",
    "score_desc": "score DESC",
}


@dataclass(frozen=True)
class SQLQuery:
    sql: str
    params: tuple[SQLParam, ...]


def plan_to_select_query(plan: OperationPlan) -> SQLQuery:
    """Convert a validated operation plan into a parameterized read-only query."""

    table = TABLE_BY_TARGET[plan.target]
    filters = plan.filters.model_dump(exclude_none=True)
    clauses: list[str] = []
    params: list[SQLParam] = []

    for filter_name, raw_value in filters.items():
        column = COLUMN_BY_FILTER[filter_name]
        value = _param_value(raw_value)
        if filter_name == "score_lt":
            clauses.append(f"{column} < ?")
        else:
            clauses.append(f"{column} = ?")
        params.append(value)

    sql_parts = [f"SELECT * FROM {table}"]
    if clauses:
        sql_parts.append("WHERE " + " AND ".join(clauses))
    if plan.sort:
        order_by = ", ".join(ORDER_BY_SORT[sort_key] for sort_key in plan.sort)
        sql_parts.append(f"ORDER BY {order_by}")
    sql_parts.append("LIMIT ?")
    params.append(plan.limit)

    return SQLQuery(sql=" ".join(sql_parts), params=tuple(params))


def _param_value(value: Any) -> SQLParam:
    if isinstance(value, str | int | float):
        return value
    raise TypeError(f"unsupported SQL parameter value: {value!r}")
