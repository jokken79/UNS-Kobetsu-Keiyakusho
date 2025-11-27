"""
Comments API Router

Endpoints for managing contract comments and discussions.
Multi-user commenting system for collaboration.
"""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.comment import ContractComment
from app.schemas.comment import (
    CommentCreate,
    CommentUpdate,
    CommentResponse,
)

router = APIRouter()


# ========================================
# COMMENT ENDPOINTS
# ========================================

@router.get("/contract/{contract_id}", response_model=List[CommentResponse])
async def get_contract_comments(
    contract_id: int,
    include_deleted: bool = Query(False, description="Include deleted comments"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get all comments for a specific contract.

    Returns comments in threaded structure (parent comments with replies).
    """
    query = db.query(ContractComment).filter(
        ContractComment.contract_id == contract_id
    )

    if not include_deleted:
        query = query.filter(ContractComment.is_deleted == False)

    comments = query.order_by(ContractComment.created_at.asc()).all()

    return [CommentResponse.model_validate(c) for c in comments]


@router.post("/", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(
    comment: CommentCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Create a new comment on a contract.

    Supports both top-level comments and replies (using parent_id).
    """
    # Verify contract exists
    from app.models.kobetsu_keiyakusho import KobetsuKeiyakusho
    contract = db.query(KobetsuKeiyakusho).filter(
        KobetsuKeiyakusho.id == comment.contract_id
    ).first()

    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract not found"
        )

    # If replying to another comment, verify parent exists
    if comment.parent_id:
        parent = db.query(ContractComment).filter(
            ContractComment.id == comment.parent_id
        ).first()

        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent comment not found"
            )

        if parent.contract_id != comment.contract_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Parent comment belongs to different contract"
            )

    # Create comment
    new_comment = ContractComment(
        contract_id=comment.contract_id,
        parent_id=comment.parent_id,
        user_id=current_user["id"],
        user_email=current_user["email"],
        user_name=current_user.get("name", current_user["email"]),
        content=comment.content,
        comment_type=comment.comment_type,
        is_internal=comment.is_internal,
    )

    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)

    # Create audit log
    from app.services.audit_service import AuditService
    audit = AuditService(db)
    audit.log_action(
        entity_type="contract_comment",
        entity_id=new_comment.id,
        action="create",
        user_id=current_user["id"],
        user_email=current_user["email"],
        user_name=current_user.get("name"),
        new_value=comment.content[:200],  # First 200 chars
        reason=f"Comment added to contract {comment.contract_id}"
    )

    return CommentResponse.model_validate(new_comment)


