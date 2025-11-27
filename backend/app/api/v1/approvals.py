"""
Approval Workflow API Router

Endpoints for managing contract approval workflows.
Supports multi-level approvals for compliance.
"""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.kobetsu_keiyakusho import KobetsuKeiyakusho
from app.schemas.approval import (
    ApprovalRequest,
    ApprovalResponse,
    ApprovalAction,
)

router = APIRouter()


# ========================================
# APPROVAL ENDPOINTS
# ========================================

@router.post("/contract/{contract_id}/submit", response_model=dict)
async def submit_for_approval(
    contract_id: int,
    approval_request: ApprovalRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Submit a contract for approval.

    Changes contract status to 'pending_approval'.
    """
    contract = db.query(KobetsuKeiyakusho).filter(
        KobetsuKeiyakusho.id == contract_id
    ).first()

    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract not found"
        )

    # Check if contract can be submitted for approval
    if contract.status not in ["draft", "rejected"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Contract in status '{contract.status}' cannot be submitted for approval"
        )

    # Update contract status
    old_status = contract.status
    contract.status = "pending_approval"
    contract.submitted_for_approval_at = datetime.now()
    contract.submitted_by = current_user["id"]

    db.commit()
    db.refresh(contract)

    # Create audit log
    from app.services.audit_service import AuditService
    audit = AuditService(db)
    audit.log_action(
        entity_type="kobetsu_keiyakusho",
        entity_id=contract.id,
        action="submit_for_approval",
        user_id=current_user["id"],
        user_email=current_user["email"],
        user_name=current_user.get("name"),
        old_value=old_status,
        new_value="pending_approval",
        reason=approval_request.notes or "Submitted for approval"
    )

    # Create comment for submission
    from app.models.comment import ContractComment
    comment = ContractComment(
        contract_id=contract.id,
        user_id=current_user["id"],
        user_email=current_user["email"],
        user_name=current_user.get("name", current_user["email"]),
        content=approval_request.notes or "契約書を承認申請しました",
        comment_type="approval",
        is_internal=True
    )
    db.add(comment)
    db.commit()

    # Trigger webhook for approval request
    from app.services.webhook_service import WebhookService
    webhook_service = WebhookService(db)
    webhook_service.trigger_event(
        event_type="contract.submitted_for_approval",
        event_data={
            "contract_id": contract.id,
            "contract_number": contract.contract_number,
            "submitted_by": current_user["email"],
            "submitted_at": datetime.now().isoformat(),
        }
    )

    return {
        "message": "Contract submitted for approval",
        "contract_id": contract.id,
        "status": contract.status,
        "submitted_at": contract.submitted_for_approval_at
    }


@router.post("/contract/{contract_id}/approve", response_model=dict)
async def approve_contract(
    contract_id: int,
    approval_action: ApprovalAction,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role(["manager", "admin"])),
):
    """
    Approve a contract.

    Changes contract status to 'approved'.
    Requires manager or admin role.
    """
    contract = db.query(KobetsuKeiyakusho).filter(
        KobetsuKeiyakusho.id == contract_id
    ).first()

    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract not found"
        )

    # Check if contract is pending approval
    if contract.status != "pending_approval":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Contract in status '{contract.status}' cannot be approved"
        )

    # Update contract status
    old_status = contract.status
    contract.status = "approved"
    contract.approved_at = datetime.now()
    contract.approved_by = current_user["id"]

    db.commit()
    db.refresh(contract)

    # Create audit log
    from app.services.audit_service import AuditService
    audit = AuditService(db)
    audit.log_action(
        entity_type="kobetsu_keiyakusho",
        entity_id=contract.id,
        action="approve",
        user_id=current_user["id"],
        user_email=current_user["email"],
        user_name=current_user.get("name"),
        old_value=old_status,
        new_value="approved",
        reason=approval_action.notes or "Contract approved"
    )

    # Create comment for approval
    from app.models.comment import ContractComment
    comment = ContractComment(
        contract_id=contract.id,
        user_id=current_user["id"],
        user_email=current_user["email"],
        user_name=current_user.get("name", current_user["email"]),
        content=approval_action.notes or "契約書を承認しました",
        comment_type="approval",
        is_internal=True
    )
    db.add(comment)
    db.commit()

    # Trigger webhook for approval
    from app.services.webhook_service import WebhookService
    webhook_service = WebhookService(db)
    webhook_service.trigger_event(
        event_type="contract.approved",
        event_data={
            "contract_id": contract.id,
            "contract_number": contract.contract_number,
            "approved_by": current_user["email"],
            "approved_at": datetime.now().isoformat(),
        }
    )

    return {
        "message": "Contract approved successfully",
        "contract_id": contract.id,
        "status": contract.status,
        "approved_at": contract.approved_at,
        "approved_by": current_user["email"]
    }


@router.post("/contract/{contract_id}/reject", response_model=dict)
async def reject_contract(
    contract_id: int,
    approval_action: ApprovalAction,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role(["manager", "admin"])),
):
    """
    Reject a contract.

    Changes contract status to 'rejected'.
    Requires manager or admin role.
    Rejection reason is mandatory.
    """
    contract = db.query(KobetsuKeiyakusho).filter(
        KobetsuKeiyakusho.id == contract_id
    ).first()

    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract not found"
        )

    # Check if contract is pending approval
    if contract.status != "pending_approval":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Contract in status '{contract.status}' cannot be rejected"
        )

    # Rejection reason is mandatory
    if not approval_action.notes or not approval_action.notes.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rejection reason is required"
        )

    # Update contract status
    old_status = contract.status
    contract.status = "rejected"
    contract.rejected_at = datetime.now()
    contract.rejected_by = current_user["id"]
    contract.rejection_reason = approval_action.notes

    db.commit()
    db.refresh(contract)

    # Create audit log
    from app.services.audit_service import AuditService
    audit = AuditService(db)
    audit.log_action(
        entity_type="kobetsu_keiyakusho",
        entity_id=contract.id,
        action="reject",
        user_id=current_user["id"],
        user_email=current_user["email"],
        user_name=current_user.get("name"),
        old_value=old_status,
        new_value="rejected",
        reason=approval_action.notes
    )

    # Create comment for rejection
    from app.models.comment import ContractComment
    comment = ContractComment(
        contract_id=contract.id,
        user_id=current_user["id"],
        user_email=current_user["email"],
        user_name=current_user.get("name", current_user["email"]),
        content=f"契約書を却下しました: {approval_action.notes}",
        comment_type="rejection",
        is_internal=True
    )
    db.add(comment)
    db.commit()

    # Trigger webhook for rejection
    from app.services.webhook_service import WebhookService
    webhook_service = WebhookService(db)
    webhook_service.trigger_event(
        event_type="contract.rejected",
        event_data={
            "contract_id": contract.id,
            "contract_number": contract.contract_number,
            "rejected_by": current_user["email"],
            "rejected_at": datetime.now().isoformat(),
            "reason": approval_action.notes
        }
    )

    return {
        "message": "Contract rejected",
        "contract_id": contract.id,
        "status": contract.status,
        "rejected_at": contract.rejected_at,
        "rejected_by": current_user["email"],
        "reason": approval_action.notes
    }


@router.post("/contract/{contract_id}/recall", response_model=dict)
async def recall_approval_request(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Recall a contract from approval workflow.

    Changes contract status back to 'draft'.
    Only the submitter can recall their own submission.
    """
    contract = db.query(KobetsuKeiyakusho).filter(
        KobetsuKeiyakusho.id == contract_id
    ).first()

    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract not found"
        )

    # Check if contract is pending approval
    if contract.status != "pending_approval":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Contract in status '{contract.status}' cannot be recalled"
        )

    # Check if user is the one who submitted
    if contract.submitted_by != current_user["id"]:
        # Allow admins to recall any contract
        if current_user.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only recall contracts you submitted"
            )

    # Update contract status
    old_status = contract.status
    contract.status = "draft"
    contract.submitted_for_approval_at = None
    contract.submitted_by = None

    db.commit()
    db.refresh(contract)

    # Create audit log
    from app.services.audit_service import AuditService
    audit = AuditService(db)
    audit.log_action(
        entity_type="kobetsu_keiyakusho",
        entity_id=contract.id,
        action="recall",
        user_id=current_user["id"],
        user_email=current_user["email"],
        user_name=current_user.get("name"),
        old_value=old_status,
        new_value="draft",
        reason="Approval request recalled"
    )

    # Create comment for recall
    from app.models.comment import ContractComment
    comment = ContractComment(
        contract_id=contract.id,
        user_id=current_user["id"],
        user_email=current_user["email"],
        user_name=current_user.get("name", current_user["email"]),
        content="承認申請を取り下げました",
        comment_type="general",
        is_internal=True
    )
    db.add(comment)
    db.commit()

    return {
        "message": "Approval request recalled",
        "contract_id": contract.id,
        "status": contract.status
    }


