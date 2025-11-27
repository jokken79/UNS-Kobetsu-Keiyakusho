"""
Webhook Schemas

Pydantic models for webhook configuration and logging.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, HttpUrl, ConfigDict, field_validator


class WebhookConfigBase(BaseModel):
    """Base webhook configuration schema."""
    name: str
    url: str
    events: List[str]
    is_active: bool = True


class WebhookConfigCreate(WebhookConfigBase):
    """Schema for creating webhook configuration."""
    secret: Optional[str] = None
    custom_headers: Optional[Dict[str, str]] = None
    max_retries: int = 3
    retry_delay_seconds: int = 60
    description: Optional[str] = None

    @field_validator('events')
    @classmethod
    def validate_events(cls, v):
        """Validate event types."""
        valid_events = [
            "contract.created",
            "contract.updated",
            "contract.deleted",
            "contract.submitted_for_approval",
            "contract.approved",
            "contract.rejected",
            "contract.signed",
            "contract.expired",
            "conflict_date.approaching",
            "employee.assigned",
            "employee.terminated",
        ]

        for event in v:
            if event not in valid_events:
                raise ValueError(f"Invalid event type: {event}")

        return v


class WebhookConfigUpdate(BaseModel):
    """Schema for updating webhook configuration."""
    name: Optional[str] = None
    url: Optional[str] = None
    secret: Optional[str] = None
    events: Optional[List[str]] = None
    is_active: Optional[bool] = None
    custom_headers: Optional[Dict[str, str]] = None
    max_retries: Optional[int] = None
    retry_delay_seconds: Optional[int] = None
    description: Optional[str] = None


class WebhookConfigResponse(WebhookConfigBase):
    """Webhook configuration response schema."""
    id: int
    secret: Optional[str] = None
    custom_headers: Optional[Dict[str, str]] = None
    max_retries: int
    retry_delay_seconds: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_triggered_at: Optional[datetime] = None
    description: Optional[str] = None
    created_by: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class WebhookLogResponse(BaseModel):
    """Webhook log response schema."""
    id: int
    webhook_config_id: int
    event_type: str
    event_data: Dict[str, Any]
    attempt_number: int
    status_code: Optional[int] = None
    response_body: Optional[str] = None
    error_message: Optional[str] = None
    success: bool
    attempted_at: datetime
    completed_at: Optional[datetime] = None
    response_time_ms: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class WebhookTestRequest(BaseModel):
    """Schema for testing webhooks."""
    event_type: str
    event_data: Optional[Dict[str, Any]] = None
