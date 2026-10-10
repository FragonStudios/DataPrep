"""Schema inference for Polars DataFrames."""

from uuid import NAMESPACE_URL, uuid5

import polars as pl

from dataprep_core.schema_inference import infer_columns


def test_infers_column_metadata_and_stable_ids():
    df = pl.DataFrame(
        {
            "number": [1, None, 2, 1, 3, 4, 5, 6],
            "label": ["a", "b", "a", "c", "d", "e", "f", "g"],
        }
    )

    columns = infer_columns(df, "version-1")

    assert len(columns) == 2
    assert columns[0].dataset_version_id == "version-1"
    assert columns[0].name == "number"
    assert columns[0].inferred_type == "integer"
    assert columns[0].declared_type is None
    assert columns[0].nullable is True
    assert columns[0].unique is False
    assert columns[0].sample_values == ["1", "2", "3", "4", "5"]
    assert columns[1].inferred_type == "string"
    assert columns[1].nullable is False
    assert columns[1].unique is False
    assert columns[1].sample_values == ["a", "b", "c", "d", "e"]

    namespace = uuid5(NAMESPACE_URL, "dataprep-core")
    assert columns[0].id == str(uuid5(namespace, "version-1:number"))
    assert infer_columns(df, "version-1") == columns
    assert infer_columns(df, "version-2")[0].id != columns[0].id


def test_maps_supported_and_unknown_dtypes():
    df = pl.DataFrame(
        [
            pl.Series("int8", [1], dtype=pl.Int8),
            pl.Series("int16", [1], dtype=pl.Int16),
            pl.Series("int32", [1], dtype=pl.Int32),
            pl.Series("int64", [1], dtype=pl.Int64),
            pl.Series("float32", [1.5], dtype=pl.Float32),
            pl.Series("float64", [1.5], dtype=pl.Float64),
            pl.Series("boolean", [True], dtype=pl.Boolean),
            pl.Series("date", ["2026-01-01"]).str.to_date(),
            pl.Series("datetime", ["2026-01-01T12:00:00"]).str.to_datetime(),
            pl.Series("time", ["12:00:00"]).str.to_time(),
            pl.Series("string", ["hello"], dtype=pl.Utf8),
            pl.Series("binary", [b"hello"], dtype=pl.Binary),
        ]
    )

    assert [column.inferred_type for column in infer_columns(df, "v1")] == [
        "integer", "integer", "integer", "integer",
        "float", "float", "boolean", "datetime", "datetime", "datetime",
        "string", "unknown",
    ]


def test_empty_all_null_and_object_columns():
    assert infer_columns(pl.DataFrame(), "v1") == []
    assert infer_columns(pl.DataFrame(schema={"value": pl.Int64}), "v1") == []

    df = pl.DataFrame(
        [
            pl.Series("missing", [None, None], dtype=pl.Null),
            pl.Series("objects", [[1], [1]], dtype=pl.Object),
        ]
    )
    missing, objects = infer_columns(df, "v1")

    assert missing.inferred_type == "unknown"
    assert missing.nullable is True
    assert missing.unique is True
    assert missing.sample_values == []
    assert objects.inferred_type == "unknown"
    assert objects.unique is False
    assert objects.sample_values == ["[1]"]
