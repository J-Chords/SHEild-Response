import calendar
from datetime import date, datetime, timedelta

from .extensions import db
from .models import CaseUpdate, EmergencyAlert, EmergencyContact, Incident, SupportService, User


FINAL_ACCOUNTS = (
    {
        "full_name": "SHEild Administrator",
        "email": "admin@sheild.local",
        "password": "Admin123!",
        "role": "ADMIN",
        "phone": None,
    },
    {
        "full_name": "Nneka Okafor (Demo)",
        "email": "responder@sheild.local",
        "password": "Responder123!",
        "role": "RESPONDER",
        "phone": "DEMO-2001",
    },
    {
        "full_name": "Kemi Adara (Demo)",
        "email": "responder2@sheild.local",
        "password": "Responder2Pass!",
        "role": "RESPONDER",
        "phone": "DEMO-2002",
    },
    {
        "full_name": "Amina Demo",
        "email": "demo@sheild.local",
        "password": "Demo123!",
        "role": "REPORTER",
        "phone": "DEMO-1001",
    },
)


CASE_SPECS = (
    # suffix, category, risk, status, source, assignee key, anonymous, months ago
    (101, "Physical Violence", "LOW", "RECEIVED", "REPORT", None, False, 0),
    (102, "Sexual Violence", "HIGH", "UNDER_REVIEW", "REPORT", None, True, 1),
    (103, "Domestic Violence", "HIGH", "RESPONDER_ASSIGNED", "REPORT", "responder1", False, 1),
    (104, "Emotional/Psychological Abuse", "LOW", "IN_PROGRESS", "REPORT", "responder2", False, 2),
    (105, "Stalking", "MEDIUM", "REFERRED", "REPORT", "responder1", True, 2),
    (106, "Threat to Life", "CRITICAL", "RESOLVED", "REPORT", "responder2", False, 3),
    (107, "Forced Marriage", "HIGH", "CLOSED", "REPORT", "responder1", False, 3),
    (108, "Economic Abuse", "MEDIUM", "IN_PROGRESS", "REPORT", "responder2", False, 4),
    (109, "Online Harassment", "LOW", "RESOLVED", "REPORT", "responder1", False, 4),
    (110, "Domestic Violence", "MEDIUM", "UNDER_REVIEW", "REPORT", None, False, 5),
    (111, "Physical Violence", "HIGH", "RESPONDER_ASSIGNED", "REPORT", "responder2", False, 5),
    (112, "Threat to Life", "CRITICAL", "RECEIVED", "SOS", None, True, 0),
    (113, "Physical Violence", "CRITICAL", "RESPONDER_ASSIGNED", "SOS", "responder1", False, 1),
    (114, "Domestic Violence", "CRITICAL", "IN_PROGRESS", "SOS", "responder2", True, 0),
    (115, "Threat to Life", "CRITICAL", "RESOLVED", "SOS", "responder1", False, 3),
)


ALERT_SPECS = (
    # alert suffix, case suffix, status
    (101, 112, "NEW"),
    (102, 113, "ACKNOWLEDGED"),
    (103, 114, "RESPONDING"),
    (104, 115, "RESOLVED"),
)


SERVICE_SPECS = (
    {
        "name": "Safe Harbour Support Centre",
        "category": "Counselling",
        "description": "Fictional demo counselling and safety-planning service; not a real organisation.",
        "phone": "DEMO-3001",
        "hours": "Demo hours: Mon–Fri, 08:00–18:00",
    },
    {
        "name": "Community Legal Access",
        "category": "Legal Support",
        "description": "Fictional demo legal information and referral service; not a real organisation.",
        "email": "legal@example.test",
        "hours": "Demo hours: Mon–Fri, 09:00–17:00",
    },
    {
        "name": "Hope Shelter Network",
        "category": "Shelter / Safe Space",
        "description": "Fictional demo safe-space referral service; not a real shelter network.",
        "phone": "DEMO-3003",
        "hours": "Demo availability: 24 hours",
    },
    {
        "name": "New Dawn Medical Referral Hub",
        "category": "Medical Referral",
        "description": "Fictional demo medical-referral service for the defence dataset only.",
        "phone": "DEMO-3004",
        "hours": "Demo hours: daily, 08:00–20:00",
    },
    {
        "name": "Community Bridge Demo Network",
        "category": "Community Support",
        "description": "Fictional community-support directory entry created for demonstration.",
        "email": "community@example.test",
        "hours": "Demo hours: Tue–Sat, 09:00–16:00",
    },
    {
        "name": "Family First Demo Support",
        "category": "Child / Family Support",
        "description": "Fictional child and family support referral resource; not a real provider.",
        "phone": "DEMO-3006",
        "hours": "Demo hours: Mon–Fri, 08:30–17:00",
    },
)