# ========================================
# LIST ENDPOINTS
# ========================================

@router.get("/pending", response_model=dict)
async def get_pending_approvals(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum records to return"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role(["manager", "admin"])),
):
    """
    Get list of contracts pending approval.

    Requires manager or admin role.
    """
    query = db.query(KobetsuKeiyakusho).filter(
        KobetsuKeiyakusho.status == "pending_approval"
    )

    # Get total count
    total = query.count()

    # Get paginated results (oldest first - FIFO)
    contracts = query.order_by(
        KobetsuKeiyakusho.submitted_for_approval_at.asc()
    ).offset(skip).limit(limit).all()

    from app.schemas.kobetsu_keiyakusho import KobetsuKeiyakushoList

    return {
        "items": [KobetsuKeiyakushoList.model_validate(c) for c in contracts],
        "total": total,
        "skip": skip,
        "limit": limit,
        "has_more": skip + len(contracts) < total,
    }


@router.get("/history", response_model=dict)
async def get_approval_history(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum records to return"),
    status: Optional[str] = Query(None, description="Filter by status (approved/rejected)"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role(["manager", "admin"])),
):
    """
    Get approval history.

    Returns contracts that have been approved or rejected.
    Requires manager or admin role.
    """
    query = db.query(KobetsuKeiyakusho)

    if status == "approved":
        query = query.filter(KobetsuKeiyakusho.status == "approved")
    elif status == "rejected":
        query = query.filter(KobetsuKeiyakusho.status == "rejected")
    else:
        query = query.filter(
            or_(
                KobetsuKeiyakusho.status == "approved",
                KobetsuKeiyakusho.status == "rejected"
            )
        )

    # Get total count
    total = query.count()

    # Get paginated results (newest first)
    contracts = query.order_by(
        KobetsuKeiyakusho.approved_at.desc().nullslast(),
        KobetsuKeiyakusho.rejected_at.desc().nullslast()
    ).offset(skip).limit(limit).all()

    from app.schemas.kobetsu_keiyakusho import KobetsuKeiyakushoList

    return {
        "items": [KobetsuKeiyakushoList.model_validate(c) for c in contracts],
        "total": total,
        "skip": skip,
        "limit": limit,
        "has_more": skip + len(contracts) < total,
    }


