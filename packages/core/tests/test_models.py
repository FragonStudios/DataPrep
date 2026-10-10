"""Shared metadata models accept and serialize their declared fields."""

import json

import pytest

from dataprep_core import models


NOW = "2026-01-02T03:04:05Z"


@pytest.mark.parametrize(
    ("model_type", "data"),
    [
        (models.Tenant, dict(id="t1", name="Tenant", plan="free", status="active", created_at=NOW, updated_at=NOW)),
        (models.User, dict(id="u1", tenant_id="t1", email="user@example.com", password_hash="hash", display_name="User", status="active", last_login_at=None, created_at=NOW)),
        (models.Role, dict(id="r1", name="admin", description="Administrator")),
        (models.UserRole, dict(user_id="u1", role_id="r1", tenant_id="t1")),
        (models.Project, dict(id="p1", tenant_id="t1", name="Project", description="Example", created_by="u1", created_at=NOW)),
        (models.Dataset, dict(id="d1", project_id="p1", name="Dataset", source_type="csv", storage_key="data.csv", row_count=3, checksum="abc", created_by="u1", created_at=NOW)),
        (models.DatasetVersion, dict(id="v1", dataset_id="d1", version=1, storage_key="v1.csv", checksum="abc", row_count=3, created_at=NOW)),
        (models.Column, dict(id="c1", dataset_version_id="v1", name="value", inferred_type="integer", declared_type=None, nullable=False, unique=True, sample_values=[1, 2, None])),
        (models.ValidationRule, dict(id="vr1", project_id="p1", dataset_id="d1", column_id="c1", rule_type="range", expression="value > 0", severity="error", enabled=True, description="Positive values")),
        (models.CleaningOperation, dict(id="op1", project_id="p1", dataset_id="d1", operation_type="replace", parameters={"from": None, "to": 0}, order=1, description="Fill missing values")),
        (models.Pipeline, dict(id="pl1", project_id="p1", name="Pipeline", version=1, operations=["op1"], validation_rules=["vr1"], status="active", created_by="u1", created_at=NOW)),
        (models.Job, dict(id="j1", pipeline_id="pl1", dataset_version_id="v1", status="running", triggered_by="u1", started_at=NOW, finished_at=None, error=None)),
        (models.JobMetric, dict(id="m1", job_id="j1", metric="rows_processed", value=3.0, details={"stage": "clean"})),
        (models.Export, dict(id="e1", job_id="j1", format="csv", storage_key="export.csv", checksum="def", file_size=100, created_at=NOW)),
        (models.StorageObject, dict(id="s1", tenant_id="t1", key="data.csv", size=100, checksum="abc", content_type="text/csv", created_at=NOW)),
        (models.AuditEvent, dict(id="a1", tenant_id="t1", user_id="u1", action="create", resource_type="dataset", resource_id="d1", ip_address="127.0.0.1", user_agent="test", metadata={"source": "api"}, created_at=NOW)),
        (models.SampleDataset, dict(id="sd1", name="Sample", description="Example", storage_key="sample.csv", version=1, active=True)),
    ],
)
def test_model_json_round_trip(model_type, data):
    instance = model_type(**data)

    assert set(model_type.model_fields) == set(data)
    assert json.loads(instance.model_dump_json()) == data
    assert model_type.model_validate_json(instance.model_dump_json()) == instance
