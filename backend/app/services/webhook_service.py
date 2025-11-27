"""
Webhook Service
Manages webhooks for integration with external systems (ERP, payroll, etc).
"""
import hmac
import hashlib
import json
import time
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc
import requests

from app.models.webhook import WebhookConfig, WebhookLog


class WebhookService:
    """Service for managing and triggering webhooks."""

    def __init__(self, db: Session):
        self.db = db

    def create_webhook(
        self,
        name: str,
        url: str,
        events: List[str],
        secret: Optional[str] = None,
        custom_headers: Optional[Dict[str, str]] = None,
        max_retries: int = 3,
        retry_delay_seconds: int = 60,
        description: Optional[str] = None,
        created_by: Optional[int] = None
    ) -> WebhookConfig:
        """
        Create a new webhook configuration.

        Args:
            name: Human-readable name
            url: Endpoint URL
            events: List of events to subscribe to
            secret: Shared secret for HMAC validation
            custom_headers: Custom headers (for auth, etc)
            max_retries: Maximum retry attempts
            retry_delay_seconds: Delay between retries
            description: Optional description
            created_by: User ID who created it

        Returns:
            Created WebhookConfig
        """
        webhook = WebhookConfig(
            name=name,
            url=url,
            events=events,
            secret=secret,
            custom_headers=custom_headers or {},
            max_retries=max_retries,
            retry_delay_seconds=retry_delay_seconds,
            description=description,
            created_by=created_by,
            is_active=True
        )

        self.db.add(webhook)
        self.db.commit()
        self.db.refresh(webhook)

        return webhook

    def get_webhooks(
        self,
        is_active: Optional[bool] = None
    ) -> List[WebhookConfig]:
        """
        Get all webhook configurations.

        Args:
            is_active: Filter by active status (None = all)

        Returns:
            List of WebhookConfig
        """
        query = self.db.query(WebhookConfig)

        if is_active is not None:
            query = query.filter(WebhookConfig.is_active == is_active)

        return query.all()

    def get_webhook(self, webhook_id: int) -> Optional[WebhookConfig]:
        """Get a specific webhook by ID."""
        return self.db.query(WebhookConfig).filter(WebhookConfig.id == webhook_id).first()

    def update_webhook(
        self,
        webhook_id: int,
        **kwargs
    ) -> Optional[WebhookConfig]:
        """
        Update a webhook configuration.

        Args:
            webhook_id: ID of webhook to update
            **kwargs: Fields to update

        Returns:
            Updated WebhookConfig or None
        """
        webhook = self.get_webhook(webhook_id)
        if not webhook:
            return None

        for key, value in kwargs.items():
            if hasattr(webhook, key):
                setattr(webhook, key, value)

        self.db.commit()
        self.db.refresh(webhook)

        return webhook

    def delete_webhook(self, webhook_id: int) -> bool:
        """
        Delete a webhook configuration.

        Args:
            webhook_id: ID of webhook to delete

        Returns:
            True if deleted, False if not found
        """
        webhook = self.get_webhook(webhook_id)
        if not webhook:
            return False

        self.db.delete(webhook)
        self.db.commit()

        return True

    def trigger_event(
        self,
        event_type: str,
        event_data: Dict[str, Any]
    ) -> List[WebhookLog]:
        """
        Trigger webhooks for a specific event.

        Args:
            event_type: Type of event (e.g., 'contract.approved')
            event_data: Event payload data

        Returns:
            List of WebhookLog entries for each triggered webhook
        """
        # Find all active webhooks subscribed to this event
        webhooks = (
            self.db.query(WebhookConfig)
            .filter(
                WebhookConfig.is_active == True,
                WebhookConfig.events.contains([event_type])
            )
            .all()
        )

        logs = []
        for webhook in webhooks:
            log = self._send_webhook(webhook, event_type, event_data)
            logs.append(log)

        return logs

    def _send_webhook(
        self,
        webhook: WebhookConfig,
        event_type: str,
        event_data: Dict[str, Any],
        attempt_number: int = 1
    ) -> WebhookLog:
        """
        Send a webhook delivery.

        Args:
            webhook: WebhookConfig to send to
            event_type: Type of event
            event_data: Event payload
            attempt_number: Attempt number (for retries)

        Returns:
            WebhookLog entry
        """
        start_time = time.time()

        # Prepare payload
        payload = {
            "event": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": event_data
        }

        # Prepare headers
        headers = {
            "Content-Type": "application/json",
            "X-Event-Type": event_type,
            "User-Agent": "UNS-Kobetsu-Webhook/1.0"
        }

        # Add custom headers
        if webhook.custom_headers:
            headers.update(webhook.custom_headers)

        # Add HMAC signature if secret is configured
        if webhook.secret:
            payload_bytes = json.dumps(payload).encode('utf-8')
            signature = hmac.new(
                webhook.secret.encode('utf-8'),
                payload_bytes,
                hashlib.sha256
            ).hexdigest()
            headers["X-Webhook-Signature"] = f"sha256={signature}"

        # Create log entry
        log = WebhookLog(
            webhook_config_id=webhook.id,
            event_type=event_type,
            event_data=event_data,
            attempt_number=attempt_number,
            attempted_at=datetime.now(timezone.utc)
        )

        try:
            # Send HTTP POST request
            response = requests.post(
                webhook.url,
                json=payload,
                headers=headers,
                timeout=30  # 30 seconds timeout
            )

            # Calculate response time
            response_time_ms = int((time.time() - start_time) * 1000)

            # Update log with response
            log.status_code = response.status_code
            log.response_body = response.text[:1000]  # Limit to 1000 chars
            log.response_time_ms = response_time_ms
            log.success = 200 <= response.status_code < 300
            log.completed_at = datetime.now(timezone.utc)

            # Update webhook last_triggered_at
            webhook.last_triggered_at = datetime.now(timezone.utc)

        except requests.exceptions.Timeout:
            log.error_message = "Request timeout (30 seconds)"
            log.success = False
            log.completed_at = datetime.now(timezone.utc)

        except requests.exceptions.ConnectionError as e:
            log.error_message = f"Connection error: {str(e)[:500]}"
            log.success = False
            log.completed_at = datetime.now(timezone.utc)

        except Exception as e:
            log.error_message = f"Unexpected error: {str(e)[:500]}"
            log.success = False
            log.completed_at = datetime.now(timezone.utc)

        # Save log
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)

        # Retry if failed and retries remaining
        if not log.success and attempt_number < webhook.max_retries:
            # Schedule retry (in a real implementation, use a task queue like Celery)
            # For now, we just log that a retry is needed
            # You can implement retry logic with a background task
            pass

        return log

    def get_webhook_logs(
        self,
        webhook_id: int,
        limit: int = 100
    ) -> List[WebhookLog]:
        """
        Get logs for a specific webhook.

        Args:
            webhook_id: ID of webhook
            limit: Maximum number of logs to return

        Returns:
            List of WebhookLog entries, most recent first
        """
        return (
            self.db.query(WebhookLog)
            .filter(WebhookLog.webhook_config_id == webhook_id)
            .order_by(desc(WebhookLog.attempted_at))
            .limit(limit)
            .all()
        )

    def get_recent_failures(
        self,
        hours: int = 24,
        limit: int = 50
    ) -> List[WebhookLog]:
        """
        Get recent failed webhook deliveries.

        Args:
            hours: Number of hours to look back
            limit: Maximum number of logs

        Returns:
            List of failed WebhookLog entries
        """
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)

        return (
            self.db.query(WebhookLog)
            .filter(
                WebhookLog.success == False,
                WebhookLog.attempted_at >= cutoff_time
            )
            .order_by(desc(WebhookLog.attempted_at))
            .limit(limit)
            .all()
        )

    def test_webhook(
        self,
        webhook_id: int
    ) -> WebhookLog:
        """
        Send a test event to a webhook.

        Args:
            webhook_id: ID of webhook to test

        Returns:
            WebhookLog entry with test result
        """
        webhook = self.get_webhook(webhook_id)
        if not webhook:
            raise ValueError(f"Webhook {webhook_id} not found")

        test_data = {
            "test": True,
            "message": "This is a test webhook from UNS Kobetsu Keiyakusho",
            "webhook_id": webhook_id,
            "webhook_name": webhook.name
        }

        return self._send_webhook(webhook, "webhook.test", test_data)
