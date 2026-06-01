from finetune_lab.schemas import OperationPlan
from finetune_lab.sql_converter import plan_to_select_query


def test_task_plan_converts_to_parameterized_select() -> None:
    plan = OperationPlan.model_validate(
        {
            "intent": "search_tasks",
            "target": "tasks",
            "filters": {
                "project": "Aプロジェクト",
                "status": "not_done",
                "priority": "high",
                "due": "overdue",
            },
            "sort": ["due_date_asc"],
            "limit": 20,
        }
    )

    query = plan_to_select_query(plan)

    assert query.sql == (
        "SELECT * FROM tasks "
        "WHERE project_name = ? AND status = ? AND priority = ? AND due_bucket = ? "
        "ORDER BY due_date ASC LIMIT ?"
    )
    assert query.params == ("Aプロジェクト", "not_done", "high", "overdue", 20)


def test_evaluation_score_filter_uses_less_than_operator() -> None:
    plan = OperationPlan.model_validate(
        {
            "intent": "search_evaluation_runs",
            "target": "evaluation_runs",
            "filters": {"score_lt": 0.8},
            "sort": ["score_asc"],
            "limit": 10,
        }
    )

    query = plan_to_select_query(plan)

    assert query.sql == (
        "SELECT * FROM evaluation_runs WHERE score < ? ORDER BY score ASC LIMIT ?"
    )
    assert query.params == (0.8, 10)


def test_user_values_are_not_interpolated_into_sql() -> None:
    plan = OperationPlan.model_validate(
        {
            "intent": "search_tasks",
            "target": "tasks",
            "filters": {"project": "x'; DROP TABLE tasks; --", "status": "not_done"},
            "sort": ["created_at_desc"],
            "limit": 20,
        }
    )

    query = plan_to_select_query(plan)

    assert "DROP TABLE" not in query.sql
    assert "x'; DROP TABLE tasks; --" in query.params