CONTACT_SPECS = (
    {
        "name": "SHEild Demo Safety Desk",
        "phone": "DEMO-4001",
        "description": "Demonstration resource only — not a working emergency number.",
        "is_primary": True,
    },
    {
        "name": "Demo Safe Space Referral",
        "phone": "DEMO-4002",
        "description": "Fictional demonstration contact; does not connect to a real service.",
        "is_primary": False,
    },
    {
        "name": "Fictional Medical Support Desk",
        "phone": "DEMO-4003",
        "description": "Academic prototype contact only; not a medical hotline.",
        "is_primary": False,
    },
    {
        "name": "Demo Child and Family Support",
        "phone": "DEMO-4004",
        "description": "Fictional demonstration contact; not a real safeguarding service.",
        "is_primary": False,
    },
)


def _month_datetime(months_ago, day):
    today = date.today()
    month_index = today.year * 12 + today.month - 1 - months_ago
    year, zero_month = divmod(month_index, 12)
    month = zero_month + 1
    safe_day = min(day, calendar.monthrange(year, month)[1])
    return datetime(year, month, safe_day, 10, 30)


def _ensure_accounts():
    accounts = {}
    for spec in FINAL_ACCOUNTS:
        user = User.query.filter_by(email=spec["email"]).first()
        if user is None:
            user = User(email=spec["email"])
            db.session.add(user)
        user.full_name = spec["full_name"]
        user.role = spec["role"]
        user.phone = spec["phone"]
        user.is_active_account = True
        if not user.password_hash or not user.check_password(spec["password"]):
            user.set_password(spec["password"])
        accounts[spec["email"]] = user
    db.session.flush()
    return accounts


def _legacy_dependency_count(user):
    return sum((
        Incident.query.filter_by(reporter_id=user.id).count(),
        Incident.query.filter_by(assigned_to_id=user.id).count(),
        EmergencyAlert.query.filter_by(reporter_id=user.id).count(),
        EmergencyAlert.query.filter_by(assigned_to_id=user.id).count(),
        CaseUpdate.query.filter_by(author_id=user.id).count(),
    ))


def cleanup_legacy_accounts():
    result = {"deactivated": [], "removed": []}
    legacy_users = User.query.filter(User.email.like("%@shield.demo")).all()
    for user in legacy_users:
        if _legacy_dependency_count(user):
            user.is_active_account = False
            result["deactivated"].append(user.email)
        else:
            result["removed"].append(user.email)
            db.session.delete(user)
    db.session.flush()
    return result


def _remove_obsolete_seed_alert():
    """Remove only the exact pre-SOS-workflow orphan created by the original seed."""
    alert = EmergencyAlert.query.filter_by(
        alert_number=f"SOS-{date.today().year}-0001", incident_id=None
    ).first()
    if alert and alert.message == "Fictional alert used to demonstrate the response queue.":
        db.session.delete(alert)
        db.session.flush()
        return True
    return False


def _case_description(category, source):
    channel = "emergency request" if source == "SOS" else "incident report"
    return (
        f"Fictional {channel} concerning {category.lower()}, created solely for the "
        "SHEild Response final-year project demonstration. No real person is represented."
    )


