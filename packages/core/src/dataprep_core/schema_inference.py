"""Infer column metadata from a Polars DataFrame."""

from uuid import NAMESPACE_URL, uuid5

import polars as pl

from dataprep_core.models import Column


_COLUMN_NAMESPACE = uuid5(NAMESPACE_URL, "dataprep-core")
_INTEGER_TYPES = {pl.Int8, pl.Int16, pl.Int32, pl.Int64}
_FLOAT_TYPES = {pl.Float32, pl.Float64}
_DATETIME_TYPES = {pl.Date, pl.Datetime, pl.Time}
_STRING_TYPES = {pl.Utf8}
if hasattr(pl, "LargeUtf8"):
    _STRING_TYPES.add(pl.LargeUtf8)


def _inferred_type(dtype: pl.DataType) -> str:
    base_type = dtype.base_type()
    if base_type in _INTEGER_TYPES:
        return "integer"
    if base_type in _FLOAT_TYPES:
        return "float"
    if base_type == pl.Boolean:
        return "boolean"
    if base_type in _DATETIME_TYPES:
        return "datetime"
    if base_type in _STRING_TYPES:
        return "string"
    return "unknown"


def _distinct_values(series: pl.Series) -> tuple[int, list[object]]:
    """Return distinct count and first five values, including object dtypes."""
    try:
        return series.n_unique(), series.unique(maintain_order=True).head(5).to_list()
    except pl.exceptions.InvalidOperationError:
        # Polars cannot calculate uniqueness for Object columns.
        seen: list[object] = []
        samples: list[object] = []
        for value in series:
            if any(value is prior or value == prior for prior in seen):
                continue
            seen.append(value)
            if len(samples) < 5:
                samples.append(value)
        return len(seen), samples


def infer_columns(df: pl.DataFrame, dataset_version_id: str) -> list[Column]:
    """Create metadata for each column of a non-empty DataFrame."""
    if df.is_empty():
        return []

    columns = []
    for series in df:
        non_null = series.drop_nulls()
        distinct_count, samples = _distinct_values(non_null)
        columns.append(
            Column(
                id=str(uuid5(_COLUMN_NAMESPACE, f"{dataset_version_id}:{series.name}")),
                dataset_version_id=dataset_version_id,
                name=series.name,
                inferred_type=_inferred_type(series.dtype),
                nullable=series.null_count() > 0,
                unique=distinct_count == len(non_null),
                sample_values=[str(value) for value in samples],
            )
        )
    return columns
