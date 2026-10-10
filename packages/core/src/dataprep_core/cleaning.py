"""Apply ordered cleaning operations to a Polars DataFrame."""

import ast
from dataclasses import dataclass

import polars as pl

from dataprep_core.models import CleaningOperation


@dataclass
class CleanResult:
    df: pl.DataFrame
    applied: list[str]
    removed_rows: int


_CAST_TYPES = {
    "integer": pl.Int64,
    "float": pl.Float64,
    "boolean": pl.Boolean,
    "string": pl.String,
    "datetime": pl.Datetime,
}

_FILTER_NODES = (
    ast.Expression,
    ast.BoolOp,
    ast.BinOp,
    ast.UnaryOp,
    ast.Compare,
    ast.Name,
    ast.Constant,
    ast.List,
    ast.Tuple,
    ast.And,
    ast.Or,
    ast.Not,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.Mod,
    ast.USub,
    ast.UAdd,
    ast.Eq,
    ast.NotEq,
    ast.Lt,
    ast.LtE,
    ast.Gt,
    ast.GtE,
    ast.Is,
    ast.IsNot,
    ast.In,
    ast.NotIn,
    ast.Load,
)


def _filter_rows(df: pl.DataFrame, expression: str) -> pl.DataFrame:
    """Evaluate a restricted Python expression against each row's columns."""
    tree = ast.parse(expression, mode="eval")
    for node in ast.walk(tree):
        if not isinstance(node, _FILTER_NODES):
            raise ValueError(f"Unsupported filter expression: {expression}")
        if isinstance(node, ast.Name) and node.id not in df.columns:
            raise ValueError(f"Unknown column in filter expression: {node.id}")

    code = compile(tree, "<cleaning filter>", "eval")
    mask = [bool(eval(code, {"__builtins__": {}}, row)) for row in df.iter_rows(named=True)]
    return df.filter(mask)


def apply_cleaning(df: pl.DataFrame, operations: list[CleaningOperation]) -> CleanResult:
    """Apply operations by order and report their IDs and net rows removed."""
    original_rows = df.height
    applied: list[str] = []

    for operation in sorted(operations, key=lambda item: item.order):
        params = operation.parameters
        kind = operation.operation_type

        if kind == "cast":
            to_type = params["to_type"]
            if to_type not in _CAST_TYPES:
                raise ValueError(f"Unsupported cast type: {to_type}")
            column_name = params["column"]
            column = pl.col(column_name)
            if df.schema[column_name] == pl.String and to_type == "boolean":
                column = column.str.to_lowercase().replace_strict({"true": True, "false": False})
            elif df.schema[column_name] == pl.String and to_type == "datetime":
                column = column.str.to_datetime()
            df = df.with_columns(column.cast(_CAST_TYPES[to_type]))
        elif kind == "fill_null":
            df = df.with_columns(pl.col(params["column"]).fill_null(params["value"]))
        elif kind == "drop_null":
            df = df.drop_nulls(subset=params.get("column"))
        elif kind == "deduplicate":
            df = df.unique(subset=params.get("columns"), keep="first", maintain_order=True)
        elif kind == "normalize":
            column = pl.col(params["column"])
            mode = params["mode"]
            if mode == "lower":
                normalized = column.str.to_lowercase()
            elif mode == "trim":
                normalized = column.str.strip_chars()
            else:
                raise ValueError(f"Unsupported normalize mode: {mode}")
            df = df.with_columns(normalized)
        elif kind == "filter":
            df = _filter_rows(df, params["expression"])
        else:
            raise ValueError(f"Unknown cleaning operation type: {kind}")

        applied.append(operation.id)

    return CleanResult(df=df, applied=applied, removed_rows=original_rows - df.height)