def _ensure_case(spec, accounts):
    suffix, category, risk, status, source, assignee_key, anonymous, months_ago = spec
    year = date.today().year
    case_number = f"SHR-{year}-{suffix:04d}"
    incident = Incident.query.filter_by(case_number=case_number).first()
    if incident is None:
        incident = Incident(case_number=case_number)
        db.session.add(incident)

    created_at = _month_datetime(months_ago, 4 + suffix % 20)
    assignees = {
        "responder1": accounts["responder@sheild.local"],
        "responder2": accounts["responder2@sheild.local"],
    }
    incident.reporter = accounts["demo@sheild.local"]
    incident.assigned_to = assignees.get(assignee_key)
    incident.category = category
    incident.description = _case_description(category, source)
    incident.location = f"Demo District {suffix - 100}"
    incident.incident_date = created_at.date() - timedelta(days=2)
    incident.safe_contact = "Secure in-app updates only"
    incident.preferred_contact_method = "IN_APP"
    incident.is_anonymous = anonymous
    incident.immediate_danger = source == "SOS" or risk == "CRITICAL"
    incident.threat_to_life = category == "Threat to Life"
    incident.weapon_involved = source == "SOS" and suffix in (113, 115)
    incident.medical_attention = category in ("Physical Violence", "Sexual Violence")
    incident.dependants_at_risk = category in ("Domestic Violence", "Forced Marriage")
    incident.risk_level = risk
    incident.status = status
    incident.source = source
    incident.created_at = created_at
    incident.updated_at = created_at + timedelta(days=2)
    db.session.flush()
    return incident


def _ensure_update(incident, author, status, note, update_type, visibility, created_at):
    update = CaseUpdate.query.filter_by(
        incident_id=incident.id, update_type=update_type, note=note
    ).first()
    if update is None:
        update = CaseUpdate(incident=incident, update_type=update_type, note=note)
        db.session.add(update)
    update.author = author
    update.status = status
    update.visibility = visibility
    update.visible_to_reporter = visibility != "INTERNAL"
    update.created_at = created_at
    return update


def _ensure_timelines(cases, accounts):
    reporter = accounts["demo@sheild.local"]
    admin = accounts["admin@sheild.local"]
    responder1 = accounts["responder@sheild.local"]
    responder2 = accounts["responder2@sheild.local"]

    for incident in cases.values():
        _ensure_update(
            incident, reporter, "RECEIVED",
            "Fictional report received securely by the academic prototype.",
            "SOS" if incident.source == "SOS" else "REPORT_RECEIVED",
            "SYSTEM", incident.created_at,
        )

    rich_updates = {
        103: (
            (admin, "UNDER_REVIEW", "Initial safeguarding review completed for the fictional case.", "STATUS", "SYSTEM", 1),
            (admin, "RESPONDER_ASSIGNED", "Case assigned to a demonstration responder.", "ADMIN_ASSIGNMENT", "SYSTEM", 2),
        ),
        105: (
            (admin, "UNDER_REVIEW", "Fictional case reviewed and prioritised for follow-up.", "STATUS", "SYSTEM", 1),
            (admin, "RESPONDER_ASSIGNED", "Case assigned to a demonstration responder.", "ADMIN_ASSIGNMENT", "SYSTEM", 2),
            (responder1, "IN_PROGRESS", "Internal safety-planning note recorded for demonstration.", "NOTE", "INTERNAL", 3),
            (responder1, "REFERRED", "Referral recorded to a fictional support service.", "REFERRAL", "INTERNAL", 4),
            (responder1, "REFERRED", "A support referral has been recorded for your case.", "REPORTER_UPDATE", "REPORTER_VISIBLE", 4),
        ),
        114: (
            (responder2, "RESPONDER_ASSIGNED", "Emergency request acknowledged by a demonstration responder.", "ACKNOWLEDGEMENT", "SYSTEM", 1),
            (responder2, "IN_PROGRESS", "Emergency response workflow started in the prototype.", "RESPONSE_STARTED", "SYSTEM", 1),
            (responder2, "IN_PROGRESS", "Internal emergency coordination note for demonstration only.", "NOTE", "INTERNAL", 2),
        ),
        115: (
            (responder1, "RESPONDER_ASSIGNED", "Emergency request acknowledged by a demonstration responder.", "ACKNOWLEDGEMENT", "SYSTEM", 1),
            (responder1, "IN_PROGRESS", "Emergency response workflow started in the prototype.", "RESPONSE_STARTED", "SYSTEM", 2),
            (responder1, "RESOLVED", "Emergency alert resolved in the fictional workflow.", "ALERT_RESOLVED", "SYSTEM", 3),
            (responder1, "RESOLVED", "The demonstration case was marked resolved after follow-up.", "REPORTER_UPDATE", "REPORTER_VISIBLE", 4),
        ),
    }
    for suffix, updates in rich_updates.items():
        incident = cases[suffix]
        for author, status, note, update_type, visibility, days_after in updates:
            _ensure_update(
                incident, author, status, note, update_type, visibility,
                incident.created_at + timedelta(days=days_after),
            )
        incident.updated_at = incident.created_at + timedelta(
            days=max(item[-1] for item in updates)
        )


