"""
Audit Log Service
Tracks all changes to contracts and entities for compliance.
"""
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.audit_log import AuditLog, ContractVersion
from app.models.kobetsu_keiyakusho import KobetsuKeiyakusho


class AuditService:
    """Service for audit logging and contract versioning."""

    def __init__(self, db: Session):
        self.db = db

    def log_change(
        self,
        entity_type: str,
        entity_id: int,
        action: str,
        user_id: int,
        user_email: str,
        user_name: Optional[str] = None,
        field_name: Optional[str] = None,
        old_value: Optional[str] = None,
        new_value: Optional[str] = None,
        full_snapshot: Optional[Dict] = None,
        reason: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """
        Log a change to an entity.

        Args:
            entity_type: Type of entity (e.g., 'kobetsu_keiyakusho', 'employee')
            entity_id: ID of the entity
            action: Action performed ('create', 'update', 'delete', 'approve', 'reject')
            user_id: ID of user who made the change
            user_email: Email of user
            user_name: Name of user (optional)
            field_name: Name of field changed (optional)
            old_value: Previous value (optional)
            new_value: New value (optional)
            full_snapshot: Complete state snapshot (optional)
            reason: Reason for change (optional but recommended)
            ip_address: IP address of request
            user_agent: User agent string

        Returns:
            Created AuditLog entry
        """
        audit_log = AuditLog(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            user_id=user_id,
            user_email=user_email,
            user_name=user_name,
            field_name=field_name,
            old_value=str(old_value) if old_value is not None else None,
            new_value=str(new_value) if new_value is not None else None,
            full_snapshot=full_snapshot,
            reason=reason,
            ip_address=ip_address,
            user_agent=user_agent,
            timestamp=datetime.now(timezone.utc)
        )

        self.db.add(audit_log)
        self.db.commit()
        self.db.refresh(audit_log)

        return audit_log

    def get_entity_history(
        self,
        entity_type: str,
        entity_id: int,
        limit: int = 100
    ) -> List[AuditLog]:
        """
        Get complete history of changes for an entity.

        Args:
            entity_type: Type of entity
            entity_id: ID of entity
            limit: Maximum number of records to return

        Returns:
            List of AuditLog entries, most recent first
        """
        return (
            self.db.query(AuditLog)
            .filter(
                AuditLog.entity_type == entity_type,
                AuditLog.entity_id == entity_id
            )
            .order_by(desc(AuditLog.timestamp))
            .limit(limit)
            .all()
        )

    def get_user_activity(
        self,
        user_id: int,
        limit: int = 100
    ) -> List[AuditLog]:
        """
        Get all activity by a specific user.

        Args:
            user_id: ID of user
            limit: Maximum number of records

        Returns:
            List of AuditLog entries
        """
        return (
            self.db.query(AuditLog)
            .filter(AuditLog.user_id == user_id)
            .order_by(desc(AuditLog.timestamp))
            .limit(limit)
            .all()
        )

    def create_contract_version(
        self,
        contract_id: int,
        contract_data: Dict[str, Any],
        change_summary: str,
        change_type: str,
        created_by: int,
        created_by_email: str,
        status: str
    ) -> ContractVersion:
        """
        Create a new version of a contract.

        Args:
            contract_id: ID of contract
            contract_data: Complete contract data as dict
            change_summary: Summary of what changed
            change_type: Type of change ('draft', 'amendment', 'renewal', 'correction')
            created_by: User ID who created this version
            created_by_email: Email of user
            status: Status at this version

        Returns:
            Created ContractVersion
        """
        # Get current version number
        latest_version = (
            self.db.query(ContractVersion)
            .filter(ContractVersion.contract_id == contract_id)
            .order_by(desc(ContractVersion.version_number))
            .first()
        )

        version_number = (latest_version.version_number + 1) if latest_version else 1

        version = ContractVersion(
            contract_id=contract_id,
            version_number=version_number,
            contract_data=contract_data,
            change_summary=change_summary,
            change_type=change_type,
            created_by=created_by,
            created_by_email=created_by_email,
            status=status,
            version_date=datetime.now(timezone.utc)
        )

        self.db.add(version)
        self.db.commit()
        self.db.refresh(version)

        return version

    def get_contract_versions(
        self,
        contract_id: int
    ) -> List[ContractVersion]:
        """
        Get all versions of a contract.

        Args:
            contract_id: ID of contract

        Returns:
            List of ContractVersion entries, most recent first
        """
        return (
            self.db.query(ContractVersion)
            .filter(ContractVersion.contract_id == contract_id)
            .order_by(desc(ContractVersion.version_number))
            .all()
        )

    def get_contract_version(
        self,
        contract_id: int,
        version_number: int
    ) -> Optional[ContractVersion]:
        """
        Get a specific version of a contract.

        Args:
            contract_id: ID of contract
            version_number: Version number to retrieve

        Returns:
            ContractVersion or None
        """
        return (
            self.db.query(ContractVersion)
            .filter(
                ContractVersion.contract_id == contract_id,
                ContractVersion.version_number == version_number
            )
            .first()
        )

    def compare_versions(
        self,
        contract_id: int,
        version1: int,
        version2: int
    ) -> Dict[str, Any]:
        """
        Compare two versions of a contract.

        Args:
            contract_id: ID of contract
            version1: First version number
            version2: Second version number

        Returns:
            Dict with differences between versions
        """
        v1 = self.get_contract_version(contract_id, version1)
        v2 = self.get_contract_version(contract_id, version2)

        if not v1 or not v2:
            return {"error": "Version not found"}

        differences = {}
        data1 = v1.contract_data
        data2 = v2.contract_data

        # Find all keys in both versions
        all_keys = set(data1.keys()) | set(data2.keys())

        for key in all_keys:
            val1 = data1.get(key)
            val2 = data2.get(key)

            if val1 != val2:
                differences[key] = {
                    f"version_{version1}": val1,
                    f"version_{version2}": val2
                }

        return {
            "contract_id": contract_id,
            "version1": {
                "number": version1,
                "date": v1.version_date.isoformat(),
                "created_by": v1.created_by_email,
                "summary": v1.change_summary
            },
            "version2": {
                "number": version2,
                "date": v2.version_date.isoformat(),
                "created_by": v2.created_by_email,
                "summary": v2.change_summary
            },
            "differences": differences,
            "total_changes": len(differences)
        }
