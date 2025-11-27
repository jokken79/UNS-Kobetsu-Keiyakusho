"""
Webhook API Router

Endpoints for configuring and monitoring webhooks to external systems (ERP, etc).
"""
from datetime import datetime, date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.webhook import WebhookConfig, WebhookLog
from app.schemas.webhook import (
    WebhookConfigCreate,
    WebhookConfigUpdate,
    WebhookConfigResponse,
    WebhookLogResponse,
    WebhookTestRequest,
)

router = APIRouter()


# ========================================
# WEBHOOK CONFIG ENDPOINTS
# ========================================

@router.get("/", response_model=List[WebhookConfigResponse])
async def list_webhooks(
    active_only: bool = Query(False, description="Show only active webhooks"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get list of configured webhooks.
    """
    query = db.query(WebhookConfig)

    if active_only:
        query = query.filter(WebhookConfig.is_active == True)

    webhooks = query.order_by(WebhookConfig.created_at.desc()).all()

    return [WebhookConfigResponse.model_validate(w) for w in webhooks]


@router.post("/", response_model=WebhookConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_webhook(
    webhook: WebhookConfigCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role(["admin"])),
):
    """
    Create a new webhook configuration.

    Requires admin role.
    """
    webhook_config = WebhookConfig(
        name=webhook.name,
        url=webhook.url,
        secret=webhook.secret,
        events=webhook.events,
        is_active=webhook.is_active,
        custom_headers=webhook.custom_headers,
        max_retries=webhook.max_retries,
        retry_delay_seconds=webhook.retry_delay_seconds,
        description=webhook.description,
        created_by=current_user["id"],
    )

    db.add(webhook_config)
    db.commit()
    db.refresh(webhook_config)

    return WebhookConfigResponse.model_validate(webhook_config)


@router.get("/{webhook_id}", response_model=WebhookConfigResponse)
async def get_webhook(
    webhook_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get a specific webhook configuration.
    """
    webhook = db.query(WebhookConfig).filter(WebhookConfig.id == webhook_id).first()

    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found"
        )

    return WebhookConfigResponse.model_validate(webhook)


@router.put("/{webhook_id}", response_model=WebhookConfigResponse)
async def update_webhook(
    webhook_id: int,
    webhook_update: WebhookConfigUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role(["admin"])),
):
    """
    Update webhook configuration.

    Requires admin role.
    """
    webhook = db.query(WebhookConfig).filter(WebhookConfig.id == webhook_id).first()

    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found"
        )

    # Update fields
    update_data = webhook_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(webhook, field, value)

    webhook.updated_at = datetime.now()

    db.commit()
    db.refresh(webhook)

    return WebhookConfigResponse.model_validate(webhook)


@router.delete("/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook(
    webhook_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role(["admin"])),
):
    """
    Delete a webhook configuration.

    Requires admin role.
    """
    webhook = db.query(WebhookConfig).filter(WebhookConfig.id == webhook_id).first()

    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found"
        )

    db.delete(webhook)
    db.commit()

    return None


@router.post("/{webhook_id}/toggle", response_model=WebhookConfigResponse)
async def toggle_webhook(
    webhook_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role(["admin"])),
):
    """
    Toggle webhook active status.

    Requires admin role.
    """
    webhook = db.query(WebhookConfig).filter(WebhookConfig.id == webhook_id).first()

    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found"
        )

    webhook.is_active = not webhook.is_active
    webhook.updated_at = datetime.now()

    db.commit()
    db.refresh(webhook)

    return WebhookConfigResponse.model_validate(webhook)


@router.post("/{webhook_id}/test")
async def test_webhook(
    webhook_id: int,
    test_data: WebhookTestRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role(["admin"])),
):
    """
    Send a test webhook event.

    Requires admin role.
    """
    webhook = db.query(WebhookConfig).filter(WebhookConfig.id == webhook_id).first()

    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found"
        )

    # Import webhook service
    from app.services.webhook_service import WebhookService

    webhook_service = WebhookService(db)

    # Send test webhook in background
    background_tasks.add_task(
        webhook_service.send_webhook,
        webhook_id=webhook.id,
        event_type=test_data.event_type,
        event_data=test_data.event_data or {"test": True, "message": "Test webhook"}
    )

    return {
        "message": "Test webhook queued for delivery",
        "webhook_id": webhook.id,
        "event_type": test_data.event_type
    }