# ========================================
# STATISTICS ENDPOINTS
# ========================================

@router.get("/stats")
async def get_approval_stats(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role(["manager", "admin"])),
):
    """
    Get approval statistics.

    Requires manager or admin role.
    """
    from sqlalchemy import func
    from datetime import timedelta

    # Pending approvals
    pending_count = db.query(KobetsuKeiyakusho).filter(
        KobetsuKeiyakusho.status == "pending_approval"
    ).count()

    # Approved this month
    first_day_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    approved_this_month = db.query(KobetsuKeiyakusho).filter(
        and_(
            KobetsuKeiyakusho.status == "approved",
            KobetsuKeiyakusho.approved_at >= first_day_of_month
        )
    ).count()

    # Rejected this month
    rejected_this_month = db.query(KobetsuKeiyakusho).filter(
        and_(
            KobetsuKeiyakusho.status == "rejected",
            KobetsuKeiyakusho.rejected_at >= first_day_of_month
        )
    ).count()

    # Average approval time (in hours)
    avg_approval_time_query = db.query(
        func.avg(
            func.extract('epoch', KobetsuKeiyakusho.approved_at - KobetsuKeiyakusho.submitted_for_approval_at) / 3600
        )
    ).filter(
        and_(
            KobetsuKeiyakusho.status == "approved",
            KobetsuKeiyakusho.approved_at >= first_day_of_month
        )
    ).scalar()

    avg_approval_time_hours = round(avg_approval_time_query or 0, 2)

    # Oldest pending approval
    oldest_pending = db.query(KobetsuKeiyakusho).filter(
        KobetsuKeiyakusho.status == "pending_approval"
    ).order_by(KobetsuKeiyakusho.submitted_for_approval_at.asc()).first()

    oldest_pending_days = None
    if oldest_pending and oldest_pending.submitted_for_approval_at:
        delta = datetime.now() - oldest_pending.submitted_for_approval_at
        oldest_pending_days = delta.days

    return {
        "pending_count": pending_count,
        "approved_this_month": approved_this_month,
        "rejected_this_month": rejected_this_month,
        "avg_approval_time_hours": avg_approval_time_hours,
        "oldest_pending_days": oldest_pending_days,
        "oldest_pending_contract": oldest_pending.contract_number if oldest_pending else None
    }
