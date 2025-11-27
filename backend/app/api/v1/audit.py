"""
Audit Log API Router

Endpoints for viewing audit logs and contract version history.
Required for compliance and legal traceability.
"""
from datetime import datetime, date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.audit_log import AuditLog, ContractVersion
from app.schemas.audit import (
    AuditLogResponse,
    ContractVersionResponse,
    AuditLogFilter,
)

router = APIRouter()


# ========================================
# AUDIT LOG ENDPOINTS
# ========================================

@router.get("/logs", response_model=dict)
async def get_audit_logs(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=200, description="Maximum records to return"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    entity_id: Optional[int] = Query(None, description="Filter by entity ID"),
    action: Optional[str] = Query(None, description="Filter by action"),
    user_id: Optional[int] = Query(None, description="Filter by user"),
    start_date: Optional[date] = Query(None, description="Filter from date"),
    end_date: Optional[date] = Query(None, description="Filter to date"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get paginated audit logs with filtering.

    Returns audit trail of all system changes for compliance.
    """
    query = db.query(AuditLog)

    # Apply filters
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    if entity_id:
        query = query.filter(AuditLog.entity_id == entity_id)
    if action:
        query = query.filter(AuditLog.action == action)
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if start_date:
        query = query.filter(AuditLog.timestamp >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.filter(AuditLog.timestamp <= datetime.combine(end_date, datetime.max.time()))

    # Get total count
    total = query.count()

    # Get paginated results (newest first)
    logs = query.order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit).all()

    return {
        "items": [AuditLogResponse.model_validate(log) for log in logs],
        "total": total,
        "skip": skip,
        "limit": limit,
        "has_more": skip + len(logs) < total,
    }


@router.get("/logs/{log_id}", response_model=AuditLogResponse)
async def get_audit_log(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get a specific audit log entry by ID.
    """
    log = db.query(AuditLog).filter(AuditLog.id == log_id).first()

    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit log not found"
        )

    return AuditLogResponse.model_validate(log)


@router.get("/logs/contract/{contract_id}", response_model=List[AuditLogResponse])
async def get_contract_audit_logs(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get all audit logs for a specific contract.
    """
    logs = db.query(AuditLog).filter(
        and_(
            AuditLog.entity_type == "kobetsu_keiyakusho",
            AuditLog.entity_id == contract_id
        )
    ).order_by(AuditLog.timestamp.desc()).all()

    return [AuditLogResponse.model_validate(log) for log in logs]


# ========================================
# CONTRACT VERSION ENDPOINTS
# ========================================

@router.get("/versions/contract/{contract_id}", response_model=List[ContractVersionResponse])
async def get_contract_versions(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get all versions of a specific contract.

    Returns complete version history for comparison and rollback.
    """
    versions = db.query(ContractVersion).filter(
        ContractVersion.contract_id == contract_id
    ).order_by(ContractVersion.version_number.desc()).all()

    return [ContractVersionResponse.model_validate(v) for v in versions]


@router.get("/versions/{version_id}", response_model=ContractVersionResponse)
async def get_contract_version(
    version_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get a specific contract version by ID.
    """
    version = db.query(ContractVersion).filter(ContractVersion.id == version_id).first()

    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract version not found"
        )

    return ContractVersionResponse.model_validate(version)


@router.get("/versions/{version_id}/compare/{compare_version_id}")
async def compare_versions(
    version_id: int,
    compare_version_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Compare two contract versions and show differences.
    """
    version1 = db.query(ContractVersion).filter(ContractVersion.id == version_id).first()
    version2 = db.query(ContractVersion).filter(ContractVersion.id == compare_version_id).first()

    if not version1 or not version2:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or both versions not found"
        )

    if version1.contract_id != version2.contract_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Versions belong to different contracts"
        )

    # Simple diff - compare JSON data
    data1 = version1.contract_data
    data2 = version2.contract_data

    differences = {}
    all_keys = set(data1.keys()) | set(data2.keys())

    for key in all_keys:
        val1 = data1.get(key)
        val2 = data2.get(key)
        if val1 != val2:
            differences[key] = {
                "old_value": val1,
                "new_value": val2
            }

    return {
        "version1": ContractVersionResponse.model_validate(version1),
        "version2": ContractVersionResponse.model_validate(version2),
        "differences": differences,
        "diff_count": len(differences)
    }


# ========================================
# STATISTICS ENDPOINTS
# ========================================

@router.get("/stats")
async def get_audit_stats(
    days: int = Query(30, ge=1, le=365, description="Days to analyze"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get audit statistics for the specified period.
    """
    from datetime import timedelta

    start_date = datetime.now() - timedelta(days=days)

    # Total actions
    total_actions = db.query(AuditLog).filter(
        AuditLog.timestamp >= start_date
    ).count()

    # Actions by type
    from sqlalchemy import func
    actions_by_type = db.query(
        AuditLog.action,
        func.count(AuditLog.id).label('count')
    ).filter(
        AuditLog.timestamp >= start_date
    ).group_by(AuditLog.action).all()

    # Most active users
    active_users = db.query(
        AuditLog.user_email,
        AuditLog.user_name,
        func.count(AuditLog.id).label('action_count')
    ).filter(
        AuditLog.timestamp >= start_date
    ).group_by(AuditLog.user_email, AuditLog.user_name).order_by(
        func.count(AuditLog.id).desc()
    ).limit(10).all()

    # Entity types modified
    entity_types = db.query(
        AuditLog.entity_type,
        func.count(AuditLog.id).label('count')
    ).filter(
        AuditLog.timestamp >= start_date
    ).group_by(AuditLog.entity_type).all()

    return {
        "period_days": days,
        "total_actions": total_actions,
        "actions_by_type": [
            {"action": action, "count": count}
            for action, count in actions_by_type
        ],
        "active_users": [
            {"email": email, "name": name, "action_count": count}
            for email, name, count in active_users
        ],
        "entity_types": [
            {"entity_type": entity_type, "count": count}
            for entity_type, count in entity_types
        ]
    }
