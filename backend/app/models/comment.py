"""
Comment Model
Multi-user commenting system for contracts.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class ContractComment(Base):
    """
    Comments on contracts for collaboration and discussion.
    """
    __tablename__ = "contract_comments"

    id = Column(Integer, primary_key=True, index=True)

    # Contract reference
    contract_id = Column(Integer, ForeignKey("kobetsu_keiyakusho.id"), nullable=False, index=True)

    # Comment thread (for replies)
    parent_id = Column(Integer, ForeignKey("contract_comments.id"), nullable=True, index=True)

    # Author
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    user_email = Column(String(255), nullable=False)
    user_name = Column(String(255))

    # Content
    content = Column(Text, nullable=False)

    # Comment type
    comment_type = Column(String(20), default="general")  # 'general', 'approval', 'rejection', 'question'
    is_internal = Column(Boolean, default=True)  # Internal (visible to company) vs external (visible to client)

    # Timestamps
    created_at = Column(DateTime, nullable=False, server_default=func.now(), index=True)
    updated_at = Column(DateTime, onupdate=func.now())
    is_edited = Column(Boolean, default=False)

    # Soft delete
    is_deleted = Column(Boolean, default=False, index=True)
    deleted_at = Column(DateTime)

    # Relationships
    contract = relationship("KobetsuKeiyakusho", backref="comments")
    user = relationship("User", backref="comments")
    parent = relationship("ContractComment", remote_side=[id], backref="replies")

    def __repr__(self):
        return f"<ContractComment {self.id} on contract:{self.contract_id} by {self.user_email}>"
