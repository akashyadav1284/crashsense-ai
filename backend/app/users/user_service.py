"""
User Management and Security Audit Service with Role-Based Access Control (RBAC).
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from backend.app.users.schemas import (
    UserProfile,
    UserRole,
    AccountStatus,
    UserSession,
    SecurityAuditLog,
    UpdateProfileRequest,
)


class UserManager:
    """Manages user profiles, role enforcement, active sessions, and security audit logs."""

    _instance: Optional["UserManager"] = None

    def __init__(self):
        self.users: Dict[str, UserProfile] = {}
        self.sessions: Dict[str, List[UserSession]] = {}
        self.audit_logs: List[SecurityAuditLog] = []
        self._init_default_users()

    @classmethod
    def get_instance(cls) -> "UserManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _init_default_users(self):
        """Seed initial system users and administrative accounts."""
        u_admin = UserProfile(
            user_id="usr_admin_01",
            email="admin@crashsense.ai",
            display_name="System Administrator",
            role=UserRole.SUPER_ADMIN,
            status=AccountStatus.ACTIVE,
            preferences={"theme": "dark", "notifications_enabled": True}
        )
        u_researcher = UserProfile(
            user_id="default_researcher",
            email="researcher@crashsense.ai",
            display_name="Lead Quantitative Researcher",
            role=UserRole.USER,
            status=AccountStatus.ACTIVE,
            preferences={"theme": "dark", "notifications_enabled": True}
        )
        self.users[u_admin.user_id] = u_admin
        self.users[u_researcher.user_id] = u_researcher

    def get_user(self, user_id: str) -> Optional[UserProfile]:
        return self.users.get(user_id)

    def list_users(self) -> List[UserProfile]:
        return sorted(list(self.users.values()), key=lambda u: u.created_at, reverse=True)

    def update_profile(self, user_id: str, req: UpdateProfileRequest) -> Optional[UserProfile]:
        u = self.users.get(user_id)
        if not u:
            return None
        if req.display_name:
            u.display_name = req.display_name
        if req.avatar_url:
            u.avatar_url = req.avatar_url
        if req.preferences is not None:
            u.preferences.update(req.preferences)
        return u

    def update_user_status(self, actor_user_id: str, target_user_id: str, new_status: AccountStatus, reason: str = "") -> Optional[UserProfile]:
        """Admin action: update account status (ACTIVE, SUSPENDED, DISABLED)."""
        actor = self.users.get(actor_user_id)
        if not actor or actor.role not in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
            raise PermissionError("Administrative privileges required to update user status.")

        target = self.users.get(target_user_id)
        if not target:
            return None

        # Prevent non-super admins from modifying super admins
        if target.role == UserRole.SUPER_ADMIN and actor.role != UserRole.SUPER_ADMIN:
            raise PermissionError("Cannot modify SUPER_ADMIN status.")

        target.status = new_status
        self.log_security_event(
            actor_user_id=actor_user_id,
            actor_role=actor.role,
            action="ACCOUNT_STATUS_CHANGE",
            target_resource=target_user_id,
            outcome="SUCCESS",
            metadata={"new_status": new_status.value, "reason": reason}
        )
        return target

    def log_security_event(
        self,
        actor_user_id: str,
        actor_role: UserRole,
        action: str,
        target_resource: str,
        outcome: str = "SUCCESS",
        ip_address: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> SecurityAuditLog:
        """Record immutable security audit log."""
        log_entry = SecurityAuditLog(
            log_id=f"audit_{uuid.uuid4().hex[:10]}",
            actor_user_id=actor_user_id,
            actor_role=actor_role,
            action=action,
            target_resource=target_resource,
            outcome=outcome,
            ip_address=ip_address,
            metadata=metadata or {},
            timestamp=datetime.now(timezone.utc)
        )
        self.audit_logs.insert(0, log_entry)
        return log_entry

    def list_audit_logs(self, limit: int = 100) -> List[SecurityAuditLog]:
        return self.audit_logs[:limit]

