"""
Comment Schemas

Pydantic models for contract comments.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, field_validator


class CommentBase(BaseModel):
    """Base comment schema."""
    content: str
    comment_type: str = "general"
    is_internal: bool = True

    @field_validator('comment_type')
    @classmethod
    def validate_comment_type(cls, v):
        """Validate comment type."""
        valid_types = ["general", "approval", "rejection", "question"]
        if v not in valid_types:
            raise ValueError(f"Comment type must be one of: {', '.join(valid_types)}")
        return v


class CommentCreate(CommentBase):
    """Schema for creating a comment."""
    contract_id: int
    parent_id: Optional[int] = None


class CommentUpdate(BaseModel):
    """Schema for updating a comment."""
    content: Optional[str] = None
    comment_type: Optional[str] = None
    is_internal: Optional[bool] = None


class CommentResponse(CommentBase):
    """Comment response schema."""
    id: int
    contract_id: int
    parent_id: Optional[int] = None
    user_id: int
    user_email: str
    user_name: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_edited: bool = False
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class CommentWithReplies(CommentResponse):
    """Comment with nested replies."""
    replies: list['CommentWithReplies'] = []

    model_config = ConfigDict(from_attributes=True)
