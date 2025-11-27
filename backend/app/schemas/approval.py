"""
Approval Schemas

Pydantic models for contract approval workflow.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class ApprovalRequest(BaseModel):
    """Schema for submitting a contract for approval."""
    notes: Optional[str] = None


class ApprovalAction(BaseModel):
    """Schema for approval/rejection actions."""
    notes: Optional[str] = None


class ApprovalResponse(BaseModel):
    """Schema for approval response."""
    contract_id: int
    status: str
    action: str  # 'approved', 'rejected', 'submitted', 'recalled'
    performed_by: str
    performed_at: datetime
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ApprovalStats(BaseModel):
    """Schema for approval statistics."""
    pending_count: int
    approved_this_month: int
    rejected_this_month: int
    avg_approval_time_hours: float
    oldest_pending_days: Optional[int] = None
    oldest_pending_contract: Optional[str] = None
