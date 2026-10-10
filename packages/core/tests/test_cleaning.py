"""Tests for ordered DataFrame cleaning operations."""

import polars as pl
import pytest

from dataprep_core.cleaning import CleanResult, apply_cleaning
from dataprep_core.models import CleaningOperation


def operation(kind: str, params: dict, order: int = 0, id: str = "op") -> CleaningOperation:
    return CleaningOperation(
        id=id,
        project_id="project",
        dataset_id="dataset",
        operation_type=kind,
        parameters=params,
        order=order,
        description="",
    )


def test_operations_run_in_order_and_report_removed_rows():
    df = pl.DataFrame({"name": [" ALICE ", " ALICE ", " BOB ", None], "score": ["1", "1", "2", "3"]})
    operations = [
        operation("deduplicate", {"columns": ["name"]}, order=4, id="dedupe"),
        operation("normalize", {"column": "name", "mode": "lower"}, order=3, id="lower"),
        operation("cast", {"column": "score", "to_type": "integer"}, order=1, id="cast"),
        operation("normalize", {"column": "name", "mode": "trim"}, order=2, id="trim"),
        operation("drop_null", {"column": "name"}, order=5, id="drop"),
        operation("filter", {"expression": "score >= 2"}, order=6, id="filter"),
    ]

    result = apply_cleaning(df, operations)

    assert isinstance(result, CleanResult)
    assert result.applied == ["cast", "trim", "lower", "dedupe", "drop", "filter"]
    assert result.removed_rows == 3
    assert result.df.to_dict(as_series=False) == {"name": ["bob"], "score": [2]}
    assert df.height == 4


@pytest.mark.parametrize(
    ("to_type", "values", "expected"),
    [
        ("integer", ["1", "2"], [1, 2]),
        ("float", ["1.5", "2.5"], [1.5, 2.5]),
        ("boolean", ["true", "false"], [True, False]),
        ("string", [1, 2], ["1", "2"]),
    ],
)
def test_cast_types(to_type, values, expected):
    result = apply_cleaning(pl.DataFrame({"value": values}), [operation("cast", {"column": "value", "to_type": to_type})])
    assert result.df["value"].to_list() == expected


def test_cast_datetime():
    result = apply_cleaning(
        pl.DataFrame({"value": ["2026-01-02T03:04:05"]}),
        [operation("cast", {"column": "value", "to_type": "datetime"})],
    )
    assert result.df["value"].dtype == pl.Datetime
    assert result.df["value"].dt.year().to_list() == [2026]


def test_fill_null_and_drop_null_without_column():
    df = pl.DataFrame({"a": [None, 1, 1], "b": ["x", None, "y"]})
    result = apply_cleaning(df, [operation("fill_null", {"column": "a", "value": 0}), operation("drop_null", {})])
    assert result.df.to_dict(as_series=False) == {"a": [0, 1], "b": ["x", "y"]}
    assert result.removed_rows == 1


def test_deduplicate_all_columns_keeps_first():
    df = pl.DataFrame({"a": [1, 2, 1], "b": ["x", "y", "x"]})
    result = apply_cleaning(df, [operation("deduplicate", {})])
    assert result.df.to_dict(as_series=False) == {"a": [1, 2], "b": ["x", "y"]}
    assert result.removed_rows == 1


def test_filter_uses_row_values_and_rejects_code_execution():
    df = pl.DataFrame({"value": [1, 2, 3], "name": ["a", "b", "c"]})
    result = apply_cleaning(df, [operation("filter", {"expression": "value > 1 and name != 'c'"})])
    assert result.df["value"].to_list() == [2]

    with pytest.raises(ValueError, match="Unsupported filter expression"):
        apply_cleaning(df, [operation("filter", {"expression": "__import__('os').getcwd()"})])


def test_unknown_operation_and_invalid_modes_raise():
    df = pl.DataFrame({"value": ["x"]})
    with pytest.raises(ValueError, match="Unknown cleaning operation type"):
        apply_cleaning(df, [operation("other", {})])
    with pytest.raises(ValueError, match="Unsupported normalize mode"):
        apply_cleaning(df, [operation("normalize", {"column": "value", "mode": "other"})])
    with pytest.raises(ValueError, match="Unsupported cast type"):
        apply_cleaning(df, [operation("cast", {"column": "value", "to_type": "other"})])
