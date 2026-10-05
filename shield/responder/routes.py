from datetime import datetime

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user
from sqlalchemy import or_

from ..decorators import roles_required
from ..extensions import db
from ..forms import (
    CaseActionForm, InternalNoteForm, ReferralForm, ReporterUpdateForm, ResponseActionForm,
)
from ..models import (
    ALERT_STATUSES, CASE_STATUSES, INCIDENT_CATEGORIES, INCIDENT_SOURCES,
    RESPONSE_ACTION_LABELS, RISK_LEVELS, CaseUpdate, EmergencyAlert, Incident,
    SupportService, risk_priority_order, utcnow,
)
from ..services.case_transitions import allowed_next_statuses, is_transition_allowed
from ..services.risk_assessment import assess_incident_risk


bp = Blueprint("responder", __name__)

# Distinct WTForms prefixes keep field/csrf ids unique when several forms
# (status update, note, reporter update, response action, referral) share
# field names like "note" on the same case-detail page.
NOTE_FORM_PREFIX = "note"
UPDATE_FORM_PREFIX = "update"
ACTION_FORM_PREFIX = "action"
REFERRAL_FORM_PREFIX = "referral"


def _build_referral_form():
    form = ReferralForm(prefix=REFERRAL_FORM_PREFIX)
    form.support_service_id.choices = [
        (service.id, service.name)
        for service in SupportService.query.filter_by(is_active=True).order_by(SupportService.name).all()
    ]
    return form


def _case_detail_context(incident, form):
    return {
        "incident": incident,
        "form": form,
        "note_form": InternalNoteForm(prefix=NOTE_FORM_PREFIX),
        "reporter_update_form": ReporterUpdateForm(prefix=UPDATE_FORM_PREFIX),
        "action_form": ResponseActionForm(prefix=ACTION_FORM_PREFIX),
        "referral_form": _build_referral_form(),
        "action_labels": RESPONSE_ACTION_LABELS,
        "assessment": assess_incident_risk(incident),
        "allowed_statuses": allowed_next_statuses(incident.status),
    }


@bp.route("/dashboard")
@roles_required("RESPONDER")
def dashboard():
    my_cases = Incident.query.filter_by(assigned_to_id=current_user.id)
    metrics = {
        "new_alerts": EmergencyAlert.query.filter_by(status="NEW").count(),
        "critical_active": Incident.query.filter_by(risk_level="CRITICAL")
            .filter(Incident.status.notin_(["RESOLVED", "CLOSED"])).count(),
        "my_assigned": my_cases.filter(Incident.status.notin_(["RESOLVED", "CLOSED"])).count(),
        "in_progress": my_cases.filter_by(status="IN_PROGRESS").count(),
        "referred": my_cases.filter_by(status="REFERRED").count(),
        "resolved": my_cases.filter_by(status="RESOLVED").count(),
    }

    emergency_queue = (
        EmergencyAlert.query.outerjoin(Incident, EmergencyAlert.incident_id == Incident.id)
        .filter(EmergencyAlert.status != "RESOLVED")
        .order_by(risk_priority_order(Incident.risk_level).desc(), EmergencyAlert.created_at.asc())
        .limit(8).all()
    )
    assigned = (
        my_cases.filter(Incident.status.notin_(["RESOLVED", "CLOSED"]))
        .order_by(risk_priority_order().desc(), Incident.updated_at.desc())
        .limit(8).all()
    )
    unassigned = (
        Incident.query.filter_by(assigned_to_id=None)
        .filter(Incident.status.notin_(["RESOLVED", "CLOSED"]))
        .order_by(risk_priority_order().desc(), Incident.created_at.asc())
        .limit(8).all()
    )
    recent_activity = (
        CaseUpdate.query.join(Incident)
        .filter(or_(Incident.assigned_to_id == current_user.id, Incident.assigned_to_id.is_(None)))
        .order_by(CaseUpdate.created_at.desc())
        .limit(8).all()
    )
    return render_template(
        "responder/dashboard.html", metrics=metrics, emergency_queue=emergency_queue,
        assigned=assigned, unassigned=unassigned, recent_activity=recent_activity,
    )


