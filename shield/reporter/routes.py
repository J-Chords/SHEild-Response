from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user

from ..decorators import roles_required
from ..extensions import db
from ..forms import EmergencyAlertForm, IncidentForm
from ..models import (
    CASE_STATUSES, INCIDENT_CATEGORIES, RISK_LEVELS, CaseUpdate, EmergencyAlert,
    Incident, SupportService, utcnow,
)
from ..services.risk_assessment import assess_incident_risk
from ..utils import next_alert_number, next_case_number


bp = Blueprint("reporter", __name__)


@bp.route("/dashboard")
@roles_required("REPORTER")
def dashboard():
    incidents = Incident.query.filter_by(reporter_id=current_user.id).order_by(Incident.created_at.desc()).all()
    alerts = EmergencyAlert.query.filter_by(reporter_id=current_user.id).order_by(EmergencyAlert.created_at.desc()).limit(3).all()
    latest_updates = (
        CaseUpdate.query.join(Incident)
        .filter(Incident.reporter_id == current_user.id, CaseUpdate.visible_to_reporter.is_(True))
        .order_by(CaseUpdate.created_at.desc()).limit(5).all()
    )
    metrics = {
        "total": len(incidents),
        "active": sum(item.status not in ("RESOLVED", "CLOSED") for item in incidents),
        "resolved": sum(item.status in ("RESOLVED", "CLOSED") for item in incidents),
    }
    services = SupportService.query.filter_by(is_active=True).order_by(SupportService.name).limit(3).all()
    return render_template(
        "reporter/dashboard_phase2.html", incidents=incidents, alerts=alerts,
        latest_updates=latest_updates, metrics=metrics, services=services,
    )


@bp.route("/reports")
@roles_required("REPORTER")
def reports():
    selected_status = request.args.get("status", "")
    selected_risk = request.args.get("risk", "")
    selected_category = request.args.get("category", "")
    query = Incident.query.filter_by(reporter_id=current_user.id)
    if selected_status in CASE_STATUSES:
        query = query.filter_by(status=selected_status)
    if selected_risk in RISK_LEVELS:
        query = query.filter_by(risk_level=selected_risk)
    if selected_category in INCIDENT_CATEGORIES:
        query = query.filter_by(category=selected_category)
    incidents = query.order_by(Incident.created_at.desc()).all()
    return render_template(
        "reporter/reports_phase2.html", incidents=incidents,
        statuses=CASE_STATUSES, risks=RISK_LEVELS, categories=INCIDENT_CATEGORIES,
        selected_status=selected_status, selected_risk=selected_risk,
        selected_category=selected_category,
    )


@bp.route("/reports/new", methods=["GET", "POST"])
@roles_required("REPORTER")
def new_report():
    form = IncidentForm()
    if form.validate_on_submit():
        assessment = assess_incident_risk({
            "immediate_danger": form.immediate_danger.data,
            "threat_to_life": form.threat_to_life.data,
            "weapon_involved": form.weapon_involved.data,
            "medical_attention": form.medical_attention.data,
            "dependants_at_risk": form.dependants_at_risk.data,
        })
        incident = Incident(
            case_number=next_case_number(), reporter_id=current_user.id,
            category=form.category.data, incident_date=form.incident_date.data,
            location=form.location.data.strip(), description=form.description.data.strip(),
            safe_contact=form.safe_contact.data.strip() if form.safe_contact.data else None,
            preferred_contact_method=form.preferred_contact_method.data,
            immediate_danger=form.immediate_danger.data, is_anonymous=form.is_anonymous.data,
            threat_to_life=form.threat_to_life.data,
            weapon_involved=form.weapon_involved.data,
            medical_attention=form.medical_attention.data,
            dependants_at_risk=form.dependants_at_risk.data,
            risk_level=assessment.level, status="RECEIVED",
        )
        db.session.add(incident)
        db.session.flush()
        db.session.add(CaseUpdate(
            incident=incident, author_id=current_user.id, status="RECEIVED",
            note="Report received securely. A trained reviewer should assess the information next.",
        ))
        db.session.commit()
        flash(f"Report submitted. Keep your reference number: {incident.case_number}", "success")
        return redirect(url_for("reporter.report_confirmation", incident_id=incident.id))
    return render_template("reporter/new_report_phase2.html", form=form)


@bp.route("/reports/<int:incident_id>/confirmation")
@roles_required("REPORTER")
def report_confirmation(incident_id):
    incident = db.get_or_404(Incident, incident_id)
    if incident.reporter_id != current_user.id:
        abort(403)
    assessment = assess_incident_risk(incident)
    return render_template(
        "reporter/report_confirmation.html", incident=incident, assessment=assessment
    )


@bp.route("/reports/<int:incident_id>")
@roles_required("REPORTER")
def report_detail(incident_id):
    incident = db.get_or_404(Incident, incident_id)
    if incident.reporter_id != current_user.id:
        abort(403)
    updates = [update for update in incident.updates if update.visible_to_reporter]
    assessment = assess_incident_risk(incident)
    return render_template(
        "reporter/report_detail_phase2.html", incident=incident, updates=updates,
        assessment=assessment,
    )


@bp.route("/sos", methods=["GET", "POST"])
@roles_required("REPORTER")
def sos():
    form = EmergencyAlertForm()
    if form.validate_on_submit():
        location = form.location.data.strip()
        description = form.description.data.strip()

        incident = Incident(
            case_number=next_case_number(), reporter_id=current_user.id,
            category=form.category.data, description=description,
            location=location, incident_date=utcnow().date(),
            preferred_contact_method="IN_APP",
            is_anonymous=form.is_anonymous.data,
            immediate_danger=form.immediate_danger.data,
            risk_level="CRITICAL", status="RECEIVED", source="SOS",
        )
        db.session.add(incident)
        db.session.flush()

        alert = EmergencyAlert(
            alert_number=next_alert_number(), reporter_id=current_user.id,
            incident_id=incident.id, location=location, message=description,
        )
        db.session.add(alert)

        db.session.add(CaseUpdate(
            incident=incident, author_id=current_user.id, status="RECEIVED",
            note="Emergency SOS submitted. This created a critical-priority case for immediate responder review.",
            update_type="SOS", visible_to_reporter=True,
        ))
        db.session.commit()
        flash(f"Emergency request recorded as {incident.case_number}. This did not contact emergency services.", "warning")
        return redirect(url_for("reporter.sos_confirmation", alert_id=alert.id))
    return render_template("reporter/sos.html", form=form)


@bp.route("/sos/<int:alert_id>/confirmation")
@roles_required("REPORTER")
def sos_confirmation(alert_id):
    alert = db.get_or_404(EmergencyAlert, alert_id)
    if alert.reporter_id != current_user.id:
        abort(403)
    return render_template("reporter/sos_confirmation.html", alert=alert, incident=alert.incident)
