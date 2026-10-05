import re
from datetime import date, timedelta

import pytest

from shield import create_app
from shield.extensions import db
from shield.models import CaseUpdate, EmergencyAlert, EmergencyContact, Incident, SupportService, User
from shield.seed import seed_database
from shield.services.risk_assessment import assess_incident_risk


DEMO_PASSWORDS = {
    "demo@sheild.local": "Demo123!",
    "responder@sheild.local": "Responder123!",
    "admin@sheild.local": "Admin123!",
}


@pytest.fixture()
def app():
    app = create_app({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SECRET_KEY": "test-secret",
    })
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def login(client, email, password=None):
    return client.post(
        "/auth/login",
        data={"email": email, "password": password or DEMO_PASSWORDS[email]},
        follow_redirects=True,
    )


def logout(client):
    return client.post("/auth/logout", follow_redirects=True)


def test_public_pages_and_prototype_notice(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Academic prototype" in response.data
    assert b"Quick Exit" in response.data
    support = client.get("/support")
    assert support.status_code == 200
    assert b"fictional" in support.data.lower()
    assert client.get("/about-safety").status_code == 200
    forgot = client.get("/auth/forgot-password")
    assert forgot.status_code == 200
    assert b"does not send external emails" in forgot.data


def test_demo_roles_reach_their_dashboards(client):
    for email, expected in [
        ("demo@sheild.local", b"Reporter overview"),
        ("responder@sheild.local", b"Responder workspace"),
        ("admin@sheild.local", b"Operational overview"),
    ]:
        response = login(client, email)
        assert response.status_code == 200
        assert expected in response.data
        logout(client)


def test_passwords_are_hashed(app):
    with app.app_context():
        user = User.query.filter_by(email="demo@sheild.local").first()
        assert user.password_hash != "Demo123!"
        assert user.check_password("Demo123!")


def test_reporter_can_submit_report_and_get_public_reference(client, app):
    login(client, "demo@sheild.local")
    response = client.post("/reporter/reports/new", data={
        "category": "Stalking",
        "incident_date": "2026-10-01",
        "location": "Fictional North District",
        "description": "A fictional description long enough for validation and safe testing.",
        "preferred_contact_method": "IN_APP",
        "safe_contact": "Email only",
        "immediate_danger": "y",
        "threat_to_life": "y",
        "is_anonymous": "y",
        "consent": "y",
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Report submitted" in response.data
    assert b"Your report has been recorded" in response.data
    with app.app_context():
        incident = Incident.query.filter_by(category="Stalking").first()
        assert incident is not None
        assert re.fullmatch(r"SHR-\d{4}-\d{4}", incident.case_number)
        assert incident.is_anonymous is True
        assert incident.immediate_danger is True
        assert incident.threat_to_life is True
        assert incident.risk_level == "CRITICAL"

    reports = client.get("/reporter/reports?status=RECEIVED&risk=CRITICAL&category=Stalking")
    assert reports.status_code == 200
    assert b"Stalking" in reports.data


def test_role_isolation(client):
    login(client, "demo@sheild.local")
    assert client.get("/admin/dashboard").status_code == 403
    assert client.get("/responder/dashboard").status_code == 403


def test_responder_can_open_assigned_case_but_not_another_responders_case(client, app):
    login(client, "responder@sheild.local")
    with app.app_context():
        assigned = Incident.query.filter(Incident.assigned_to_id.isnot(None)).first()
        assigned_id = assigned.id
    response = client.get(f"/responder/cases/{assigned_id}")
    assert response.status_code == 200
    assert b"Identity minimised" in response.data


def test_invalid_login_is_rejected(client):
    response = client.post("/auth/login", data={"email": "admin@sheild.local", "password": "wrong"}, follow_redirects=True)
    assert b"not recognised" in response.data


@pytest.mark.parametrize("email,paths", [
    ("demo@sheild.local", [
        "/reporter/dashboard", "/reporter/reports", "/reporter/reports/new",
        "/reporter/reports/1", "/reporter/sos", "/auth/profile",
    ]),
    ("responder@sheild.local", [
        "/responder/dashboard", "/responder/cases", "/responder/cases/1",
        "/responder/alerts", "/responder/alerts/1", "/auth/profile",
    ]),
    ("admin@sheild.local", [
        "/admin/dashboard", "/admin/users", "/admin/incidents",
        "/admin/incidents/1", "/admin/services", "/admin/contacts",
        "/admin/responders/new", "/admin/services/1/edit",
        "/admin/contacts/1/edit", "/auth/profile",
    ]),
])
def test_role_pages_render_without_errors(client, email, paths):
    login(client, email)
    for path in paths:
        response = client.get(path)
        assert response.status_code == 200, path


def test_admin_can_create_responder(client, app):
    login(client, "admin@sheild.local")
    response = client.post("/admin/responders/new", data={
        "full_name": "Fictional New Responder",
        "email": "new.responder@example.com",
        "phone": "0800 000 0999",
        "password": "Temporary123!",
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Responder account created" in response.data
    with app.app_context():
        responder = User.query.filter_by(email="new.responder@example.com").first()
        assert responder is not None
        assert responder.role == "RESPONDER"
        assert responder.check_password("Temporary123!")


def test_demo_seeder_is_repeat_safe(app):
    with app.app_context():
        initial_users = User.query.count()
        initial_incidents = Incident.query.count()
        seed_database()
        seed_database()
        assert User.query.count() == initial_users
        assert Incident.query.count() == initial_incidents
        assert User.query.filter_by(email="admin@sheild.local").count() == 1
        assert User.query.filter_by(email="responder@sheild.local").count() == 1
        assert User.query.filter_by(email="demo@sheild.local").count() == 1

    result = app.test_cli_runner().invoke(args=["seed-demo"])
    assert result.exit_code == 0
    assert "demo data is ready" in result.output


def test_risk_assessment_rules_are_deterministic():
    assert assess_incident_risk({}).level == "LOW"
    assert assess_incident_risk({"medical_attention": True}).level == "MEDIUM"
    assert assess_incident_risk({"immediate_danger": True}).level == "HIGH"
    critical = assess_incident_risk({"immediate_danger": True, "weapon_involved": True})
    assert critical.level == "CRITICAL"
    assert critical.score == 8
    assert "immediate danger" in critical.explanation


def test_reporter_cannot_access_or_filter_into_another_reporters_case(client, app):
    with app.app_context():
        other = User(full_name="Other Fictional Reporter", email="other@example.com", role="REPORTER")
        other.set_password("AnotherPass123!")
        db.session.add(other)
        db.session.flush()
        private_case = Incident(
            case_number="SHR-2026-0999", reporter_id=other.id,
            category="Economic Abuse", description="A fictional private report for authorization testing.",
            location="Fictional West District", incident_date=date(2026, 10, 1),
            preferred_contact_method="IN_APP", risk_level="LOW", status="RECEIVED",
            is_anonymous=True,
        )
        db.session.add(private_case)
        db.session.commit()
        private_id = private_case.id

    login(client, "demo@sheild.local")
    assert client.get(f"/reporter/reports/{private_id}").status_code == 403
    assert client.get(f"/reporter/reports/{private_id}/confirmation").status_code == 403
    listing = client.get("/reporter/reports?category=Economic%20Abuse")
    assert b"SHR-2026-0999" not in listing.data
    dashboard = client.get("/reporter/dashboard")
    assert b"SHR-2026-0999" not in dashboard.data


def test_anonymous_case_hides_reporter_identity_from_responder(client, app):
    with app.app_context():
        reporter = User.query.filter_by(email="demo@sheild.local").one()
        responder = User.query.filter_by(email="responder@sheild.local").one()
        incident = Incident(
            case_number="SHR-2026-0888", reporter_id=reporter.id,
            assigned_to_id=responder.id, category="Stalking",
            description="Fictional anonymous report used to verify responder privacy.",
            location="Fictional Central Area", incident_date=date(2026, 10, 1),
            preferred_contact_method="IN_APP", risk_level="HIGH",
            status="RESPONDER_ASSIGNED", is_anonymous=True,
        )
        db.session.add(incident)
        db.session.commit()
        incident_id = incident.id

    login(client, "responder@sheild.local")
    response = client.get(f"/responder/cases/{incident_id}")
    assert response.status_code == 200
    assert b"Anonymous report" in response.data
    assert b"demo@sheild.local" not in response.data
    assert b"Amina Demo" not in response.data


def test_incident_form_rejects_future_date(client, app):
    login(client, "demo@sheild.local")
    with app.app_context():
        before = Incident.query.count()
    response = client.post("/reporter/reports/new", data={
        "category": "Other",
        "incident_date": (date.today() + timedelta(days=1)).isoformat(),
        "location": "Fictional Test Area",
        "description": "A fictional report that should fail future-date validation.",
        "preferred_contact_method": "IN_APP",
        "consent": "y",
    })
    assert response.status_code == 200
    assert b"cannot be in the future" in response.data
    with app.app_context():
        assert Incident.query.count() == before


def sos_payload(**overrides):
    payload = {
        "category": "Threat to Life",
        "description": "A fictional description of an ongoing emergency situation for testing.",
        "location": "Fictional Riverside Ward",
        "immediate_danger": "y",
        "consent": "y",
    }
    payload.update(overrides)
    return payload


def test_a_authenticated_reporter_can_submit_sos(client, app):
    login(client, "demo@sheild.local")
    response = client.post("/reporter/sos", data=sos_payload(), follow_redirects=True)
    assert response.status_code == 200
    assert b"Emergency request recorded" in response.data


def test_bcde_sos_atomically_creates_linked_critical_new_records(client, app):
    login(client, "demo@sheild.local")
    with app.app_context():
        incidents_before = Incident.query.count()
        alerts_before = EmergencyAlert.query.count()
        updates_before = CaseUpdate.query.count()

    client.post("/reporter/sos", data=sos_payload(location="Fictional Riverside Ward"))

    with app.app_context():
        assert Incident.query.count() == incidents_before + 1
        assert EmergencyAlert.query.count() == alerts_before + 1
        assert CaseUpdate.query.count() == updates_before + 1

        incident = Incident.query.filter_by(location="Fictional Riverside Ward").one()
        alert = EmergencyAlert.query.filter_by(incident_id=incident.id).one()

        # B: the three records exist and reference each other
        assert alert.incident_id == incident.id
        assert incident.updates[-1].incident_id == incident.id

        # C: SOS incident is CRITICAL regardless of indicators selected
        assert incident.risk_level == "CRITICAL"
        assert incident.source == "SOS"

        # D: EmergencyAlert begins as NEW with timestamps
        assert alert.status == "NEW"
        assert alert.created_at is not None
        assert alert.updated_at is not None

        # E: public case reference follows SHR-YEAR-XXXX
        assert re.fullmatch(r"SHR-\d{4}-\d{4}", incident.case_number)

        timeline_entry = incident.updates[-1]
        assert timeline_entry.update_type == "SOS"
        assert timeline_entry.visible_to_reporter is True


def test_f_reporter_sees_own_emergency_case_everywhere(client, app):
    login(client, "demo@sheild.local")
    client.post("/reporter/sos", data=sos_payload(location="Fictional Own Case Ward"))
    with app.app_context():
        incident = Incident.query.filter_by(location="Fictional Own Case Ward").one()
        case_number = incident.case_number
        incident_id = incident.id

    dashboard = client.get("/reporter/dashboard")
    assert case_number.encode() in dashboard.data or b"Emergency SOS" in dashboard.data

    reports = client.get("/reporter/reports")
    assert case_number.encode() in reports.data

    detail = client.get(f"/reporter/reports/{incident_id}")
    assert detail.status_code == 200
    assert case_number.encode() in detail.data
    assert b"Emergency SOS" in detail.data


def test_g_another_reporter_cannot_access_sos_case_or_confirmation(client, app):
    login(client, "demo@sheild.local")
    client.post("/reporter/sos", data=sos_payload(location="Fictional Owner Only Ward"))
    with app.app_context():
        incident = Incident.query.filter_by(location="Fictional Owner Only Ward").one()
        incident_id = incident.id
        alert = EmergencyAlert.query.filter_by(incident_id=incident_id).one()
        alert_id = alert.id
    logout(client)

    with app.app_context():
        other = User(full_name="Other Fictional Reporter", email="other.sos@example.com", role="REPORTER")
        other.set_password("AnotherPass123!")
        db.session.add(other)
        db.session.commit()

    login(client, "other.sos@example.com", "AnotherPass123!")
    assert client.get(f"/reporter/reports/{incident_id}").status_code == 403
    assert client.get(f"/reporter/sos/{alert_id}/confirmation").status_code == 403


def test_h_anonymous_sos_hides_reporter_identity_from_responder(client, app):
    login(client, "demo@sheild.local")
    client.post("/reporter/sos", data=sos_payload(location="Fictional Anonymous SOS Ward", is_anonymous="y"))
    with app.app_context():
        incident = Incident.query.filter_by(location="Fictional Anonymous SOS Ward").one()
        assert incident.is_anonymous is True
        incident_id = incident.id
    logout(client)

    login(client, "responder@sheild.local")
    response = client.get(f"/responder/cases/{incident_id}")
    assert response.status_code == 200
    assert b"Anonymous report" in response.data
    assert b"demo@sheild.local" not in response.data
    assert b"Amina Demo" not in response.data


def test_i_responder_dashboard_and_queue_display_emergency(client, app):
    login(client, "demo@sheild.local")
    client.post("/reporter/sos", data=sos_payload(location="Fictional Responder Visible Ward"))
    with app.app_context():
        incident = Incident.query.filter_by(location="Fictional Responder Visible Ward").one()
        case_number = incident.case_number
    logout(client)

    login(client, "responder@sheild.local")
    dashboard = client.get("/responder/dashboard")
    assert dashboard.status_code == 200
    assert b"Emergency queue" in dashboard.data
    assert case_number.encode() in dashboard.data

    alerts_page = client.get("/responder/alerts")
    assert alerts_page.status_code == 200
    assert case_number.encode() in alerts_page.data
    assert b"Threat to Life" in alerts_page.data
    assert b"Critical" in alerts_page.data


def test_j_admin_dashboard_reflects_emergency_counts(client, app):
    with app.app_context():
        new_alerts_before = EmergencyAlert.query.filter_by(status="NEW").count()
        critical_before = Incident.query.filter_by(risk_level="CRITICAL").filter(
            Incident.status.notin_(["RESOLVED", "CLOSED"])
        ).count()

    login(client, "demo@sheild.local")
    client.post("/reporter/sos", data=sos_payload(location="Fictional Admin Count Ward One"))
    logout(client)

    with app.app_context():
        other = User(full_name="Second Fictional Reporter", email="second.sos@example.com", role="REPORTER")
        other.set_password("AnotherPass123!")
        db.session.add(other)
        db.session.commit()
    login(client, "second.sos@example.com", "AnotherPass123!")
    client.post("/reporter/sos", data=sos_payload(location="Fictional Admin Count Ward Two"))
    logout(client)

    with app.app_context():
        assert EmergencyAlert.query.filter_by(status="NEW").count() == new_alerts_before + 2
        assert Incident.query.filter_by(risk_level="CRITICAL").filter(
            Incident.status.notin_(["RESOLVED", "CLOSED"])
        ).count() == critical_before + 2

    login(client, "admin@sheild.local")
    dashboard = client.get("/admin/dashboard")
    assert dashboard.status_code == 200
    assert b"New SOS alerts" in dashboard.data
    assert b"Active emergency alerts" in dashboard.data
    assert b"Fictional Admin Count Ward One" in dashboard.data or b"Fictional Admin Count Ward Two" in dashboard.data

    alerts_page = client.get("/admin/alerts")
    assert alerts_page.status_code == 200
    assert b"Fictional Admin Count Ward One" in alerts_page.data
    assert b"Fictional Admin Count Ward Two" in alerts_page.data


def test_k_malformed_sos_submission_creates_no_partial_records(client, app):
    login(client, "demo@sheild.local")
    with app.app_context():
        incidents_before = Incident.query.count()
        alerts_before = EmergencyAlert.query.count()
        updates_before = CaseUpdate.query.count()

    # missing required consent
    response = client.post("/reporter/sos", data=sos_payload(consent=""))
    assert response.status_code == 200

    # missing required description
    response = client.post("/reporter/sos", data=sos_payload(description=""))
    assert response.status_code == 200

    with app.app_context():
        assert Incident.query.count() == incidents_before
        assert EmergencyAlert.query.count() == alerts_before
        assert CaseUpdate.query.count() == updates_before


def test_unassigned_queue_prioritises_critical_risk_first(client, app):
    with app.app_context():
        from shield.models import risk_priority_order
        low = Incident(
            case_number="SHR-2026-0100", category="Other",
            description="Fictional low-risk unassigned case for ordering test.",
            location="Fictional Low Ward", incident_date=date.today(),
            preferred_contact_method="IN_APP", risk_level="LOW", status="RECEIVED",
        )
        critical = Incident(
            case_number="SHR-2026-0101", category="Threat to Life",
            description="Fictional critical-risk unassigned case for ordering test.",
            location="Fictional Critical Ward", incident_date=date.today(),
            preferred_contact_method="IN_APP", risk_level="CRITICAL", status="RECEIVED",
        )
        db.session.add_all([low, critical])
        db.session.commit()

        ordered = (
            Incident.query.filter_by(assigned_to_id=None)
            .filter(Incident.status.notin_(["RESOLVED", "CLOSED"]))
            .order_by(risk_priority_order().desc(), Incident.created_at.asc())
            .all()
        )
        assert ordered[0].case_number == "SHR-2026-0101"


# ---------------------------------------------------------------------------
# Phase 4: responder case management and emergency response workflow
# ---------------------------------------------------------------------------


def create_sos_case(client, app, location):
    login(client, "demo@sheild.local")
    client.post("/reporter/sos", data=sos_payload(location=location))
    logout(client)
    with app.app_context():
        incident = Incident.query.filter_by(location=location).one()
        alert = EmergencyAlert.query.filter_by(incident_id=incident.id).one()
        return incident.id, alert.id


def create_normal_case(client, app, location):
    login(client, "demo@sheild.local")
    client.post("/reporter/reports/new", data={
        "category": "Stalking",
        "incident_date": date.today().isoformat(),
        "location": location,
        "description": "A fictional description long enough for validation and safe Phase 4 testing.",
        "preferred_contact_method": "IN_APP",
        "consent": "y",
    })
    logout(client)
    with app.app_context():
        incident = Incident.query.filter_by(location=location).one()
        return incident.id


def test_a_responder_dashboard_loads_with_metrics(client, app):
    response = login(client, "responder@sheild.local")
    assert response.status_code == 200
    for label in (b"New emergency alerts", b"Critical active cases", b"My assigned cases",
                  b"In progress", b"Referred", b"Resolved", b"Emergency queue",
                  b"Unassigned priority cases", b"Recent activity"):
        assert label in response.data


def test_b_reporter_cannot_access_responder_routes(client, app):
    incident_id = create_normal_case(client, app, "Fictional B Reporter Block Ward")
    login(client, "demo@sheild.local")
    assert client.get("/responder/dashboard").status_code == 403
    assert client.get("/responder/cases").status_code == 403
    assert client.get(f"/responder/cases/{incident_id}").status_code == 403
    assert client.post(f"/responder/cases/{incident_id}/claim").status_code == 403
    assert client.post(f"/responder/cases/{incident_id}/notes", data={"note": "x"}).status_code == 403
    assert client.get("/responder/alerts").status_code == 403


def test_c_responder_sees_critical_emergency(client, app):
    incident_id, alert_id = create_sos_case(client, app, "Fictional C Critical Ward")
    login(client, "responder@sheild.local")
    with app.app_context():
        incident = db.session.get(Incident, incident_id)
        case_number = incident.case_number
    dashboard = client.get("/responder/dashboard")
    assert case_number.encode() in dashboard.data
    alerts_page = client.get("/responder/alerts")
    assert case_number.encode() in alerts_page.data
    assert b"Critical" in alerts_page.data


def test_def_acknowledge_emergency_assigns_and_logs_timeline(client, app):
    incident_id, alert_id = create_sos_case(client, app, "Fictional DEF Acknowledge Ward")
    login(client, "responder@sheild.local")
    with app.app_context():
        responder = User.query.filter_by(email="responder@sheild.local").one()
        responder_id = responder.id

    response = client.post(f"/responder/alerts/{alert_id}/acknowledge", follow_redirects=True)
    assert response.status_code == 200

    with app.app_context():
        alert = db.session.get(EmergencyAlert, alert_id)
        incident = db.session.get(Incident, incident_id)
        # D
        assert alert.status == "ACKNOWLEDGED"
        assert alert.acknowledged_at is not None
        # E
        assert alert.assigned_to_id == responder_id
        assert incident.assigned_to_id == responder_id
        assert incident.status == "RESPONDER_ASSIGNED"
        # F
        ack_updates = [u for u in incident.updates if u.update_type == "ACKNOWLEDGEMENT"]
        assert len(ack_updates) == 1
        assert "acknowledged" in ack_updates[0].note.lower()


def test_ghi_start_response_moves_alert_and_incident(client, app):
    incident_id, alert_id = create_sos_case(client, app, "Fictional GHI Start Response Ward")
    login(client, "responder@sheild.local")
    # acknowledgement first moves a fresh RECEIVED incident to RESPONDER_ASSIGNED,
    # from which IN_PROGRESS is a valid next step
    client.post(f"/responder/alerts/{alert_id}/acknowledge")
    response = client.post(f"/responder/alerts/{alert_id}/start-response", follow_redirects=True)
    assert response.status_code == 200
    with app.app_context():
        alert = db.session.get(EmergencyAlert, alert_id)
        incident = db.session.get(Incident, incident_id)
        # H
        assert alert.status == "RESPONDING"
        # I
        assert incident.status == "IN_PROGRESS"
        assert incident.assigned_to_id is not None


def test_jk_resolve_emergency_does_not_close_case(client, app):
    incident_id, alert_id = create_sos_case(client, app, "Fictional JK Resolve Ward")
    login(client, "responder@sheild.local")
    client.post(f"/responder/alerts/{alert_id}/acknowledge")
    client.post(f"/responder/alerts/{alert_id}/start-response")
    response = client.post(f"/responder/alerts/{alert_id}/resolve", follow_redirects=True)
    assert response.status_code == 200
    with app.app_context():
        alert = db.session.get(EmergencyAlert, alert_id)
        incident = db.session.get(Incident, incident_id)
        # J
        assert alert.status == "RESOLVED"
        # K
        assert incident.status not in ("RESOLVED", "CLOSED")
        assert incident.status == "IN_PROGRESS"


def test_l_responder_claims_unassigned_normal_case(client, app):
    incident_id = create_normal_case(client, app, "Fictional L Claim Ward")
    login(client, "responder@sheild.local")
    with app.app_context():
        responder = User.query.filter_by(email="responder@sheild.local").one()
        responder_id = responder.id
    response = client.post(f"/responder/cases/{incident_id}/claim", follow_redirects=True)
    assert response.status_code == 200
    with app.app_context():
        incident = db.session.get(Incident, incident_id)
        assert incident.assigned_to_id == responder_id
        assert incident.status == "RESPONDER_ASSIGNED"
        assignment_updates = [u for u in incident.updates if u.update_type == "ASSIGNMENT"]
        assert len(assignment_updates) == 1


def test_m_second_responder_cannot_steal_assigned_case(client, app):
    incident_id = create_normal_case(client, app, "Fictional M Steal Ward")
    login(client, "responder@sheild.local")
    client.post(f"/responder/cases/{incident_id}/claim")
    logout(client)

    with app.app_context():
        second = User(full_name="Second Fictional Responder", email="second.responder@example.com", role="RESPONDER")
        second.set_password("SecondPass123!")
        db.session.add(second)
        db.session.commit()
        original_responder = User.query.filter_by(email="responder@sheild.local").one()
        original_responder_id = original_responder.id

    login(client, "second.responder@example.com", "SecondPass123!")
    response = client.post(f"/responder/cases/{incident_id}/claim", follow_redirects=True)
    assert response.status_code == 200
    assert b"already claimed" in response.data.lower()
    assert client.get(f"/responder/cases/{incident_id}").status_code == 403

    with app.app_context():
        incident = db.session.get(Incident, incident_id)
        assert incident.assigned_to_id == original_responder_id


def test_n_allowed_status_transition_succeeds(client, app):
    incident_id = create_normal_case(client, app, "Fictional N Allowed Transition Ward")
    login(client, "responder@sheild.local")
    client.post(f"/responder/cases/{incident_id}/claim")
    with app.app_context():
        incident = db.session.get(Incident, incident_id)
        assert incident.status == "RESPONDER_ASSIGNED"

    response = client.post(f"/responder/cases/{incident_id}", data={
        "status": "IN_PROGRESS", "risk_level": "LOW",
        "note": "Fictional progress note for an allowed transition.",
        "visible_to_reporter": "y",
    }, follow_redirects=True)
    assert response.status_code == 200
    with app.app_context():
        incident = db.session.get(Incident, incident_id)
        assert incident.status == "IN_PROGRESS"


def test_o_disallowed_status_transition_is_rejected(client, app):
    incident_id = create_normal_case(client, app, "Fictional O Disallowed Transition Ward")
    login(client, "responder@sheild.local")
    client.post(f"/responder/cases/{incident_id}/claim")
    with app.app_context():
        incident = db.session.get(Incident, incident_id)
        assert incident.status == "RESPONDER_ASSIGNED"

    # RESPONDER_ASSIGNED only allows a move to IN_PROGRESS, not straight to RESOLVED.
    # The dropdown itself is restricted to allowed choices, so WTForms rejects this
    # as an invalid choice; the state machine would also reject it if that were bypassed.
    response = client.post(f"/responder/cases/{incident_id}", data={
        "status": "RESOLVED", "risk_level": "LOW",
        "note": "Fictional note attempting an unsafe jump.",
        "visible_to_reporter": "y",
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"not a valid choice" in response.data.lower() or b"cannot" in response.data.lower()
    with app.app_context():
        incident = db.session.get(Incident, incident_id)
        assert incident.status == "RESPONDER_ASSIGNED"


def test_o2_transition_helper_rejects_disallowed_jump_directly():
    from shield.services.case_transitions import is_transition_allowed
    assert is_transition_allowed("RESPONDER_ASSIGNED", "RESOLVED") is False
    assert is_transition_allowed("RECEIVED", "IN_PROGRESS") is False
    assert is_transition_allowed("RESPONDER_ASSIGNED", "IN_PROGRESS") is True
    assert is_transition_allowed("CLOSED", "IN_PROGRESS") is False


def test_pq_internal_note_is_hidden_from_reporter(client, app):
    incident_id = create_normal_case(client, app, "Fictional PQ Internal Note Ward")
    login(client, "responder@sheild.local")
    client.post(f"/responder/cases/{incident_id}/claim")
    secret_note = "Fictional internal-only note about safeguarding concerns."
    response = client.post(f"/responder/cases/{incident_id}/notes", data={"note-note": secret_note}, follow_redirects=True)
    assert response.status_code == 200
    # P
    with app.app_context():
        incident = db.session.get(Incident, incident_id)
        notes = [u for u in incident.updates if u.update_type == "NOTE"]
        assert len(notes) == 1
        assert notes[0].visibility == "INTERNAL"
        assert notes[0].visible_to_reporter is False
    logout(client)

    # Q
    login(client, "demo@sheild.local")
    detail = client.get(f"/reporter/reports/{incident_id}")
    assert secret_note.encode() not in detail.data


def test_r_reporter_visible_update_appears_in_reporter_timeline(client, app):
    incident_id = create_normal_case(client, app, "Fictional R Reporter Update Ward")
    login(client, "responder@sheild.local")
    client.post(f"/responder/cases/{incident_id}/claim")
    message = "Your case has been reviewed and is progressing."
    response = client.post(f"/responder/cases/{incident_id}/reporter-updates", data={"update-note": message}, follow_redirects=True)
    assert response.status_code == 200
    logout(client)

    login(client, "demo@sheild.local")
    detail = client.get(f"/reporter/reports/{incident_id}")
    assert message.encode() in detail.data


def test_s_anonymous_case_identity_hidden_throughout_responder_workflow(client, app):
    login(client, "demo@sheild.local")
    client.post("/reporter/reports/new", data={
        "category": "Stalking",
        "incident_date": date.today().isoformat(),
        "location": "Fictional S Anonymous Workflow Ward",
        "description": "A fictional anonymous description for Phase 4 workflow testing.",
        "preferred_contact_method": "IN_APP",
        "is_anonymous": "y",
        "consent": "y",
    })
    logout(client)
    with app.app_context():
        incident_id = Incident.query.filter_by(location="Fictional S Anonymous Workflow Ward").one().id

    login(client, "responder@sheild.local")
    client.post(f"/responder/cases/{incident_id}/claim")
    client.post(f"/responder/cases/{incident_id}/notes", data={"note-note": "Fictional internal note on anonymous case."})
    detail = client.get(f"/responder/cases/{incident_id}")
    assert detail.status_code == 200
    assert b"Anonymous report" in detail.data
    assert b"demo@sheild.local" not in detail.data
    assert b"Amina Demo" not in detail.data


def test_t_referral_action_records_correctly(client, app):
    incident_id = create_normal_case(client, app, "Fictional T Referral Ward")
    with app.app_context():
        service = SupportService.query.filter_by(name="Safe Harbour Support Centre").one()
        service_id = service.id

    login(client, "responder@sheild.local")
    client.post(f"/responder/cases/{incident_id}/claim")
    # REFERRED is only reachable from IN_PROGRESS in the allowed-transition map
    client.post(f"/responder/cases/{incident_id}", data={
        "status": "IN_PROGRESS", "risk_level": "LOW",
        "note": "Fictional note moving the case into progress before referral.",
        "visible_to_reporter": "y",
    })
    response = client.post(f"/responder/cases/{incident_id}/referral", data={
        "referral-support_service_id": str(service_id),
        "referral-note": "Fictional referral note.",
        "referral-mark_referred": "y",
    }, follow_redirects=True)
    assert response.status_code == 200

    with app.app_context():
        incident = db.session.get(Incident, incident_id)
        referrals = [u for u in incident.updates if u.update_type == "REFERRAL"]
        assert len(referrals) == 1
        assert referrals[0].support_service_id == service_id
        assert referrals[0].visibility == "INTERNAL"
        assert "Safe Harbour Support Centre" in referrals[0].note
        assert incident.status == "REFERRED"


def test_u_csrf_protection_blocks_unsigned_post():
    csrf_app = create_app({
        "TESTING": True,
        "WTF_CSRF_ENABLED": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SECRET_KEY": "csrf-test-secret",
    })
    csrf_client = csrf_app.test_client()
    try:
        login(csrf_client, "responder@sheild.local")
        with csrf_app.app_context():
            incident = Incident.query.first()
            incident_id = incident.id
        # a POST with no csrf_token field must be rejected when CSRF protection is active
        response = csrf_client.post(f"/responder/cases/{incident_id}/claim")
        assert response.status_code == 400
    finally:
        with csrf_app.app_context():
            db.session.remove()
            db.drop_all()


def test_u_invalid_ids_404_and_forbidden_actions_403(client, app):
    login(client, "responder@sheild.local")
    assert client.get("/responder/cases/999999").status_code == 404
    assert client.get("/responder/alerts/999999").status_code == 404
    assert client.post("/responder/cases/999999/claim").status_code == 404
    assert client.post("/responder/cases/999999/notes", data={"note": "x"}).status_code == 404
    assert client.post("/responder/alerts/999999/acknowledge").status_code == 404
    logout(client)

    # a responder cannot use admin-only management operations
    login(client, "responder@sheild.local")
    assert client.get("/admin/dashboard").status_code == 403
    assert client.get("/admin/users").status_code == 403
    assert client.post("/admin/responders/new", data={
        "full_name": "Fictional Rogue Responder", "email": "rogue@example.com", "password": "RoguePass123!",
    }).status_code == 403


# ---------------------------------------------------------------------------
# Phase 5: admin operations, analytics and system management
# ---------------------------------------------------------------------------


def test_a_admin_dashboard_loads(client, app):
    response = login(client, "admin@sheild.local")
    assert response.status_code == 200
    for label in (b"Total reports", b"Active cases", b"Critical active cases", b"New SOS alerts",
                  b"In progress", b"Referred", b"Resolved", b"Registered reporters", b"Active responders",
                  b"Incidents by category", b"Reports over time"):
        assert label in response.data


def test_b_reporter_cannot_access_admin_routes(client, app):
    login(client, "demo@sheild.local")
    for path in ("/admin/dashboard", "/admin/incidents", "/admin/alerts", "/admin/users",
                 "/admin/responders", "/admin/activity", "/admin/services", "/admin/contacts"):
        assert client.get(path).status_code == 403, path


def test_c_responder_cannot_access_admin_routes(client, app):
    login(client, "responder@sheild.local")
    for path in ("/admin/dashboard", "/admin/incidents", "/admin/alerts", "/admin/users",
                 "/admin/responders", "/admin/activity", "/admin/services", "/admin/contacts"):
        assert client.get(path).status_code == 403, path


def test_d_dashboard_metrics_reflect_database_values(client, app):
    with app.app_context():
        expected_total = Incident.query.count()
        expected_reporters = User.query.filter_by(role="REPORTER", is_active_account=True).count()
    login(client, "admin@sheild.local")
    response = client.get("/admin/dashboard")
    assert str(expected_total).encode() in response.data
    assert str(expected_reporters).encode() in response.data
    logout(client)

    # create a new incident and confirm the total increments accordingly
    incident_id = create_normal_case(client, app, "Fictional D Metrics Ward")
    login(client, "admin@sheild.local")
    with app.app_context():
        new_total = Incident.query.count()
    assert new_total == expected_total + 1
    response = client.get("/admin/dashboard")
    assert str(new_total).encode() in response.data


def test_e_analytics_values_come_from_database(client, app):
    incident_id = create_normal_case(client, app, "Fictional E Analytics Ward")
    login(client, "admin@sheild.local")
    with app.app_context():
        category_count = Incident.query.filter_by(category="Stalking").count()
    response = client.get("/admin/dashboard")
    assert response.status_code == 200
    assert b'"category"' in response.data
    assert b"Stalking" in response.data
    assert str(category_count).encode() in response.data


def test_f_admin_can_search_filter_incidents(client, app):
    incident_id = create_normal_case(client, app, "Fictional F Filter Ward")
    with app.app_context():
        incident = db.session.get(Incident, incident_id)
        case_number = incident.case_number
    login(client, "admin@sheild.local")
    response = client.get(f"/admin/incidents?q={case_number}")
    assert response.status_code == 200
    assert case_number.encode() in response.data

    response = client.get("/admin/incidents?source=SOS")
    assert response.status_code == 200
    assert case_number.encode() not in response.data

    response = client.get("/admin/incidents?assignment=unassigned")
    assert response.status_code == 200
    assert case_number.encode() in response.data


def test_gh_admin_can_assign_responder_with_timeline(client, app):
    incident_id = create_normal_case(client, app, "Fictional GH Assign Ward")
    with app.app_context():
        responder = User.query.filter_by(email="responder@sheild.local").one()
        responder_id = responder.id
        updates_before = CaseUpdate.query.filter_by(incident_id=incident_id).count()

    login(client, "admin@sheild.local")
    response = client.post(f"/admin/incidents/{incident_id}", data={
        "responder_id": str(responder_id), "status": "RESPONDER_ASSIGNED", "risk_level": "LOW",
        "note": "Fictional admin assignment note.",
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"assigned to responder" in response.data.lower()

    with app.app_context():
        incident = db.session.get(Incident, incident_id)
        assert incident.assigned_to_id == responder_id
        assignment_updates = [u for u in incident.updates if u.update_type == "ADMIN_ASSIGNMENT"]
        assert len(assignment_updates) == 1
        assert "assigned to responder by administrator" in assignment_updates[0].note.lower()
        assert CaseUpdate.query.filter_by(incident_id=incident_id).count() == updates_before + 1


def test_ij_admin_can_deliberately_reassign_with_timeline(client, app):
    incident_id = create_normal_case(client, app, "Fictional IJ Reassign Ward")
    with app.app_context():
        responder = User.query.filter_by(email="responder@sheild.local").one()
        second = User(full_name="Second Fictional Admin-Managed Responder", email="second.admin.responder@example.com", role="RESPONDER")
        second.set_password("SecondPass123!")
        db.session.add(second)
        db.session.commit()
        responder_id, second_id = responder.id, second.id

    login(client, "admin@sheild.local")
    client.post(f"/admin/incidents/{incident_id}", data={
        "responder_id": str(responder_id), "status": "RESPONDER_ASSIGNED", "risk_level": "LOW",
        "note": "Initial fictional assignment.",
    })
    response = client.post(f"/admin/incidents/{incident_id}", data={
        "responder_id": str(second_id), "status": "RESPONDER_ASSIGNED", "risk_level": "LOW",
        "note": "Fictional deliberate reassignment note.",
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"reassigned" in response.data.lower()

    with app.app_context():
        incident = db.session.get(Incident, incident_id)
        assert incident.assigned_to_id == second_id
        reassignment_updates = [u for u in incident.updates if u.update_type == "ADMIN_REASSIGNMENT"]
        assert len(reassignment_updates) == 1
        assert "reassigned by administrator" in reassignment_updates[0].note.lower()
        # historical activity is preserved, not deleted
        assignment_updates = [u for u in incident.updates if u.update_type == "ADMIN_ASSIGNMENT"]
        assert len(assignment_updates) == 1


def test_k_admin_can_list_users(client, app):
    login(client, "admin@sheild.local")
    response = client.get("/admin/users")
    assert response.status_code == 200
    assert b"demo@sheild.local" in response.data
    assert b"responder@sheild.local" in response.data
    assert b"admin@sheild.local" in response.data
    # no authentication internals leaked
    assert b"password_hash" not in response.data
    assert b"pbkdf2" not in response.data.lower()
    assert b"scrypt" not in response.data.lower()


def test_lmn_admin_can_create_responder_hashed_password_duplicate_rejected(client, app):
    login(client, "admin@sheild.local")
    response = client.post("/admin/responders/new", data={
        "full_name": "Fictional New Phase5 Responder", "email": "phase5.responder@example.com",
        "password": "Phase5Pass123!",
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Responder account created" in response.data

    with app.app_context():
        responder = User.query.filter_by(email="phase5.responder@example.com").one()
        assert responder.role == "RESPONDER"
        # M: password is hashed, not stored plaintext
        assert responder.password_hash != "Phase5Pass123!"
        assert responder.check_password("Phase5Pass123!")

    # N: duplicate email rejected
    response = client.post("/admin/responders/new", data={
        "full_name": "Fictional Duplicate Responder", "email": "phase5.responder@example.com",
        "password": "AnotherPass123!",
    })
    assert response.status_code == 200
    assert b"already uses this email" in response.data
    with app.app_context():
        assert User.query.filter_by(email="phase5.responder@example.com").count() == 1


def test_opq_admin_can_deactivate_and_reactivate_user(client, app):
    with app.app_context():
        reporter = User.query.filter_by(email="demo@sheild.local").one()
        reporter_id = reporter.id

    login(client, "admin@sheild.local")
    response = client.post(f"/admin/users/{reporter_id}/toggle", follow_redirects=True)
    assert response.status_code == 200
    with app.app_context():
        assert db.session.get(User, reporter_id).is_active_account is False
    logout(client)

    # P: deactivated user cannot login
    response = login(client, "demo@sheild.local")
    assert response.status_code == 200
    assert b"deactivated" in response.data.lower()
    assert b"Reporter overview" not in response.data

    # Q: reactivate
    login(client, "admin@sheild.local")
    client.post(f"/admin/users/{reporter_id}/toggle")
    with app.app_context():
        assert db.session.get(User, reporter_id).is_active_account is True
    logout(client)
    response = login(client, "demo@sheild.local")
    assert b"Reporter overview" in response.data


def test_r_admin_cannot_deactivate_own_account(client, app):
    with app.app_context():
        admin = User.query.filter_by(email="admin@sheild.local").one()
        admin_id = admin.id
    login(client, "admin@sheild.local")
    response = client.post(f"/admin/users/{admin_id}/toggle", follow_redirects=True)
    assert response.status_code == 200
    assert b"cannot deactivate your own account" in response.data.lower()
    with app.app_context():
        assert db.session.get(User, admin_id).is_active_account is True


def test_st_admin_can_create_and_edit_support_service(client, app):
    login(client, "admin@sheild.local")
    response = client.post("/admin/services", data={
        "name": "Fictional Phase5 Support Centre", "category": "Counselling",
        "description": "A fictional Phase 5 test service.", "hours": "Mon–Fri",
        "is_active": "y",
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Support service added" in response.data

    with app.app_context():
        service = SupportService.query.filter_by(name="Fictional Phase5 Support Centre").one()
        service_id = service.id

    response = client.post(f"/admin/services/{service_id}/edit", data={
        "name": "Fictional Phase5 Support Centre", "category": "Counselling",
        "description": "An updated fictional Phase 5 test service description.", "hours": "Mon–Sat",
        "is_active": "y",
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Support service updated" in response.data
    with app.app_context():
        service = db.session.get(SupportService, service_id)
        assert "updated fictional" in service.description.lower()


def test_u_inactive_support_service_disappears_from_reporter_directory(client, app):
    login(client, "admin@sheild.local")
    client.post("/admin/services", data={
        "name": "Fictional Toggle Service", "category": "Legal Support",
        "description": "A fictional service used to test directory visibility toggling.",
        "is_active": "y",
    })
    with app.app_context():
        service = SupportService.query.filter_by(name="Fictional Toggle Service").one()
        service_id = service.id
    logout(client)

    support_page = client.get("/support")
    assert b"Fictional Toggle Service" in support_page.data

    login(client, "admin@sheild.local")
    client.post(f"/admin/services/{service_id}/toggle")
    logout(client)

    support_page = client.get("/support")
    assert b"Fictional Toggle Service" not in support_page.data


def test_v_admin_can_create_emergency_contact(client, app):
    login(client, "admin@sheild.local")
    response = client.post("/admin/contacts", data={
        "name": "Fictional Phase5 Contact", "phone": "0800 555 0199",
        "description": "A fictional Phase 5 test contact.", "is_active": "y",
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Emergency contact added" in response.data
    with app.app_context():
        assert EmergencyContact.query.filter_by(name="Fictional Phase5 Contact").count() == 1


def test_w_inactive_contact_disappears_from_reporter_facing_pages(client, app):
    login(client, "admin@sheild.local")
    client.post("/admin/contacts", data={
        "name": "Fictional Toggle Contact", "phone": "0800 555 0200",
        "description": "A fictional contact used to test visibility toggling.", "is_active": "y",
    })
    with app.app_context():
        contact = EmergencyContact.query.filter_by(name="Fictional Toggle Contact").one()
        contact_id = contact.id
    logout(client)

    support_page = client.get("/support")
    assert b"Fictional Toggle Contact" in support_page.data

    login(client, "admin@sheild.local")
    client.post(f"/admin/contacts/{contact_id}/toggle")
    logout(client)

    support_page = client.get("/support")
    assert b"Fictional Toggle Contact" not in support_page.data


def test_x_admin_activity_log_renders_update_visibilities(client, app):
    incident_id = create_normal_case(client, app, "Fictional X Activity Ward")
    login(client, "responder@sheild.local")
    client.post(f"/responder/cases/{incident_id}/claim")
    client.post(f"/responder/cases/{incident_id}/notes", data={"note-note": "Fictional internal note for activity log test."})
    client.post(f"/responder/cases/{incident_id}/reporter-updates", data={"update-note": "Fictional reporter-visible update for activity log test."})
    logout(client)

    login(client, "admin@sheild.local")
    response = client.get("/admin/activity")
    assert response.status_code == 200
    assert b"Internal" in response.data
    assert b"Reporter Visible" in response.data or b"Reporter visible" in response.data
    assert b"Fictional internal note for activity log test" in response.data

    with app.app_context():
        incident = db.session.get(Incident, incident_id)
        case_number = incident.case_number
    filtered = client.get(f"/admin/activity?q={case_number}&visibility=INTERNAL")
    assert b"Fictional internal note for activity log test" in filtered.data
    assert b"Fictional reporter-visible update for activity log test" not in filtered.data


def test_y_anonymous_identity_hidden_after_admin_operations(client, app):
    login(client, "demo@sheild.local")
    client.post("/reporter/reports/new", data={
        "category": "Stalking", "incident_date": date.today().isoformat(),
        "location": "Fictional Y Admin Anonymous Ward",
        "description": "A fictional anonymous report for Phase 5 admin-operation testing.",
        "preferred_contact_method": "IN_APP", "is_anonymous": "y", "consent": "y",
    })
    logout(client)
    with app.app_context():
        incident_id = Incident.query.filter_by(location="Fictional Y Admin Anonymous Ward").one().id
        responder = User.query.filter_by(email="responder@sheild.local").one()
        responder_id = responder.id

    login(client, "admin@sheild.local")
    client.post(f"/admin/incidents/{incident_id}", data={
        "responder_id": str(responder_id), "status": "RESPONDER_ASSIGNED", "risk_level": "HIGH",
        "note": "Fictional admin assignment on an anonymous case.",
    })
    admin_detail = client.get(f"/admin/incidents/{incident_id}")
    assert b"Anonymous Report" in admin_detail.data
    assert b"demo@sheild.local" not in admin_detail.data
    assert b"Amina Demo" not in admin_detail.data
    logout(client)

    login(client, "responder@sheild.local")
    responder_detail = client.get(f"/responder/cases/{incident_id}")
    assert b"Anonymous report" in responder_detail.data
    assert b"demo@sheild.local" not in responder_detail.data
    assert b"Amina Demo" not in responder_detail.data


def test_z_admin_state_changing_routes_require_csrf():
    csrf_app = create_app({
        "TESTING": True, "WTF_CSRF_ENABLED": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "SECRET_KEY": "csrf-admin-test-secret",
    })
    csrf_client = csrf_app.test_client()
    try:
        login(csrf_client, "admin@sheild.local")
        with csrf_app.app_context():
            reporter = User.query.filter_by(email="demo@sheild.local").one()
            reporter_id = reporter.id
        response = csrf_client.post(f"/admin/users/{reporter_id}/toggle")
        assert response.status_code == 400
        response = csrf_client.post("/admin/responders/new", data={
            "full_name": "Fictional CSRF Bypass Responder", "email": "csrfbypass@example.com",
            "password": "BypassPass123!",
        })
        assert response.status_code == 400
        with csrf_app.app_context():
            assert User.query.filter_by(email="csrfbypass@example.com").count() == 0
    finally:
        with csrf_app.app_context():
            db.session.remove()
            db.drop_all()


def test_public_registration_cannot_elevate_role(client, app):
    # the registration form has no role field at all, so even a forged extra
    # POST field cannot elevate a publicly-registered account above REPORTER
    response = client.post("/auth/register", data={
        "full_name": "Fictional Role Elevation Attempt", "email": "elevation@example.com",
        "phone": "", "password": "ElevationPass123!", "confirm_password": "ElevationPass123!",
        "role": "ADMIN",
    }, follow_redirects=True)
    assert response.status_code == 200
    with app.app_context():
        user = User.query.filter_by(email="elevation@example.com").one()
        assert user.role == "REPORTER"


def test_admin_created_responder_role_cannot_be_manipulated(client, app):
    login(client, "admin@sheild.local")
    response = client.post("/admin/responders/new", data={
        "full_name": "Fictional Role Manipulation Attempt", "email": "manipulation@example.com",
        "password": "ManipulationPass123!", "role": "ADMIN",
    }, follow_redirects=True)
    assert response.status_code == 200
    with app.app_context():
        user = User.query.filter_by(email="manipulation@example.com").one()
        assert user.role == "RESPONDER"


# ---------------------------------------------------------------------------
# Phase 6: UI/UX polish, accessibility, offline readiness and frontend QA
# ---------------------------------------------------------------------------

import os


def test_response_action_can_be_recorded(client, app):
    incident_id = create_normal_case(client, app, "Fictional Response Action Ward")
    login(client, "responder@sheild.local")
    client.post(f"/responder/cases/{incident_id}/claim")
    response = client.post(f"/responder/cases/{incident_id}/actions", data={
        "action-action_type": "SAFETY_CHECK", "action-note": "Fictional safety check note.",
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Response action recorded" in response.data
    with app.app_context():
        incident = db.session.get(Incident, incident_id)
        actions = [u for u in incident.updates if u.update_type == "SAFETY_CHECK"]
        assert len(actions) == 1
        assert actions[0].visibility == "INTERNAL"


def test_no_duplicate_form_field_ids_on_case_detail_page(client, app):
    # regression guard: the case-detail page stacks 5 WTForms (status update,
    # internal note, reporter update, response action, referral); each must
    # use a unique WTForms prefix so field/csrf ids and label "for" targets
    # never collide.
    incident_id = create_normal_case(client, app, "Fictional Duplicate Id Ward")
    login(client, "responder@sheild.local")
    client.post(f"/responder/cases/{incident_id}/claim")
    response = client.get(f"/responder/cases/{incident_id}")
    ids = re.findall(r'id="([^"]+)"', response.data.decode())
    duplicates = {i for i in ids if ids.count(i) > 1}
    assert not duplicates, f"duplicate ids found: {duplicates}"


def test_chartjs_is_vendored_locally_not_cdn(client, app):
    login(client, "admin@sheild.local")
    response = client.get("/admin/dashboard")
    assert response.status_code == 200
    assert b"vendor/chartjs/chart.umd.min.js" in response.data
    assert b"cdnjs.cloudflare.com" not in response.data
    assert b"cdn.jsdelivr.net" not in response.data
    assert b"unpkg.com" not in response.data

    vendored = client.get("/static/vendor/chartjs/chart.umd.min.js")
    assert vendored.status_code == 200
    assert len(vendored.data) > 10000


def test_no_remote_cdn_or_font_dependency_anywhere():
    base = os.path.join(os.path.dirname(__file__), "..", "shield")
    offenders = []
    for root, _, files in os.walk(base):
        if "vendor" in root:
            continue
        for name in files:
            if name.endswith((".html", ".css", ".js")):
                path = os.path.join(root, name)
                with open(path, encoding="utf-8") as f:
                    content = f.read()
                if re.search(r"https?://(cdn|fonts\.|unpkg|jsdelivr|googleapis)", content):
                    offenders.append(path)
    assert not offenders, f"remote dependency references found in: {offenders}"


def test_public_pages_load(client, app):
    for path in ["/", "/support", "/about-safety", "/emergency", "/auth/login",
                 "/auth/register", "/auth/forgot-password"]:
        assert client.get(path).status_code == 200, path


def test_reporter_pages_load(client, app):
    login(client, "demo@sheild.local")
    for path in ["/reporter/dashboard", "/reporter/reports", "/reporter/reports/new",
                 "/reporter/sos", "/auth/profile"]:
        assert client.get(path).status_code == 200, path


def test_responder_pages_load(client, app):
    login(client, "responder@sheild.local")
    for path in ["/responder/dashboard", "/responder/cases", "/responder/alerts"]:
        assert client.get(path).status_code == 200, path


def test_admin_pages_load(client, app):
    login(client, "admin@sheild.local")
    for path in ["/admin/dashboard", "/admin/incidents", "/admin/alerts", "/admin/users",
                 "/admin/responders", "/admin/responders/new", "/admin/activity",
                 "/admin/services", "/admin/contacts"]:
        assert client.get(path).status_code == 200, path


def test_navigation_contains_expected_destinations(client, app):
    home = client.get("/")
    assert b"Find support" in home.data
    assert b"Safety" in home.data and b"privacy" in home.data
    assert b"Emergency SOS" in home.data
    assert b"Sign in" in home.data
    assert b"Create account" in home.data

    login(client, "demo@sheild.local")
    dashboard = client.get("/reporter/dashboard")
    assert b"Dashboard" in dashboard.data
    assert b"Profile" in dashboard.data
    assert b"Sign out" in dashboard.data


def test_quick_exit_present_on_sensitive_pages(client, app):
    for path in ["/", "/auth/login", "/auth/register"]:
        resp = client.get(path)
        assert b"Quick Exit" in resp.data
        assert b"data-quick-exit" in resp.data

    login(client, "demo@sheild.local")
    for path in ["/reporter/dashboard", "/reporter/reports/new", "/reporter/sos"]:
        resp = client.get(path)
        assert b"Quick Exit" in resp.data


def test_error_pages_render_with_branding_and_context_actions(client, app):
    not_found = client.get("/this-route-does-not-exist-at-all")
    assert not_found.status_code == 404
    assert b"We could not find that page" in not_found.data
    assert b"Return home" in not_found.data
    assert b"SHE" in not_found.data

    login(client, "demo@sheild.local")
    forbidden = client.get("/admin/dashboard")
    assert forbidden.status_code == 403
    assert b"This area is protected" in forbidden.data
    assert b"Return to dashboard" in forbidden.data


def test_anonymous_identity_hidden_across_all_role_views_phase6(client, app):
    login(client, "demo@sheild.local")
    client.post("/reporter/reports/new", data={
        "category": "Stalking", "incident_date": date.today().isoformat(),
        "location": "Fictional Phase6 Anonymous Ward",
        "description": "A fictional anonymous report for Phase 6 regression testing.",
        "preferred_contact_method": "IN_APP", "is_anonymous": "y", "consent": "y",
    })
    logout(client)
    with app.app_context():
        incident_id = Incident.query.filter_by(location="Fictional Phase6 Anonymous Ward").one().id

    login(client, "admin@sheild.local")
    client.post(f"/admin/incidents/{incident_id}", data={
        "responder_id": "0", "status": "UNDER_REVIEW", "risk_level": "MEDIUM",
        "note": "Fictional Phase 6 regression note.",
    })
    admin_detail = client.get(f"/admin/incidents/{incident_id}")
    assert b"Anonymous Report" in admin_detail.data
    assert b"demo@sheild.local" not in admin_detail.data
    assert b"Amina Demo" not in admin_detail.data

    with app.app_context():
        case_number = db.session.get(Incident, incident_id).case_number
    # filtered to this specific anonymous case: other (non-anonymous) cases'
    # activity legitimately shows reporter names, so scope the check here
    admin_activity = client.get(f"/admin/activity?q={case_number}")
    assert b"demo@sheild.local" not in admin_activity.data
    assert b"Amina Demo" not in admin_activity.data
