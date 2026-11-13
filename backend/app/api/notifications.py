"""
FastAPI Endpoints for Phase 9: Notifications, Alerts & Advanced User Management.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, status, Header

from backend.app.notifications.schemas import (
    NotificationItem,
    NotificationType,
    CreateNotificationRequest,
    NotificationPreferences,
    AlertRule,
    CreateAlertRuleRequest,
)
from backend.app.notifications.notification_service import NotificationService
from backend.app.users.schemas import (
    UserProfile,
    UserRole,
    AccountStatus,
    UpdateProfileRequest,
    UpdateUserStatusRequest,
    SecurityAuditLog,
)
from backend.app.users.user_service import UserManager

router_notifications = APIRouter(prefix="/notifications", tags=["Notifications Engine"])
router_alerts = APIRouter(prefix="/alerts", tags=["Alert Rule Engine"])
router_users = APIRouter(prefix="/users", tags=["User Profile & Preferences"])
router_admin = APIRouter(prefix="/admin", tags=["Administrative & Security Audit"])


def get_current_user_id(x_user_id: Optional[str] = Header(default="default_researcher")) -> str:
    """Extract authenticated user ID from header context with fallback."""
    return x_user_id or "default_researcher"


# --- 1. Notification Endpoints ---

@router_notifications.post("", response_model=NotificationItem, status_code=status.HTTP_201_CREATED)
async def create_notification(req: CreateNotificationRequest):
    svc = NotificationService.get_instance()
    notif = await svc.create_notification(req)
    if not notif:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Notification suppressed by user preferences.")
    return notif


@router_notifications.get("", response_model=List[NotificationItem])
async def list_notifications(
    unread_only: bool = Query(False),
    notification_type: Optional[NotificationType] = Query(None),
    x_user_id: Optional[str] = Header(default="default_researcher"),
):
    svc = NotificationService.get_instance()
    return svc.list_notifications(user_id=x_user_id, unread_only=unread_only, notif_type=notification_type)


@router_notifications.get("/unread-count")
async def get_unread_count(x_user_id: Optional[str] = Header(default="default_researcher")):
    svc = NotificationService.get_instance()
    return {"user_id": x_user_id, "unread_count": svc.get_unread_count(user_id=x_user_id)}


@router_notifications.patch("/{notification_id}/read", response_model=NotificationItem)
async def mark_notification_read(
    notification_id: str,
    x_user_id: Optional[str] = Header(default="default_researcher"),
):
    svc = NotificationService.get_instance()
    notif = svc.mark_read(notification_id=notification_id, user_id=x_user_id)
    if not notif:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")
    return notif


@router_notifications.post("/read-all")
async def mark_all_notifications_read(x_user_id: Optional[str] = Header(default="default_researcher")):
    svc = NotificationService.get_instance()
    count = svc.mark_all_read(user_id=x_user_id)
    return {"user_id": x_user_id, "marked_read": count}


@router_notifications.delete("/{notification_id}")
async def delete_notification(
    notification_id: str,
    x_user_id: Optional[str] = Header(default="default_researcher"),
):
    svc = NotificationService.get_instance()
    ok = svc.delete_notification(notification_id=notification_id, user_id=x_user_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")
    return {"status": "DELETED", "notification_id": notification_id}


# --- 2. Alert Rules Endpoints ---

@router_alerts.get("/rules", response_model=List[AlertRule])
async def list_alert_rules(x_user_id: Optional[str] = Header(default="default_researcher")):
    svc = NotificationService.get_instance()
    return svc.list_rules(user_id=x_user_id)


@router_alerts.post("/rules", response_model=AlertRule, status_code=status.HTTP_201_CREATED)
async def create_alert_rule(
    req: CreateAlertRuleRequest,
    x_user_id: Optional[str] = Header(default="default_researcher"),
):
    svc = NotificationService.get_instance()
    return svc.create_rule(user_id=x_user_id, req=req)


@router_alerts.get("/rules/{rule_id}", response_model=AlertRule)
async def get_alert_rule(rule_id: str):
    svc = NotificationService.get_instance()
    rule = svc.get_rule(rule_id)
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert rule not found.")
    return rule


@router_alerts.delete("/rules/{rule_id}")
async def delete_alert_rule(
    rule_id: str,
    x_user_id: Optional[str] = Header(default="default_researcher"),
):
    svc = NotificationService.get_instance()
    ok = svc.delete_rule(rule_id=rule_id, user_id=x_user_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert rule not found.")
    return {"status": "DELETED", "rule_id": rule_id}


@router_alerts.post("/rules/{rule_id}/test", response_model=NotificationItem)
async def test_alert_rule(
    rule_id: str,
    x_user_id: Optional[str] = Header(default="default_researcher"),
):
    svc = NotificationService.get_instance()
    item = await svc.trigger_test_alert(rule_id=rule_id, user_id=x_user_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found or could not fire test.")
    return item


# --- 3. User Profile & Preferences Endpoints ---

@router_users.get("/me", response_model=UserProfile)
async def get_my_profile(x_user_id: Optional[str] = Header(default="default_researcher")):
    um = UserManager.get_instance()
    u = um.get_user(x_user_id)
    if not u:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found.")
    return u


@router_users.put("/me", response_model=UserProfile)
async def update_my_profile(
    req: UpdateProfileRequest,
    x_user_id: Optional[str] = Header(default="default_researcher"),
):
    um = UserManager.get_instance()
    u = um.update_profile(x_user_id, req)
    if not u:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return u


@router_users.get("/me/preferences", response_model=NotificationPreferences)
async def get_my_preferences(x_user_id: Optional[str] = Header(default="default_researcher")):
    svc = NotificationService.get_instance()
    return svc.get_preferences(x_user_id)


@router_users.put("/me/preferences", response_model=NotificationPreferences)
async def update_my_preferences(
    pref: NotificationPreferences,
    x_user_id: Optional[str] = Header(default="default_researcher"),
):
    svc = NotificationService.get_instance()
    pref.user_id = x_user_id
    return svc.update_preferences(pref)


# --- 4. Admin Management & Security Audit Endpoints ---

@router_admin.get("/dashboard")
async def get_admin_dashboard(x_user_id: Optional[str] = Header(default="usr_admin_01")):
    um = UserManager.get_instance()
    actor = um.get_user(x_user_id)
    if not actor or actor.role not in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Administrative access required.")

    users = um.list_users()
    active_count = sum(1 for u in users if u.status == AccountStatus.ACTIVE)
    suspended_count = sum(1 for u in users if u.status == AccountStatus.SUSPENDED)
    logs = um.list_audit_logs(limit=10)

    return {
        "total_users": len(users),
        "active_users": active_count,
        "suspended_users": suspended_count,
        "recent_security_events": logs,
        "system_status": "HEALTHY",
    }


@router_admin.get("/users", response_model=List[UserProfile])
async def list_admin_users(x_user_id: Optional[str] = Header(default="usr_admin_01")):
    um = UserManager.get_instance()
    actor = um.get_user(x_user_id)
    if not actor or actor.role not in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Administrative access required.")
    return um.list_users()


@router_admin.get("/users/{user_id}", response_model=UserProfile)
async def get_admin_user_detail(user_id: str, x_user_id: Optional[str] = Header(default="usr_admin_01")):
    um = UserManager.get_instance()
    actor = um.get_user(x_user_id)
    if not actor or actor.role not in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Administrative access required.")
    u = um.get_user(user_id)
    if not u:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return u


@router_admin.patch("/users/{user_id}/status", response_model=UserProfile)
async def update_user_status(
    user_id: str,
    req: UpdateUserStatusRequest,
    x_user_id: Optional[str] = Header(default="usr_admin_01"),
):
    um = UserManager.get_instance()
    try:
        updated = um.update_user_status(
            actor_user_id=x_user_id,
            target_user_id=user_id,
            new_status=req.status,
            reason=req.reason or ""
        )
        if not updated:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        return updated
    except PermissionError as pe:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(pe))


@router_admin.get("/audit-logs", response_model=List[SecurityAuditLog])
async def list_audit_logs(
    limit: int = Query(50, ge=1, le=200),
    x_user_id: Optional[str] = Header(default="usr_admin_01"),
):
    um = UserManager.get_instance()
    actor = um.get_user(x_user_id)
    if not actor or actor.role not in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Administrative access required.")
    return um.list_audit_logs(limit=limit)