# ========================================
# WEBHOOK LOG ENDPOINTS
# ========================================

@router.get("/{webhook_id}/logs", response_model=dict)
async def get_webhook_logs(
    webhook_id: int,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=200, description="Maximum records to return"),
    success_only: Optional[bool] = Query(None, description="Filter by success status"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get delivery logs for a specific webhook.
    """
    query = db.query(WebhookLog).filter(WebhookLog.webhook_config_id == webhook_id)

    # Apply filters
    if success_only is not None:
        query = query.filter(WebhookLog.success == success_only)
    if event_type:
        query = query.filter(WebhookLog.event_type == event_type)

    # Get total count
    total = query.count()

    # Get paginated results (newest first)
    logs = query.order_by(WebhookLog.attempted_at.desc()).offset(skip).limit(limit).all()

    return {
        "items": [WebhookLogResponse.model_validate(log) for log in logs],
        "total": total,
        "skip": skip,
        "limit": limit,
        "has_more": skip + len(logs) < total,
    }


@router.get("/logs/{log_id}", response_model=WebhookLogResponse)
async def get_webhook_log(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get a specific webhook delivery log.
    """
    log = db.query(WebhookLog).filter(WebhookLog.id == log_id).first()

    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook log not found"
        )

    return WebhookLogResponse.model_validate(log)


@router.post("/logs/{log_id}/retry")
async def retry_webhook(
    log_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role(["admin"])),
):
    """
    Retry a failed webhook delivery.

    Requires admin role.
    """
    log = db.query(WebhookLog).filter(WebhookLog.id == log_id).first()

    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook log not found"
        )

    if log.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot retry successful webhook delivery"
        )

    # Import webhook service
    from app.services.webhook_service import WebhookService

    webhook_service = WebhookService(db)

    # Retry webhook in background
    background_tasks.add_task(
        webhook_service.send_webhook,
        webhook_id=log.webhook_config_id,
        event_type=log.event_type,
        event_data=log.event_data
    )

    return {
        "message": "Webhook retry queued for delivery",
        "log_id": log.id,
        "event_type": log.event_type
    }


# ========================================
# STATISTICS ENDPOINTS
# ========================================

@router.get("/{webhook_id}/stats")
async def get_webhook_stats(
    webhook_id: int,
    days: int = Query(30, ge=1, le=365, description="Days to analyze"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get webhook delivery statistics.
    """
    from datetime import timedelta
    from sqlalchemy import func

    start_date = datetime.now() - timedelta(days=days)

    # Total deliveries
    total_deliveries = db.query(WebhookLog).filter(
        and_(
            WebhookLog.webhook_config_id == webhook_id,
            WebhookLog.attempted_at >= start_date
        )
    ).count()

    # Success count
    success_count = db.query(WebhookLog).filter(
        and_(
            WebhookLog.webhook_config_id == webhook_id,
            WebhookLog.attempted_at >= start_date,
            WebhookLog.success == True
        )
    ).count()

    # Failed count
    failed_count = total_deliveries - success_count

    # Success rate
    success_rate = (success_count / total_deliveries * 100) if total_deliveries > 0 else 0

    # Average response time (for successful deliveries)
    avg_response_time = db.query(
        func.avg(WebhookLog.response_time_ms)
    ).filter(
        and_(
            WebhookLog.webhook_config_id == webhook_id,
            WebhookLog.attempted_at >= start_date,
            WebhookLog.success == True
        )
    ).scalar() or 0

    # Events by type
    events_by_type = db.query(
        WebhookLog.event_type,
        func.count(WebhookLog.id).label('count')
    ).filter(
        and_(
            WebhookLog.webhook_config_id == webhook_id,
            WebhookLog.attempted_at >= start_date
        )
    ).group_by(WebhookLog.event_type).all()

    return {
        "webhook_id": webhook_id,
        "period_days": days,
        "total_deliveries": total_deliveries,
        "success_count": success_count,
        "failed_count": failed_count,
        "success_rate": round(success_rate, 2),
        "avg_response_time_ms": round(avg_response_time, 2),
        "events_by_type": [
            {"event_type": event_type, "count": count}
            for event_type, count in events_by_type
        ]
    }
