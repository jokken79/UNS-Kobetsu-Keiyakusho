"""
Webhook Model
Configuration and logging for webhooks to external systems (ERP, etc).
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, JSON
from sqlalchemy.sql import func

from app.core.database import Base


class WebhookConfig(Base):
    """
    Webhook configuration for integrating with external systems.
    """
    __tablename__ = "webhook_configs"

    id = Column(Integer, primary_key=True, index=True)

    # Webhook details
    name = Column(String(255), nullable=False)  # Human-readable name
    url = Column(String(500), nullable=False)  # Endpoint URL
    secret = Column(String(255))  # Shared secret for HMAC validation

    # Events to subscribe to
    events = Column(JSON, nullable=False)  # List of event types
    # Examples: ["contract.created", "contract.signed", "contract.expired", "conflict_date.approaching"]

    # Status
    is_active = Column(Boolean, default=True, index=True)

    # Headers (for authentication, etc)
    custom_headers = Column(JSON)  # Dict of custom headers

    # Retry configuration
    max_retries = Column(Integer, default=3)
    retry_delay_seconds = Column(Integer, default=60)

    # Timestamps
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    last_triggered_at = Column(DateTime)

    # Metadata
    description = Column(Text)
    created_by = Column(Integer)

    def __repr__(self):
        return f"<WebhookConfig {self.name} -> {self.url}>"


class WebhookLog(Base):
    """
    Log of webhook delivery attempts.
    """
    __tablename__ = "webhook_logs"

    id = Column(Integer, primary_key=True, index=True)

    # Webhook reference
    webhook_config_id = Column(Integer, nullable=False, index=True)

    # Event details
    event_type = Column(String(100), nullable=False, index=True)
    event_data = Column(JSON, nullable=False)  # Payload sent

    # Delivery attempt
    attempt_number = Column(Integer, default=1)
    status_code = Column(Integer)  # HTTP status code
    response_body = Column(Text)  # Response from endpoint
    error_message = Column(Text)  # Error if failed

    # Success/failure
    success = Column(Boolean, default=False, index=True)

    # Timestamps
    attempted_at = Column(DateTime, nullable=False, server_default=func.now(), index=True)
    completed_at = Column(DateTime)

    # Performance
    response_time_ms = Column(Integer)  # Response time in milliseconds

    def __repr__(self):
        status = "✓" if self.success else "✗"
        return f"<WebhookLog {status} {self.event_type} attempt {self.attempt_number}>"
