from datetime import date

import pytest
from sqlalchemy import func

from shield import create_app
from shield.admin.routes import _build_chart_data
from shield.extensions import db
from shield.final_demo import ALERT_SPECS, CASE_SPECS, FINAL_ACCOUNTS, seed_final_demo
from shield.models import CaseUpdate, EmergencyAlert, EmergencyContact, Incident, SupportService, User


@pytest.fixture()
def app():
    app = create_app({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SECRET_KEY": "final-demo-test-secret",
    })
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def login(client, email, password):
    return client.post(
        "/auth/login", data={"email": email, "password": password},
        follow_redirects=True,
    )


def final_cases():
    year = date.today().year
    expected = {f"SHR-{year}-{spec[0]:04d}" for spec in CASE_SPECS}
    return Incident.query.filter(Incident.case_number.in_(expected)).all()


def final_alerts():
    year = date.today().year
    expected = {f"SOS-{year}-{spec[0]:04d}" for spec in ALERT_SPECS}
    return EmergencyAlert.query.filter(EmergencyAlert.alert_number.in_(expected)).all()


def test_final_demo_seed_is_repeat_safe(app):
    with app.app_context():
        seed_final_demo()
        first = {
            "users": User.query.count(),
            "incidents": Incident.query.count(),
            "alerts": EmergencyAlert.query.count(),
            "updates": CaseUpdate.query.count(),
            "services": SupportService.query.count(),
            "contacts": EmergencyContact.query.count(),
        }
        seed_final_demo()
        second = {
            "users": User.query.count(),
            "incidents": Incident.query.count(),
            "alerts": EmergencyAlert.query.count(),
            "updates": CaseUpdate.query.count(),
            "services": SupportService.query.count(),
            "contacts": EmergencyContact.query.count(),
        }
        assert second == first
        assert len(final_cases()) == 15
        assert len(final_alerts()) == 4
        assert EmergencyAlert.query.count() == 4
        assert all(alert.incident_id is not None for alert in EmergencyAlert.query.all())


def test_final_accounts_exist_are_active_and_passwords_are_hashed(app):
    with app.app_context():
        seed_final_demo()
        for spec in FINAL_ACCOUNTS:
            user = User.query.filter_by(email=spec["email"]).one()
            assert user.role == spec["role"]
            assert user.is_active_account is True
            assert user.check_password(spec["password"])
            assert user.password_hash != spec["password"]
            assert spec["password"] not in user.password_hash
        assert User.query.filter_by(email="responder2@sheild.local", role="RESPONDER").count() == 1


