from datetime import date, timedelta

from .extensions import db
from .models import CaseUpdate, EmergencyAlert, EmergencyContact, Incident, SupportService, User


DEMO_ACCOUNTS = (
    {
        "full_name": "SHEild Administrator",
        "email": "admin@sheild.local",
        "password": "Admin123!",
        "role": "ADMIN",
    },
    {
        "full_name": "Nneka Okafor",
        "email": "responder@sheild.local",
        "password": "Responder123!",
        "role": "RESPONDER",
        "phone": "0800 000 0202",
    },
    {
        "full_name": "Amina Demo",
        "email": "demo@sheild.local",
        "password": "Demo123!",
        "role": "REPORTER",
        "phone": "0800 000 0101",
    },
)


def _get_or_create_demo_users():
    users = {}
    for account in DEMO_ACCOUNTS:
        user = User.query.filter_by(email=account["email"]).first()
        if user is None:
            user = User(
                full_name=account["full_name"],
                email=account["email"],
                role=account["role"],
                phone=account.get("phone"),
            )
            user.set_password(account["password"])
            db.session.add(user)
        users[account["role"]] = user
    db.session.flush()
    return users


def seed_database():
    users = _get_or_create_demo_users()
    reporter = users["REPORTER"]
    responder = users["RESPONDER"]
    admin = users["ADMIN"]

    case_number = f"SHR-{date.today().year}-0001"
    incident = Incident.query.filter_by(case_number=case_number).first()
    if incident is None:
        incident = Incident(
            case_number=case_number,
            reporter=reporter,
            assigned_to=responder,
            category="Online Harassment",
            description="Fictional demonstration report concerning repeated threatening messages.",
            location="Central District (demo location)",
            incident_date=date.today() - timedelta(days=3),
            safe_contact="Email only",
            risk_level="LOW",
            status="IN_PROGRESS",
        )
        db.session.add(incident)
        db.session.flush()
        db.session.add_all([
            CaseUpdate(incident=incident, author=reporter, status="RECEIVED", note="Report received securely by the prototype."),
            CaseUpdate(incident=incident, author=admin, status="RESPONDER_ASSIGNED", note="A support responder has been assigned."),
            CaseUpdate(incident=incident, author=responder, status="IN_PROGRESS", note="Initial safe-contact plan recorded."),
        ])

    alert_number = f"SOS-{date.today().year}-0001"
    final_demo_marker = Incident.query.filter_by(
        case_number=f"SHR-{date.today().year}-0101"
    ).first()
    if final_demo_marker is None and EmergencyAlert.query.filter_by(alert_number=alert_number).first() is None:
        db.session.add(EmergencyAlert(
            alert_number=alert_number, reporter=reporter,
            location="Demo community centre", safe_contact="0800 000 0101",
            message="Fictional alert used to demonstrate the response queue.", status="ACKNOWLEDGED",
            assigned_to=responder,
        ))

    service_data = (
        dict(name="Safe Harbour Support Centre", category="Counselling", description="Fictional trauma-informed counselling and safety-planning service for demonstration purposes.", phone="0800 111 0101", hours="Mon–Fri, 08:00–18:00"),
        dict(name="Community Legal Access", category="Legal Support", description="Fictional confidential legal information and referral service.", email="help@example.test", hours="Mon–Fri, 09:00–17:00"),
        dict(name="Hope Shelter Network", category="Safe Accommodation", description="Fictional short-term safe accommodation referral service.", phone="0800 111 0303", hours="24 hours (demo)"),
    )
    for values in service_data:
        if SupportService.query.filter_by(name=values["name"]).first() is None:
            db.session.add(SupportService(**values))

    contact_data = (
        dict(name="National Emergency Number", phone="112", description="Public emergency number. Availability varies by location; verify locally.", is_primary=True),
        dict(name="SHEild Demo Support Line", phone="0800 000 0000", description="Fictional contact for prototype demonstration only."),
    )
    for values in contact_data:
        if EmergencyContact.query.filter_by(name=values["name"]).first() is None:
            db.session.add(EmergencyContact(**values))
    db.session.commit()
