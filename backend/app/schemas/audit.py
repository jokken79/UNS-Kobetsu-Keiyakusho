"""
Audit Log Schemas

Pydantic models for audit log and contract version API responses.
"""
from datetime import datetime
from typing import Optional, Any, Dict
from pydantic import BaseModel, ConfigDict


class AuditLogBase(BaseModel):
    """Base audit log schema."""
    entity_type: str
    entity_id: int
    action: str


class AuditLogResponse(AuditLogBase):
    """Audit log response schema."""
    id: int
    user_id: int
    user_email: str
    user_name: Optional[str] = None
    timestamp: datetime
    field_name: Optional[str] = None
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    full_snapshot: Optional[Dict[str, Any]] = None
    reason: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class AuditLogFilter(BaseModel):
    """Audit log filter parameters."""
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    action: Optional[str] = None
    user_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class ContractVersionBase(BaseModel):
    """Base contract version schema."""
    contract_id: int
    version_number: int


class ContractVersionResponse(ContractVersionBase):
    """Contract version response schema."""
    id: int
    version_date: datetime
    created_by: int
    created_by_email: str
    contract_data: Dict[str, Any]
    change_summary: Optional[str] = None
    change_type: Optional[str] = None
    status: str

    model_config = ConfigDict(from_attributes=True)


class ContractVersionCreate(BaseModel):
    """Schema for creating a new contract version."""
    contract_id: int
    contract_data: Dict[str, Any]
    change_summary: Optional[str] = None
    change_type: str = "draft"
    status: str