def test_final_cases_span_categories_risks_statuses_sources_and_six_months(app):
    with app.app_context():
        seed_final_demo()
        cases = final_cases()
        assert len({item.category for item in cases}) >= 9
        assert {item.risk_level for item in cases} == {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
        assert {item.status for item in cases} == {
            "RECEIVED", "UNDER_REVIEW", "RESPONDER_ASSIGNED", "IN_PROGRESS",
            "REFERRED", "RESOLVED", "CLOSED",
        }
        assert sum(item.source == "REPORT" for item in cases) == 11
        assert sum(item.source == "SOS" for item in cases) == 4
        assert len({(item.created_at.year, item.created_at.month) for item in cases}) == 6
        assert sum(item.is_anonymous and item.source == "REPORT" for item in cases) >= 2
        assert sum(item.is_anonymous and item.source == "SOS" for item in cases) >= 1


def test_final_sos_alerts_are_linked_critical_and_cover_each_state(app):
    with app.app_context():
        seed_final_demo()
        alerts = final_alerts()
        assert {alert.status for alert in alerts} == {"NEW", "ACKNOWLEDGED", "RESPONDING", "RESOLVED"}
        for alert in alerts:
            assert alert.incident is not None
            assert alert.incident.source == "SOS"
            assert alert.incident.risk_level == "CRITICAL"
            assert alert.reporter_id == alert.incident.reporter_id
            assert alert.assigned_to_id == alert.incident.assigned_to_id


def test_final_responder_workload_and_analytics_are_meaningful(app):
    with app.app_context():
        seed_final_demo()
        responder1 = User.query.filter_by(email="responder@sheild.local").one()
        responder2 = User.query.filter_by(email="responder2@sheild.local").one()
        cases = final_cases()
        assert sum(item.assigned_to_id == responder1.id for item in cases) > 0
        assert sum(item.assigned_to_id == responder2.id for item in cases) > 0
        assert sum(item.assigned_to_id is None for item in cases) > 0

        charts = _build_chart_data()
        assert len([value for value in charts["category"]["values"] if value]) >= 8
        assert all(value > 0 for value in charts["risk"]["values"])
        assert all(value > 0 for value in charts["status"]["values"])
        assert all(value > 0 for value in charts["timeline"]["values"])
        assert all(value > 0 for value in charts["source"]["values"])
        assert all(value > 0 for value in charts["alert_status"]["values"])


def test_legacy_cleanup_deactivates_dependencies_and_removes_unused(app):
    with app.app_context():
        legacy = []
        for name, email, role in (
            ("Legacy Reporter", "reporter@shield.demo", "REPORTER"),
            ("Legacy Responder", "responder@shield.demo", "RESPONDER"),
            ("Legacy Admin", "admin@shield.demo", "ADMIN"),
            ("Unused Legacy Responder", "zainab@shield.demo", "RESPONDER"),
        ):
            user = User(full_name=name, email=email, role=role)
            user.set_password("LegacyOnly123!")
            db.session.add(user)
            legacy.append(user)
        db.session.flush()

        base_case = Incident.query.first()
        base_alert = EmergencyAlert.query.first()
        base_update = CaseUpdate.query.first()
        base_case.reporter_id = legacy[0].id
        base_case.assigned_to_id = legacy[1].id
        base_alert.reporter_id = legacy[0].id
        base_alert.assigned_to_id = legacy[1].id
        base_update.author_id = legacy[2].id
        db.session.commit()

        result = seed_final_demo()
        assert set(result["legacy"]["deactivated"]) == {
            "reporter@shield.demo", "responder@shield.demo", "admin@shield.demo",
        }
        assert result["legacy"]["removed"] == ["zainab@shield.demo"]
        for email in result["legacy"]["deactivated"]:
            assert User.query.filter_by(email=email, is_active_account=False).count() == 1
        assert User.query.filter_by(email="zainab@shield.demo").first() is None
        assert db.session.get(Incident, base_case.id) is not None


def test_final_directory_is_fictional_and_unverified_number_is_inactive(app):
    with app.app_context():
        seed_final_demo()
        active_services = SupportService.query.filter_by(is_active=True).all()
        active_contacts = EmergencyContact.query.filter_by(is_active=True).all()
        assert 4 <= len(active_services) <= 6
        assert len(active_contacts) == 4
        assert all("fictional" in item.description.lower() or "demo" in item.description.lower() for item in active_services)
        assert all("demo" in item.phone.lower() for item in active_contacts)
        assert all("demo" in item.description.lower() or "fictional" in item.description.lower() or "prototype" in item.description.lower() for item in active_contacts)
        unverified = EmergencyContact.query.filter_by(name="National Emergency Number").one()
        assert unverified.is_active is False


def test_seeded_anonymous_case_stays_private_in_operational_views(app, client):
    with app.app_context():
        seed_final_demo()
        year = date.today().year
        incident = Incident.query.filter_by(case_number=f"SHR-{year}-0105").one()
        incident_id = incident.id
        case_number = incident.case_number

    responder_page = login(client, "responder@sheild.local", "Responder123!")
    assert responder_page.status_code == 200
    responder_case = client.get(f"/responder/cases/{incident_id}")
    assert responder_case.status_code == 200
    assert b"Amina Demo" not in responder_case.data
    assert b"demo@sheild.local" not in responder_case.data

    client.post("/auth/logout", follow_redirects=True)
    login(client, "admin@sheild.local", "Admin123!")
    admin_case = client.get(f"/admin/incidents/{incident_id}")
    activity = client.get(f"/admin/activity?q={case_number}")
    assert admin_case.status_code == 200
    assert activity.status_code == 200
    assert b"Amina Demo" not in admin_case.data
    assert b"demo@sheild.local" not in admin_case.data
    assert b"Amina Demo" not in activity.data
    assert b"demo@sheild.local" not in activity.data
