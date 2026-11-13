"""
User, RBAC, and Security Audit Data Contracts for Phase 9.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, EmailStr


class UserRole(str, Enum):
    USER = "USER"
    PREMIUM_USER = "PREMIUM_USER"
    MODERATOR = "MODERATOR"
    ADMIN = "ADMIN"
    SUPER_ADMIN = "SUPER_ADMIN"


class AccountStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    DISABLED = "DISABLED"
    PENDING_VERIFICATION = "PENDING_VERIFICATION"


class UserProfile(BaseModel):
    user_id: str
    email: str
    display_name: str
    role: UserRole = UserRole.USER
    status: AccountStatus = AccountStatus.ACTIVE
    avatar_url: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: Optional[datetime] = None
    preferences: Dict[str, Any] = Field(default_factory=dict)


class UserSession(BaseModel):
    session_id: str
    user_id: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_active: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True


class SecurityAuditLog(BaseModel):
    log_id: str
    actor_user_id: str
    actor_role: UserRole
    action: str  # LOGIN_ATTEMPT, ROLE_CHANGE, ACCOUNT_SUSPENSION, LIMIT_UPDATE, ADMIN_ACTION
    target_resource: str
    outcome: str  # SUCCESS, FAILURE, REJECTED
    ip_address: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class UpdateProfileRequest(BaseModel):
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None


class UpdateUserStatusRequest(BaseModel):
    status: AccountStatus
    reason: Optional[str] = None