@router.get("/{comment_id}", response_model=CommentResponse)
async def get_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get a specific comment by ID.
    """
    comment = db.query(ContractComment).filter(ContractComment.id == comment_id).first()

    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )

    if comment.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Comment has been deleted"
        )

    return CommentResponse.model_validate(comment)


@router.put("/{comment_id}", response_model=CommentResponse)
async def update_comment(
    comment_id: int,
    comment_update: CommentUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Update a comment.

    Only the comment author can update their own comments.
    """
    comment = db.query(ContractComment).filter(ContractComment.id == comment_id).first()

    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )

    if comment.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Comment has been deleted"
        )

    # Check ownership
    if comment.user_id != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only edit your own comments"
        )

    # Store old content for audit
    old_content = comment.content

    # Update comment
    update_data = comment_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(comment, field, value)

    comment.updated_at = datetime.now()
    comment.is_edited = True

    db.commit()
    db.refresh(comment)

    # Create audit log
    from app.services.audit_service import AuditService
    audit = AuditService(db)
    audit.log_action(
        entity_type="contract_comment",
        entity_id=comment.id,
        action="update",
        user_id=current_user["id"],
        user_email=current_user["email"],
        user_name=current_user.get("name"),
        old_value=old_content[:200],
        new_value=comment.content[:200],
        reason="Comment edited"
    )

    return CommentResponse.model_validate(comment)


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: int,
    hard_delete: bool = Query(False, description="Permanently delete (admin only)"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Delete a comment (soft delete by default).

    Only the comment author or admins can delete comments.
    Hard delete requires admin role.
    """
    comment = db.query(ContractComment).filter(ContractComment.id == comment_id).first()

    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )

    if comment.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Comment already deleted"
        )

    # Check ownership or admin
    is_admin = current_user.get("role") == "admin"
    is_owner = comment.user_id == current_user["id"]

    if not (is_owner or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own comments"
        )

    if hard_delete:
        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Hard delete requires admin role"
            )

        # Permanently delete
        db.delete(comment)
    else:
        # Soft delete
        comment.is_deleted = True
        comment.deleted_at = datetime.now()

    db.commit()

    # Create audit log
    from app.services.audit_service import AuditService
    audit = AuditService(db)
    audit.log_action(
        entity_type="contract_comment",
        entity_id=comment.id,
        action="delete" if hard_delete else "soft_delete",
        user_id=current_user["id"],
        user_email=current_user["email"],
        user_name=current_user.get("name"),
        old_value=comment.content[:200],
        reason="Comment deleted"
    )

    return None


@router.post("/{comment_id}/restore", response_model=CommentResponse)
async def restore_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Restore a soft-deleted comment.

    Requires admin role or comment ownership.
    """
    comment = db.query(ContractComment).filter(ContractComment.id == comment_id).first()

    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )

    if not comment.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Comment is not deleted"
        )

    # Check ownership or admin
    is_admin = current_user.get("role") == "admin"
    is_owner = comment.user_id == current_user["id"]

    if not (is_owner or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only restore your own comments"
        )

    # Restore comment
    comment.is_deleted = False
    comment.deleted_at = None

    db.commit()
    db.refresh(comment)

    # Create audit log
    from app.services.audit_service import AuditService
    audit = AuditService(db)
    audit.log_action(
        entity_type="contract_comment",
        entity_id=comment.id,
        action="restore",
        user_id=current_user["id"],
        user_email=current_user["email"],
        user_name=current_user.get("name"),
        reason="Comment restored"
    )

    return CommentResponse.model_validate(comment)


# ========================================
# STATISTICS ENDPOINTS
# ========================================

@router.get("/contract/{contract_id}/stats")
async def get_comment_stats(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get comment statistics for a contract.
    """
    from sqlalchemy import func

    # Total comments (excluding deleted)
    total_comments = db.query(ContractComment).filter(
        and_(
            ContractComment.contract_id == contract_id,
            ContractComment.is_deleted == False
        )
    ).count()

    # Comments by type
    comments_by_type = db.query(
        ContractComment.comment_type,
        func.count(ContractComment.id).label('count')
    ).filter(
        and_(
            ContractComment.contract_id == contract_id,
            ContractComment.is_deleted == False
        )
    ).group_by(ContractComment.comment_type).all()

    # Top commenters
    top_commenters = db.query(
        ContractComment.user_email,
        ContractComment.user_name,
        func.count(ContractComment.id).label('comment_count')
    ).filter(
        and_(
            ContractComment.contract_id == contract_id,
            ContractComment.is_deleted == False
        )
    ).group_by(ContractComment.user_email, ContractComment.user_name).order_by(
        func.count(ContractComment.id).desc()
    ).limit(5).all()

    # Recent activity (last 7 days)
    from datetime import timedelta
    recent_date = datetime.now() - timedelta(days=7)
    recent_comments = db.query(ContractComment).filter(
        and_(
            ContractComment.contract_id == contract_id,
            ContractComment.is_deleted == False,
            ContractComment.created_at >= recent_date
        )
    ).count()

    return {
        "contract_id": contract_id,
        "total_comments": total_comments,
        "recent_comments_7days": recent_comments,
        "comments_by_type": [
            {"comment_type": comment_type, "count": count}
            for comment_type, count in comments_by_type
        ],
        "top_commenters": [
            {"email": email, "name": name, "comment_count": count}
            for email, name, count in top_commenters
        ]
    }