def _ensure_alerts(cases):
    year = date.today().year
    for alert_suffix, case_suffix, status in ALERT_SPECS:
        incident = cases[case_suffix]
        alert_number = f"SOS-{year}-{alert_suffix:04d}"
        alert = EmergencyAlert.query.filter_by(alert_number=alert_number).first()
        if alert is None:
            alert = EmergencyAlert(alert_number=alert_number)
            db.session.add(alert)
        alert.reporter_id = incident.reporter_id
        alert.assigned_to_id = incident.assigned_to_id
        alert.incident_id = incident.id
        alert.location = incident.location
        alert.safe_contact = incident.safe_contact
        alert.message = incident.description
        alert.status = status
        alert.created_at = incident.created_at
        alert.updated_at = incident.updated_at
        alert.acknowledged_at = (
            incident.created_at + timedelta(hours=1) if status != "NEW" else None
        )


def _ensure_services_and_contacts():
    for spec in SERVICE_SPECS:
        service = SupportService.query.filter_by(name=spec["name"]).first()
        if service is None:
            service = SupportService(name=spec["name"])
            db.session.add(service)
        for key in ("category", "description", "phone", "email", "hours"):
            setattr(service, key, spec.get(key))
        service.website = None
        service.is_active = True

    EmergencyContact.query.update({EmergencyContact.is_primary: False})
    unverified = EmergencyContact.query.filter_by(name="National Emergency Number").first()
    if unverified:
        unverified.is_active = False

    old_demo = EmergencyContact.query.filter_by(name="SHEild Demo Support Line").first()
    if old_demo:
        old_demo.is_active = False

    for spec in CONTACT_SPECS:
        contact = EmergencyContact.query.filter_by(name=spec["name"]).first()
        if contact is None:
            contact = EmergencyContact(name=spec["name"])
            db.session.add(contact)
        contact.phone = spec["phone"]
        contact.description = spec["description"]
        contact.is_primary = spec["is_primary"]
        contact.is_active = True


def seed_final_demo():
    """Create the deterministic final defence dataset without duplicating records."""
    accounts = _ensure_accounts()
    legacy_result = cleanup_legacy_accounts()
    obsolete_alert_removed = _remove_obsolete_seed_alert()
    cases = {spec[0]: _ensure_case(spec, accounts) for spec in CASE_SPECS}
    _ensure_timelines(cases, accounts)
    _ensure_alerts(cases)
    _ensure_services_and_contacts()
    db.session.commit()
    return {
        "legacy": legacy_result,
        "obsolete_alert_removed": obsolete_alert_removed,
        "case_numbers": [case.case_number for case in cases.values()],
        "alert_numbers": [f"SOS-{date.today().year}-{spec[0]:04d}" for spec in ALERT_SPECS],
    }
