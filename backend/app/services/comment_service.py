"""
Comment Service
Manages multi-user commenting system for contracts.
"""
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

from app.models.comment import ContractComment


class CommentService:
    """Service for managing contract comments."""

    def __init__(self, db: Session):
        self.db = db

    def create_comment(
        self,
        contract_id: int,
        content: str,
        user_id: int,
        user_email: str,
        user_name: Optional[str] = None,
        parent_id: Optional[int] = None,
        comment_type: str = "general",
        is_internal: bool = True
    ) -> ContractComment:
        """
        Create a new comment on a contract.

        Args:
            contract_id: ID of contract
            content: Comment content
            user_id: ID of user posting comment
            user_email: Email of user
            user_name: Name of user (optional)
            parent_id: ID of parent comment (for replies)
            comment_type: Type ('general', 'approval', 'rejection', 'question')
            is_internal: Internal (visible to company) vs external (visible to client)

        Returns:
            Created ContractComment
        """
        comment = ContractComment(
            contract_id=contract_id,
            content=content,
            user_id=user_id,
            user_email=user_email,
            user_name=user_name,
            parent_id=parent_id,
            comment_type=comment_type,
            is_internal=is_internal,
            created_at=datetime.now(timezone.utc)
        )

        self.db.add(comment)
        self.db.commit()
        self.db.refresh(comment)

        return comment

    def get_contract_comments(
        self,
        contract_id: int,
        include_deleted: bool = False,
        is_internal: Optional[bool] = None
    ) -> List[ContractComment]:
        """
        Get all comments for a contract.

        Args:
            contract_id: ID of contract
            include_deleted: Include soft-deleted comments
            is_internal: Filter by internal/external (None = all)

        Returns:
            List of ContractComment entries, most recent first
        """
        query = self.db.query(ContractComment).filter(
            ContractComment.contract_id == contract_id
        )

        if not include_deleted:
            query = query.filter(ContractComment.is_deleted == False)

        if is_internal is not None:
            query = query.filter(ContractComment.is_internal == is_internal)

        return query.order_by(desc(ContractComment.created_at)).all()

    def get_comment(self, comment_id: int) -> Optional[ContractComment]:
        """Get a specific comment by ID."""
        return self.db.query(ContractComment).filter(
            ContractComment.id == comment_id,
            ContractComment.is_deleted == False
        ).first()

    def get_comment_thread(
        self,
        parent_id: int
    ) -> List[ContractComment]:
        """
        Get all replies to a comment (thread).

        Args:
            parent_id: ID of parent comment

        Returns:
            List of replies
        """
        return (
            self.db.query(ContractComment)
            .filter(
                ContractComment.parent_id == parent_id,
                ContractComment.is_deleted == False
            )
            .order_by(ContractComment.created_at)
            .all()
        )

    def update_comment(
        self,
        comment_id: int,
        content: str,
        user_id: int
    ) -> Optional[ContractComment]:
        """
        Update a comment's content.

        Args:
            comment_id: ID of comment to update
            content: New content
            user_id: ID of user updating (must match original user)

        Returns:
            Updated ContractComment or None
        """
        comment = self.get_comment(comment_id)
        if not comment:
            return None

        # Only allow user who created comment to edit it
        if comment.user_id != user_id:
            raise PermissionError("Only the comment author can edit it")

        comment.content = content
        comment.updated_at = datetime.now(timezone.utc)
        comment.is_edited = True

        self.db.commit()
        self.db.refresh(comment)

        return comment

    def delete_comment(
        self,
        comment_id: int,
        user_id: int,
        hard_delete: bool = False
    ) -> bool:
        """
        Delete a comment (soft delete by default).

        Args:
            comment_id: ID of comment to delete
            user_id: ID of user deleting
            hard_delete: If True, permanently delete (not recommended)

        Returns:
            True if deleted, False if not found
        """
        comment = self.get_comment(comment_id)
        if not comment:
            return False

        # Only allow user who created comment to delete it
        # (or implement admin permission check here)
        if comment.user_id != user_id:
            raise PermissionError("Only the comment author can delete it")

        if hard_delete:
            self.db.delete(comment)
        else:
            comment.is_deleted = True
            comment.deleted_at = datetime.now(timezone.utc)

        self.db.commit()

        return True

    def get_user_comments(
        self,
        user_id: int,
        limit: int = 50
    ) -> List[ContractComment]:
        """
        Get all comments by a specific user.

        Args:
            user_id: ID of user
            limit: Maximum number of comments

        Returns:
            List of comments by user
        """
        return (
            self.db.query(ContractComment)
            .filter(
                ContractComment.user_id == user_id,
                ContractComment.is_deleted == False
            )
            .order_by(desc(ContractComment.created_at))
            .limit(limit)
            .all()
        )

    def get_approval_comments(
        self,
        contract_id: int
    ) -> List[ContractComment]:
        """
        Get all approval/rejection comments for a contract.

        Args:
            contract_id: ID of contract

        Returns:
            List of approval-related comments
        """
        return (
            self.db.query(ContractComment)
            .filter(
                ContractComment.contract_id == contract_id,
                ContractComment.comment_type.in_(['approval', 'rejection']),
                ContractComment.is_deleted == False
            )
            .order_by(ContractComment.created_at)
            .all()
        )

    def count_comments(
        self,
        contract_id: int,
        include_deleted: bool = False
    ) -> int:
        """
        Count comments on a contract.

        Args:
            contract_id: ID of contract
            include_deleted: Include soft-deleted comments

        Returns:
            Number of comments
        """
        query = self.db.query(ContractComment).filter(
            ContractComment.contract_id == contract_id
        )

        if not include_deleted:
            query = query.filter(ContractComment.is_deleted == False)

        return query.count()