@bp.route("/cases")
@roles_required("RESPONDER")
def cases():
    status = request.args.get("status", "")
    risk = request.args.get("risk", "")
    category = request.args.get("category", "")
    source = request.args.get("source", "")
    assignment = request.args.get("assignment", "")
    search = request.args.get("q", "").strip()

    query = Incident.query.filter(or_(Incident.assigned_to_id == current_user.id, Incident.assigned_to_id.is_(None)))
    if assignment == "mine":
        query = query.filter(Incident.assigned_to_id == current_user.id)
    elif assignment == "unassigned":
        query = query.filter(Incident.assigned_to_id.is_(None))
    if status in CASE_STATUSES:
        query = query.filter_by(status=status)
    if risk in RISK_LEVELS:
        query = query.filter_by(risk_level=risk)
    if category in INCIDENT_CATEGORIES:
        query = query.filter_by(category=category)
    if source in INCIDENT_SOURCES:
        query = query.filter_by(source=source)
    if search:
        query = query.filter(Incident.case_number.ilike(f"%{search}%"))
    incidents = query.order_by(risk_priority_order().desc(), Incident.updated_at.desc()).all()
    return render_template(
        "responder/cases.html", incidents=incidents,
        statuses=CASE_STATUSES, risks=RISK_LEVELS, categories=INCIDENT_CATEGORIES, sources=INCIDENT_SOURCES,
        selected_status=status, selected_risk=risk, selected_category=category,
        selected_source=source, selected_assignment=assignment, search=search,
    )


@bp.post("/cases/<int:incident_id>/claim")
@roles_required("RESPONDER")
def claim_case(incident_id):
    incident = db.get_or_404(Incident, incident_id)
    if incident.assigned_to_id and incident.assigned_to_id != current_user.id:
        flash("This case was already claimed by another responder.", "error")
        return redirect(url_for("responder.cases"))
    if not incident.assigned_to_id:
        incident.assigned_to_id = current_user.id
        if incident.status in ("RECEIVED", "UNDER_REVIEW"):
            incident.status = "RESPONDER_ASSIGNED"
        db.session.add(CaseUpdate(
            incident=incident, author_id=current_user.id, status=incident.status,
            note="Case assigned to responder.", update_type="ASSIGNMENT",
            visibility="SYSTEM", visible_to_reporter=True,
        ))
        db.session.commit()
        flash("Case assigned to you.", "success")
    return redirect(url_for("responder.case_detail", incident_id=incident.id))


@bp.route("/cases/<int:incident_id>", methods=["GET", "POST"])
@roles_required("RESPONDER")
def case_detail(incident_id):
    incident = db.get_or_404(Incident, incident_id)
    if incident.assigned_to_id not in (None, current_user.id):
        abort(403)
    current_status = incident.status
    form = CaseActionForm(status=incident.status, risk_level=incident.risk_level)
    form.status.choices = [(v, v.replace("_", " ").title()) for v in allowed_next_statuses(current_status)]
    if form.validate_on_submit():
        if not is_transition_allowed(current_status, form.status.data):
            flash(
                f"Cannot move a case directly from {incident.status.replace('_', ' ').title()} "
                f"to {form.status.data.replace('_', ' ').title()}.", "error",
            )
        else:
            if incident.assigned_to_id is None:
                incident.assigned_to_id = current_user.id
            incident.status = form.status.data
            incident.risk_level = form.risk_level.data
            db.session.add(CaseUpdate(
                incident=incident, author_id=current_user.id, status=form.status.data,
                note=form.note.data.strip(), update_type="RESPONSE_ACTION",
                visibility="REPORTER_VISIBLE" if form.visible_to_reporter.data else "INTERNAL",
                visible_to_reporter=form.visible_to_reporter.data,
            ))
            db.session.commit()
            flash("Case update recorded.", "success")
            return redirect(url_for("responder.case_detail", incident_id=incident.id))
    return render_template("responder/case_detail.html", **_case_detail_context(incident, form))


