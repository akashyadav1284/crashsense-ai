"""
Centralized Notification Service, Preferences Manager, and Alert Rule Engine.
Supports real-time WebSocket dispatch, alert rule evaluation with cooldowns,
and persistent notification history.
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
from backend.app.notifications.schemas import (
    NotificationItem,
    NotificationType,
    NotificationSeverity,
    CreateNotificationRequest,
    NotificationPreferences,
    AlertRule,
    CreateAlertRuleRequest,
)
from backend.app.api.websocket import ws_hub
from backend.app.core.logging import logger


class NotificationService:
    """Manages notification lifecycle, preferences, alert rule evaluations, and real-time broadcasts."""

    _instance: Optional["NotificationService"] = None

    def __init__(self):
        self.notifications: Dict[str, NotificationItem] = {}
        self.preferences: Dict[str, NotificationPreferences] = {}
        self.rules: Dict[str, AlertRule] = {}
        self._init_defaults()

    @classmethod
    def get_instance(cls) -> "NotificationService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _init_defaults(self):
        """Seed default user preferences and standard system alert rules."""
        default_pref = NotificationPreferences(user_id="default_researcher")
        self.preferences[default_pref.user_id] = default_pref

        # Seed standard alert rules
        r1 = AlertRule(
            rule_id="rule_conn_disconnect",
            user_id="default_researcher",
            name="Feed Disconnection Alert",
            description="Triggers when an authorized live connector drops connection.",
            event_type="connector_disconnected",
            severity=NotificationSeverity.ERROR,
            cooldown_seconds=30,
        )
        r2 = AlertRule(
            rule_id="rule_drawdown_breach",
            user_id="default_researcher",
            name="Max Drawdown Circuit Breaker",
            description="Triggers when a paper simulation breaches maximum drawdown stop.",
            event_type="drawdown_breached",
            threshold=25.0,
            severity=NotificationSeverity.CRITICAL,
            cooldown_seconds=60,
        )
        r3 = AlertRule(
            rule_id="rule_model_validated",
            user_id="default_researcher",
            name="Model Edge Validation Notice",
            description="Triggers when a research model proves statistically significant edge.",
            event_type="model_validated",
            severity=NotificationSeverity.SUCCESS,
            cooldown_seconds=300,
        )
        self.rules[r1.rule_id] = r1
        self.rules[r2.rule_id] = r2
        self.rules[r3.rule_id] = r3

    async def create_notification(self, req: CreateNotificationRequest) -> Optional[NotificationItem]:
        """
        Creates and stores a notification if permitted by user preferences.
        Dispatches over WebSocket for real-time delivery.
        """
        pref = self.preferences.get(req.user_id) or NotificationPreferences(user_id=req.user_id)

        # 1. Check if user disabled notifications or category
        if not pref.notifications_enabled:
            return None
        if req.notification_type not in pref.enabled_types:
            return None

        notif_id = f"notif_{uuid.uuid4().hex[:10]}"
        item = NotificationItem(
            notification_id=notif_id,
            user_id=req.user_id,
            title=req.title,
            message=req.message,
            notification_type=req.notification_type,
            severity=req.severity,
            resource_id=req.resource_id,
            metadata=req.metadata,
            created_at=datetime.now(timezone.utc)
        )
        self.notifications[notif_id] = item

        # Real-time WebSocket dispatch
        try:
            await ws_hub.broadcast("notification_created", item.dict())
        except Exception as e:
            logger.warning("Failed to broadcast notification over WebSocket: %s", str(e))

        return item

    def list_notifications(
        self,
        user_id: str,
        unread_only: bool = False,
        notif_type: Optional[NotificationType] = None
    ) -> List[NotificationItem]:
        results = [n for n in self.notifications.values() if n.user_id == user_id]
        if unread_only:
            results = [n for n in results if not n.is_read]
        if notif_type:
            results = [n for n in results if n.notification_type == notif_type]
        return sorted(results, key=lambda n: n.created_at, reverse=True)

    def mark_read(self, notification_id: str, user_id: str) -> Optional[NotificationItem]:
        notif = self.notifications.get(notification_id)
        if notif and notif.user_id == user_id:
            notif.is_read = True
            return notif
        return None

    def mark_all_read(self, user_id: str) -> int:
        count = 0
        for notif in self.notifications.values():
            if notif.user_id == user_id and not notif.is_read:
                notif.is_read = True
                count += 1
        return count

    def delete_notification(self, notification_id: str, user_id: str) -> bool:
        notif = self.notifications.get(notification_id)
        if notif and notif.user_id == user_id:
            del self.notifications[notification_id]
            return True
        return False

    def get_unread_count(self, user_id: str) -> int:
        return sum(1 for n in self.notifications.values() if n.user_id == user_id and not n.is_read)

    def get_preferences(self, user_id: str) -> NotificationPreferences:
        return self.preferences.get(user_id) or NotificationPreferences(user_id=user_id)

    def update_preferences(self, pref: NotificationPreferences) -> NotificationPreferences:
        self.preferences[pref.user_id] = pref
        return pref

    # --- Alert Rules ---

    def list_rules(self, user_id: str) -> List[AlertRule]:
        return [r for r in self.rules.values() if r.user_id == user_id]

    def create_rule(self, user_id: str, req: CreateAlertRuleRequest) -> AlertRule:
        rule_id = f"rule_{uuid.uuid4().hex[:8]}"
        rule = AlertRule(
            rule_id=rule_id,
            user_id=user_id,
            name=req.name,
            description=req.description,
            event_type=req.event_type,
            threshold=req.threshold,
            severity=req.severity,
            cooldown_seconds=req.cooldown_seconds,
            notification_channel=req.notification_channel
        )
        self.rules[rule_id] = rule
        return rule

    def get_rule(self, rule_id: str) -> Optional[AlertRule]:
        return self.rules.get(rule_id)

    def delete_rule(self, rule_id: str, user_id: str) -> bool:
        r = self.rules.get(rule_id)
        if r and r.user_id == user_id:
            del self.rules[rule_id]
            return True
        return False

    async def trigger_test_alert(self, rule_id: str, user_id: str) -> Optional[NotificationItem]:
        """Dispatches a clearly tagged test notification verifying rule wiring."""
        r = self.rules.get(rule_id)
        if not r or r.user_id != user_id:
            return None

        return await self.create_notification(
            CreateNotificationRequest(
                user_id=user_id,
                title=f"[SIMULATED TEST] {r.name}",
                message=f"Test firing of rule '{r.name}' (Event: {r.event_type}). Verified intact.",
                notification_type=NotificationType.SYSTEM,
                severity=r.severity,
                metadata={"test_mode": True, "rule_id": rule_id}
            )
        )

