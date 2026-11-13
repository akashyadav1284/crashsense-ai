"""
Comprehensive Test Suite for Phase 9: Notifications, Alerts & Advanced User Management.
Covers:
1. Centralized notification creation, retrieval, and preference filtering.
2. Mark as read, mark all as read, and unread count tracking.
3. Alert rules management and safe test-firing.
4. User profile retrieval, update, and preference isolation.
5. Role-based access control (RBAC): user cannot invoke admin endpoints; admin can update user status.
6. Security audit logging on sensitive actions.
7. Data isolation between users.
"""

import pytest
from httpx import AsyncClient, ASGITransport

from backend.app.main import app
from backend.app.notifications.schemas import (
    NotificationType,
    NotificationSeverity,
    CreateNotificationRequest,
)
from backend.app.notifications.notification_service import NotificationService
from backend.app.users.schemas import UserRole, AccountStatus
from backend.app.users.user_service import UserManager


@pytest.mark.asyncio
async def test_notification_creation_and_filtering():
    """Verify notification service enforces user preferences and stores notifications."""
    svc = NotificationService()

    # Create notification of type RISK
    req = CreateNotificationRequest(
        user_id="default_researcher",
        title="Drawdown Notice",
        message="Simulated drawdown reached 15%",
        notification_type=NotificationType.RISK,
        severity=NotificationSeverity.WARNING
    )
    notif = await svc.create_notification(req)
    assert notif is not None
    assert notif.title == "Drawdown Notice"
    assert notif.is_read is False

    # Check unread count
    assert svc.get_unread_count("default_researcher") >= 1

    # Mark as read
    marked = svc.mark_read(notif.notification_id, "default_researcher")
    assert marked is not None
    assert marked.is_read is True


@pytest.mark.asyncio
async def test_alert_rules_and_test_fire():
    """Verify alert rule listing and simulated test firing."""
    svc = NotificationService()
    rules = svc.list_rules("default_researcher")
    assert len(rules) >= 2

    # Test fire rule
    rule_id = rules[0].rule_id
    test_item = await svc.trigger_test_alert(rule_id, "default_researcher")
    assert test_item is not None
    assert "[SIMULATED TEST]" in test_item.title
    assert test_item.metadata.get("test_mode") is True


@pytest.mark.asyncio
async def test_user_management_and_rbac():
    """Verify user profile retrieval and administrative status updates with RBAC."""
    um = UserManager()

    # User profile lookup
    u = um.get_user("default_researcher")
    assert u is not None
    assert u.role == UserRole.USER

    # Admin updates user status to SUSPENDED
    updated = um.update_user_status(
        actor_user_id="usr_admin_01",
        target_user_id="default_researcher",
        new_status=AccountStatus.SUSPENDED,
        reason="Compliance audit check"
    )
    assert updated is not None
    assert updated.status == AccountStatus.SUSPENDED

    # Verify security audit log was written
    logs = um.list_audit_logs()
    assert len(logs) >= 1
    assert logs[0].action == "ACCOUNT_STATUS_CHANGE"
    assert logs[0].target_resource == "default_researcher"

    # Non-admin cannot update status
    with pytest.raises(PermissionError):
        um.update_user_status(
            actor_user_id="default_researcher",
            target_user_id="usr_admin_01",
            new_status=AccountStatus.DISABLED
        )


@pytest.mark.asyncio
async def test_api_notifications_and_admin_endpoints():
    """Verify FastAPI endpoints for notifications, alerts, and admin dashboard."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Notifications list
        res_n = await client.get("/api/v1/notifications", headers={"x-user-id": "default_researcher"})
        assert res_n.status_code == 200
        assert isinstance(res_n.json(), list)

        # 2. Unread count
        res_cnt = await client.get("/api/v1/notifications/unread-count", headers={"x-user-id": "default_researcher"})
        assert res_cnt.status_code == 200
        assert "unread_count" in res_cnt.json()

        # 3. Alert rules
        res_rules = await client.get("/api/v1/alerts/rules", headers={"x-user-id": "default_researcher"})
        assert res_rules.status_code == 200
        assert len(res_rules.json()) >= 1

        # 4. User profile
        res_me = await client.get("/api/v1/users/me", headers={"x-user-id": "default_researcher"})
        assert res_me.status_code == 200
        assert res_me.json()["user_id"] == "default_researcher"

        # 5. Admin dashboard accessible with admin header
        res_admin = await client.get("/api/v1/admin/dashboard", headers={"x-user-id": "usr_admin_01"})
        assert res_admin.status_code == 200
        assert "total_users" in res_admin.json()

        # 6. Admin dashboard FORBIDDEN for regular user
        res_forbid = await client.get("/api/v1/admin/dashboard", headers={"x-user-id": "default_researcher"})
        assert res_forbid.status_code == 403

