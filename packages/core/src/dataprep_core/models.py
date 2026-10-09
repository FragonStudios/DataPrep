"""Metadata models shared by DataPrep components."""

from typing import Any

from pydantic import BaseModel


class Tenant(BaseModel):
    id: str
    name: str
    plan: str
    status: str
    created_at: str
    updated_at: str


class User(BaseModel):
    id: str
    tenant_id: str
    email: str
    password_hash: str
    display_name: str
    status: str
    last_login_at: str | None = None
    created_at: str


class Role(BaseModel):
    id: str
    name: str
    description: str


class UserRole(BaseModel):
    user_id: str
    role_id: str
    tenant_id: str


class Project(BaseModel):
    id: str
    tenant_id: str
    name: str
    description: str
    created_by: str
    created_at: str


class Dataset(BaseModel):
    id: str
    project_id: str
    name: str
    source_type: str
    storage_key: str
    row_count: int
    checksum: str
    created_by: str
    created_at: str


class DatasetVersion(BaseModel):
    id: str
    dataset_id: str
    version: int
    storage_key: str
    checksum: str
    row_count: int
    created_at: str


class Column(BaseModel):
    id: str
    dataset_version_id: str
    name: str
    inferred_type: str
    declared_type: str | None = None
    nullable: bool
    unique: bool
    sample_values: list[Any]


class ValidationRule(BaseModel):
    id: str
    project_id: str
    dataset_id: str
    column_id: str | None = None
    rule_type: str
    expression: str
    severity: str
    enabled: bool
    description: str


class CleaningOperation(BaseModel):
    id: str
    project_id: str
    dataset_id: str
    operation_type: str
    parameters: dict[str, Any]
    order: int
    description: str


class Pipeline(BaseModel):
    id: str
    project_id: str
    name: str
    version: int
    operations: list[str]
    validation_rules: list[str]
    status: str
    created_by: str
    created_at: str


class Job(BaseModel):
    id: str
    pipeline_id: str
    dataset_version_id: str
    status: str
    triggered_by: str
    started_at: str | None = None
    finished_at: str | None = None
    error: str | None = None


class JobMetric(BaseModel):
    id: str
    job_id: str
    metric: str
    value: float
    details: dict[str, Any]


class Export(BaseModel):
    id: str
    job_id: str
    format: str
    storage_key: str
    checksum: str
    file_size: int
    created_at: str


class StorageObject(BaseModel):
    id: str
    tenant_id: str
    key: str
    size: int
    checksum: str
    content_type: str
    created_at: str


class AuditEvent(BaseModel):
    id: str
    tenant_id: str
    user_id: str
    action: str
    resource_type: str
    resource_id: str
    ip_address: str
    user_agent: str
    metadata: dict[str, Any]
    created_at: str


class SampleDataset(BaseModel):
    id: str
    name: str
    description: str
    storage_key: str
    version: int
    active: bool
