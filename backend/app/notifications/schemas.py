"""
Pydantic Schemas and Contracts for Notifications & Alert Rule Engine.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class NotificationType(str, Enum):
    SYSTEM = "SYSTEM"
    SECURITY = "SECURITY"
    CONNECTOR = "CONNECTOR"
    DATA_QUALITY = "DATA_QUALITY"
    ML_RESEARCH = "ML_RESEARCH"
    SIMULATION = "SIMULATION"
    RISK = "RISK"
    ACCOUNT = "ACCOUNT"
    ADMIN = "ADMIN"


class NotificationSeverity(str, Enum):
    INFO = "INFO"
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class NotificationItem(BaseModel):
    notification_id: str
    user_id: str = "default_researcher"
    title: str
    message: str
    notification_type: NotificationType = NotificationType.SYSTEM
    severity: NotificationSeverity = NotificationSeverity.INFO
    is_read: bool = False
    resource_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None


class CreateNotificationRequest(BaseModel):
    user_id: str = "default_researcher"
    title: str
    message: str
    notification_type: NotificationType = NotificationType.SYSTEM
    severity: NotificationSeverity = NotificationSeverity.INFO
    resource_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class NotificationPreferences(BaseModel):
    user_id: str = "default_researcher"
    notifications_enabled: bool = True
    enabled_types: List[NotificationType] = Field(
        default_factory=lambda: [
            NotificationType.SYSTEM,
            NotificationType.SECURITY,
            NotificationType.CONNECTOR,
            NotificationType.DATA_QUALITY,
            NotificationType.ML_RESEARCH,
            NotificationType.SIMULATION,
            NotificationType.RISK,
        ]
    )
    min_severity: NotificationSeverity = NotificationSeverity.INFO
    sound_enabled: bool = True
    browser_notifications: bool = False
    email_notifications: bool = False
    cooldown_seconds: int = 15


class AlertRule(BaseModel):
    rule_id: str
    user_id: str = "default_researcher"
    name: str
    description: str
    event_type: str  # connector_disconnected, model_validated, drawdown_breach, etc.
    threshold: Optional[float] = None
    severity: NotificationSeverity = NotificationSeverity.WARNING
    is_enabled: bool = True
    cooldown_seconds: int = 60
    notification_channel: str = "IN_APP"  # IN_APP, WEBSOCKET, EMAIL
    last_triggered: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CreateAlertRuleRequest(BaseModel):
    name: str
    description: str
    event_type: str
    threshold: Optional[float] = None
    severity: NotificationSeverity = NotificationSeverity.WARNING
    cooldown_seconds: int = 60
    notification_channel: str = "IN_APP"

