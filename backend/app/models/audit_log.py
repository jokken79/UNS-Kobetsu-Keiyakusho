"""
Audit Log Model
Tracks all changes to contracts for compliance and auditing.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class AuditLog(Base):
    """
    Audit log for tracking all changes to contracts.
    Required for compliance audits and legal traceability.
    """
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)

    # What was changed
    entity_type = Column(String(50), nullable=False, index=True)  # 'kobetsu_keiyakusho', 'employee', etc.
    entity_id = Column(Integer, nullable=False, index=True)
    action = Column(String(20), nullable=False, index=True)  # 'create', 'update', 'delete', 'approve', 'reject'

    # Who made the change
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    user_email = Column(String(255), nullable=False)  # Denormalized for quick access
    user_name = Column(String(255))

    # When
    timestamp = Column(DateTime, nullable=False, server_default=func.now(), index=True)

    # Changes detail
    field_name = Column(String(100))  # Which field was changed
    old_value = Column(Text)  # Previous value (as JSON string if complex)
    new_value = Column(Text)  # New value (as JSON string if complex)

    # Full snapshot (for critical changes)
    full_snapshot = Column(JSON)  # Complete state after change

    # Context
    reason = Column(Text)  # Why the change was made (optional but recommended)
    ip_address = Column(String(45))  # IPv4 or IPv6
    user_agent = Column(String(500))  # Browser/device info

    # Relationships
    user = relationship("User", backref="audit_logs")

    def __repr__(self):
        return f"<AuditLog {self.action} on {self.entity_type}:{self.entity_id} by {self.user_email}>"


class ContractVersion(Base):
    """
    Contract version history.
    Stores complete snapshots of contracts for rollback and comparison.
    """
    __tablename__ = "contract_versions"

    id = Column(Integer, primary_key=True, index=True)

    # Contract reference
    contract_id = Column(Integer, ForeignKey("kobetsu_keiyakusho.id"), nullable=False, index=True)

    # Version info
    version_number = Column(Integer, nullable=False)  # 1, 2, 3, ...
    version_date = Column(DateTime, nullable=False, server_default=func.now())

    # Who created this version
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_by_email = Column(String(255), nullable=False)

    # Complete contract snapshot (JSON)
    contract_data = Column(JSON, nullable=False)

    # Change summary
    change_summary = Column(Text)  # Human-readable summary of what changed
    change_type = Column(String(50))  # 'draft', 'amendment', 'renewal', 'correction'

    # Status at this version
    status = Column(String(20), nullable=False)

    # Relationships
    contract = relationship("KobetsuKeiyakusho", backref="versions")
    user = relationship("User", foreign_keys=[created_by])

    class Config:
        from_attributes = True

    def __repr__(self):
        return f"<ContractVersion v{self.version_number} of contract:{self.contract_id}>"