@bp.post("/cases/<int:incident_id>/notes")
@roles_required("RESPONDER")
def add_internal_note(incident_id):
    incident = db.get_or_404(Incident, incident_id)
    if incident.assigned_to_id not in (None, current_user.id):
        abort(403)
    form = InternalNoteForm(prefix=NOTE_FORM_PREFIX)
    if form.validate_on_submit():
        db.session.add(CaseUpdate(
            incident=incident, author_id=current_user.id, status=incident.status,
            note=form.note.data.strip(), update_type="NOTE",
            visibility="INTERNAL", visible_to_reporter=False,
        ))
        db.session.commit()
        flash("Internal note added.", "success")
    else:
        flash("Could not add the internal note. Please enter note text.", "error")
    return redirect(url_for("responder.case_detail", incident_id=incident.id))


@bp.post("/cases/<int:incident_id>/reporter-updates")
@roles_required("RESPONDER")
def add_reporter_update(incident_id):
    incident = db.get_or_404(Incident, incident_id)
    if incident.assigned_to_id not in (None, current_user.id):
        abort(403)
    form = ReporterUpdateForm(prefix=UPDATE_FORM_PREFIX)
    if form.validate_on_submit():
        db.session.add(CaseUpdate(
            incident=incident, author_id=current_user.id, status=incident.status,
            note=form.note.data.strip(), update_type="REPORTER_UPDATE",
            visibility="REPORTER_VISIBLE", visible_to_reporter=True,
        ))
        db.session.commit()
        flash("Update sent to the reporter's case timeline.", "success")
    else:
        flash("Could not add the update. Please enter the update text.", "error")
    return redirect(url_for("responder.case_detail", incident_id=incident.id))


@bp.post("/cases/<int:incident_id>/actions")
@roles_required("RESPONDER")
def add_response_action(incident_id):
    incident = db.get_or_404(Incident, incident_id)
    if incident.assigned_to_id not in (None, current_user.id):
        abort(403)
    form = ResponseActionForm(prefix=ACTION_FORM_PREFIX)
    if form.validate_on_submit():
        label = RESPONSE_ACTION_LABELS[form.action_type.data]
        note_text = f"{label} recorded." if not form.note.data else f"{label}: {form.note.data.strip()}"
        db.session.add(CaseUpdate(
            incident=incident, author_id=current_user.id, status=incident.status,
            note=note_text, update_type=form.action_type.data,
            visibility="INTERNAL", visible_to_reporter=False,
        ))
        db.session.commit()
        flash("Response action recorded.", "success")
    else:
        flash("Could not record the response action.", "error")
    return redirect(url_for("responder.case_detail", incident_id=incident.id))


@bp.post("/cases/<int:incident_id>/referral")
@roles_required("RESPONDER")
def add_referral(incident_id):
    incident = db.get_or_404(Incident, incident_id)
    if incident.assigned_to_id not in (None, current_user.id):
        abort(403)
    form = _build_referral_form()
    if form.validate_on_submit():
        service = db.get_or_404(SupportService, form.support_service_id.data)
        note_text = f"Referral recorded in the prototype: {service.name}."
        if form.note.data:
            note_text += f" {form.note.data.strip()}"
        if form.mark_referred.data and is_transition_allowed(incident.status, "REFERRED"):
            incident.status = "REFERRED"
        db.session.add(CaseUpdate(
            incident=incident, author_id=current_user.id, status=incident.status,
            note=note_text, update_type="REFERRAL", support_service_id=service.id,
            visibility="INTERNAL", visible_to_reporter=False,
        ))
        db.session.commit()
        flash("Referral recorded.", "success")
    else:
        flash("Could not record the referral. Please choose a support service.", "error")
    return redirect(url_for("responder.case_detail", incident_id=incident.id))


@bp.route("/alerts")
@roles_required("RESPONDER")
def alerts():
    status = request.args.get("status", "")
    assignment = request.args.get("assignment", "")
    date_filter = request.args.get("date", "")
    search = request.args.get("q", "").strip()

    query = EmergencyAlert.query.outerjoin(Incident, EmergencyAlert.incident_id == Incident.id)
    if status in ALERT_STATUSES:
        query = query.filter(EmergencyAlert.status == status)
    if assignment == "mine":
        query = query.filter(EmergencyAlert.assigned_to_id == current_user.id)
    elif assignment == "unassigned":
        query = query.filter(EmergencyAlert.assigned_to_id.is_(None))
    if date_filter:
        try:
            day = datetime.strptime(date_filter, "%Y-%m-%d").date()
            query = query.filter(db.func.date(EmergencyAlert.created_at) == day.isoformat())
        except ValueError:
            pass
    if search:
        query = query.filter(or_(
            EmergencyAlert.alert_number.ilike(f"%{search}%"),
            Incident.case_number.ilike(f"%{search}%"),
        ))
    items = query.order_by(EmergencyAlert.status, EmergencyAlert.created_at.asc()).all()
    return render_template(
        "responder/alerts.html", alerts=items, statuses=ALERT_STATUSES,
        selected_status=status, selected_assignment=assignment, selected_date=date_filter, search=search,
    )


@bp.route("/alerts/<int:alert_id>")
@roles_required("RESPONDER")
def alert_detail(alert_id):
    alert = db.get_or_404(EmergencyAlert, alert_id)
    return render_template("responder/alert_detail.html", alert=alert)


def _alert_guard(alert):
    if alert.assigned_to_id and alert.assigned_to_id != current_user.id:
        flash("This emergency alert is already being handled by another responder.", "error")
        return False
    return True


@bp.post("/alerts/<int:alert_id>/acknowledge")
@roles_required("RESPONDER")
def acknowledge_alert(alert_id):
    alert = db.get_or_404(EmergencyAlert, alert_id)
    if not _alert_guard(alert):
        return redirect(url_for("responder.alerts"))
    if alert.status == "NEW":
        alert.status = "ACKNOWLEDGED"
        alert.acknowledged_at = utcnow()
    if not alert.assigned_to_id:
        alert.assigned_to_id = current_user.id
    incident = alert.incident
    if incident:
        if incident.assigned_to_id is None:
            incident.assigned_to_id = current_user.id
        if incident.status in ("RECEIVED", "UNDER_REVIEW"):
            incident.status = "RESPONDER_ASSIGNED"
        db.session.add(CaseUpdate(
            incident=incident, author_id=current_user.id, status=incident.status,
            note="Emergency alert acknowledged by responder.", update_type="ACKNOWLEDGEMENT",
            visibility="SYSTEM", visible_to_reporter=True,
        ))
    db.session.commit()
    flash("Emergency alert acknowledged.", "success")
    return redirect(url_for("responder.alert_detail", alert_id=alert.id))


@bp.post("/alerts/<int:alert_id>/start-response")
@roles_required("RESPONDER")
def start_response(alert_id):
    alert = db.get_or_404(EmergencyAlert, alert_id)
    if not _alert_guard(alert):
        return redirect(url_for("responder.alerts"))
    if not alert.assigned_to_id:
        alert.assigned_to_id = current_user.id
    alert.status = "RESPONDING"
    incident = alert.incident
    if incident:
        if incident.assigned_to_id is None:
            incident.assigned_to_id = current_user.id
        if is_transition_allowed(incident.status, "IN_PROGRESS"):
            incident.status = "IN_PROGRESS"
        db.session.add(CaseUpdate(
            incident=incident, author_id=current_user.id, status=incident.status,
            note="A responder has started responding to this emergency.", update_type="RESPONSE_STARTED",
            visibility="REPORTER_VISIBLE", visible_to_reporter=True,
        ))
    db.session.commit()
    flash("Response started.", "success")
    return redirect(url_for("responder.alert_detail", alert_id=alert.id))


@bp.post("/alerts/<int:alert_id>/resolve")
@roles_required("RESPONDER")
def resolve_alert(alert_id):
    alert = db.get_or_404(EmergencyAlert, alert_id)
    if not _alert_guard(alert):
        return redirect(url_for("responder.alerts"))
    alert.status = "RESOLVED"
    incident = alert.incident
    if incident:
        db.session.add(CaseUpdate(
            incident=incident, author_id=current_user.id, status=incident.status,
            note="Emergency alert resolved. This does not automatically close the case.",
            update_type="ALERT_RESOLVED", visibility="REPORTER_VISIBLE", visible_to_reporter=True,
        ))
    db.session.commit()
    flash("Emergency alert marked resolved. The case itself is unchanged unless you update its status separately.", "success")
    return redirect(url_for("responder.alert_detail", alert_id=alert.id))
