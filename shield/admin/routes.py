from datetime import date, datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user
from sqlalchemy import func, or_

from ..decorators import roles_required
from ..extensions import db
from ..forms import AssignmentForm, ContactForm, ResponderCreateForm, SupportServiceForm
from ..models import (
    ALERT_STATUSES, CASE_STATUSES, INCIDENT_CATEGORIES, INCIDENT_SOURCES, RISK_LEVELS,
    CaseUpdate, EmergencyAlert, EmergencyContact, Incident, SupportService, User,
)


bp = Blueprint("admin", __name__)

PER_PAGE = 20


def _paginate(query, order_by):
    page = request.args.get("page", 1, type=int)
    return query.order_by(order_by).paginate(page=page, per_page=PER_PAGE, error_out=False)


def _last_n_months(n=6):
    today = date.today()
    year, month = today.year, today.month
    months = []
    for _ in range(n):
        months.append((year, month))
        month -= 1
        if month == 0:
            month, year = 12, year - 1
    return list(reversed(months))


def _reports_over_time(n=6):
    months = _last_n_months(n)
    rows = (
        db.session.query(func.strftime("%Y-%m", Incident.created_at), func.count(Incident.id))
        .group_by(func.strftime("%Y-%m", Incident.created_at))
        .all()
    )
    counts = dict(rows)
    labels, values = [], []
    for year, month in months:
        key = f"{year:04d}-{month:02d}"
        labels.append(date(year, month, 1).strftime("%b %Y"))
        values.append(counts.get(key, 0))
    return labels, values


def _build_chart_data():
    category_counts = dict(db.session.query(Incident.category, func.count(Incident.id)).group_by(Incident.category).all())
    risk_counts = dict(db.session.query(Incident.risk_level, func.count(Incident.id)).group_by(Incident.risk_level).all())
    status_counts = dict(db.session.query(Incident.status, func.count(Incident.id)).group_by(Incident.status).all())
    source_counts = dict(db.session.query(Incident.source, func.count(Incident.id)).group_by(Incident.source).all())
    alert_status_counts = dict(db.session.query(EmergencyAlert.status, func.count(EmergencyAlert.id)).group_by(EmergencyAlert.status).all())
    timeline_labels, timeline_values = _reports_over_time(6)
    return {
        "category": {"labels": list(category_counts.keys()), "values": list(category_counts.values())},
        "risk": {"labels": [r.title() for r in RISK_LEVELS], "values": [risk_counts.get(r, 0) for r in RISK_LEVELS]},
        "status": {"labels": [s.replace("_", " ").title() for s in CASE_STATUSES], "values": [status_counts.get(s, 0) for s in CASE_STATUSES]},
        "timeline": {"labels": timeline_labels, "values": timeline_values},
        "source": {"labels": ["Normal report", "Emergency SOS"], "values": [source_counts.get("REPORT", 0), source_counts.get("SOS", 0)]},
        "alert_status": {"labels": [s.title() for s in ALERT_STATUSES], "values": [alert_status_counts.get(s, 0) for s in ALERT_STATUSES]},
    }


@bp.route("/dashboard")
@roles_required("ADMIN")
def dashboard():
    metrics = {
        "total_reports": Incident.query.count(),
        "active_cases": Incident.query.filter(Incident.status.notin_(["RESOLVED", "CLOSED"])).count(),
        "critical_active": Incident.query.filter_by(risk_level="CRITICAL").filter(Incident.status.notin_(["RESOLVED", "CLOSED"])).count(),
        "new_alerts": EmergencyAlert.query.filter_by(status="NEW").count(),
        "in_progress": Incident.query.filter_by(status="IN_PROGRESS").count(),
        "referred": Incident.query.filter_by(status="REFERRED").count(),
        "resolved": Incident.query.filter_by(status="RESOLVED").count(),
        "reporters": User.query.filter_by(role="REPORTER", is_active_account=True).count(),
        "responders": User.query.filter_by(role="RESPONDER", is_active_account=True).count(),
    }
    recent = Incident.query.order_by(Incident.created_at.desc()).limit(6).all()
    active_alerts = EmergencyAlert.query.filter(EmergencyAlert.status != "RESOLVED").order_by(EmergencyAlert.created_at.desc()).limit(5).all()
    chart_data = _build_chart_data()
    return render_template(
        "admin/dashboard.html", metrics=metrics, recent=recent,
        active_alerts=active_alerts, chart_data=chart_data,
    )


@bp.route("/incidents")
@roles_required("ADMIN")
def incidents():
    search = request.args.get("q", "").strip()
    status = request.args.get("status", "")
    risk = request.args.get("risk", "")
    category = request.args.get("category", "")
    source = request.args.get("source", "")
    assignment = request.args.get("assignment", "")
    responder_id = request.args.get("responder_id", type=int)

    query = Incident.query
    if search:
        query = query.filter(or_(Incident.case_number.ilike(f"%{search}%"), Incident.category.ilike(f"%{search}%")))
    if status in CASE_STATUSES:
        query = query.filter_by(status=status)
    if risk in RISK_LEVELS:
        query = query.filter_by(risk_level=risk)
    if category in INCIDENT_CATEGORIES:
        query = query.filter_by(category=category)
    if source in INCIDENT_SOURCES:
        query = query.filter_by(source=source)
    if assignment == "unassigned":
        query = query.filter(Incident.assigned_to_id.is_(None))
    elif assignment == "assigned":
        query = query.filter(Incident.assigned_to_id.isnot(None))
    if responder_id:
        query = query.filter_by(assigned_to_id=responder_id)

    pager = _paginate(query, Incident.updated_at.desc())
    responders = User.query.filter_by(role="RESPONDER").order_by(User.full_name).all()
    return render_template(
        "admin/incidents.html", pager=pager, incidents=pager.items,
        statuses=CASE_STATUSES, risks=RISK_LEVELS, categories=INCIDENT_CATEGORIES, sources=INCIDENT_SOURCES,
        responders=responders, search=search, selected_status=status, selected_risk=risk,
        selected_category=category, selected_source=source, selected_assignment=assignment,
        selected_responder_id=responder_id,
    )


@bp.route("/incidents/<int:incident_id>", methods=["GET", "POST"])
@roles_required("ADMIN")
def incident_detail(incident_id):
    incident = db.get_or_404(Incident, incident_id)
    form = AssignmentForm(status=incident.status, risk_level=incident.risk_level)
    responders = User.query.filter_by(role="RESPONDER", is_active_account=True).order_by(User.full_name).all()
    form.responder_id.choices = [(0, "Unassigned")] + [(u.id, u.full_name) for u in responders]
    if request.method == "GET":
        form.responder_id.data = incident.assigned_to_id or 0
    if form.validate_on_submit():
        previous_assigned_id = incident.assigned_to_id
        new_assigned_id = form.responder_id.data or None

        incident.assigned_to_id = new_assigned_id
        incident.status = form.status.data
        incident.risk_level = form.risk_level.data

        note = form.note.data.strip()
        update_type = "ADMIN_ACTION"
        if new_assigned_id != previous_assigned_id:
            if previous_assigned_id is None:
                prefix = "Case assigned to responder by administrator."
                update_type = "ADMIN_ASSIGNMENT"
            elif new_assigned_id is None:
                prefix = "Case unassigned by administrator."
                update_type = "ADMIN_UNASSIGNMENT"
            else:
                prefix = "Case reassigned by administrator."
                update_type = "ADMIN_REASSIGNMENT"
            note = f"{prefix} {note}" if note else prefix
            flash(prefix, "success")
        else:
            flash("Case status and risk updated.", "success")

        db.session.add(CaseUpdate(
            incident=incident, author_id=current_user.id, status=incident.status,
            note=note, update_type=update_type, visibility="REPORTER_VISIBLE", visible_to_reporter=True,
        ))
        db.session.commit()
        return redirect(url_for("admin.incident_detail", incident_id=incident.id))
    linked_alert = EmergencyAlert.query.filter_by(incident_id=incident.id).first()
    return render_template(
        "admin/incident_detail.html", incident=incident, form=form,
        responders=responders, linked_alert=linked_alert,
    )


@bp.route("/alerts")
@roles_required("ADMIN")
def alerts():
    status = request.args.get("status", "")
    responder_id = request.args.get("responder_id", type=int)
    date_filter = request.args.get("date", "")
    search = request.args.get("q", "").strip()

    query = EmergencyAlert.query.outerjoin(Incident, EmergencyAlert.incident_id == Incident.id)
    if status in ALERT_STATUSES:
        query = query.filter(EmergencyAlert.status == status)
    if responder_id:
        query = query.filter(EmergencyAlert.assigned_to_id == responder_id)
    if date_filter:
        try:
            day = datetime.strptime(date_filter, "%Y-%m-%d").date()
            query = query.filter(func.date(EmergencyAlert.created_at) == day.isoformat())
        except ValueError:
            pass
    if search:
        query = query.filter(or_(
            EmergencyAlert.alert_number.ilike(f"%{search}%"),
            Incident.case_number.ilike(f"%{search}%"),
        ))
    items = query.order_by(EmergencyAlert.status, EmergencyAlert.created_at.desc()).all()
    responders = User.query.filter_by(role="RESPONDER").order_by(User.full_name).all()
    return render_template(
        "admin/alerts.html", alerts=items, statuses=ALERT_STATUSES, responders=responders,
        selected_status=status, selected_responder_id=responder_id, selected_date=date_filter, search=search,
    )


@bp.route("/users")
@roles_required("ADMIN")
def users():
    role = request.args.get("role", "")
    active = request.args.get("active", "")
    search = request.args.get("q", "").strip()
    query = User.query
    if role:
        query = query.filter_by(role=role)
    if active == "active":
        query = query.filter_by(is_active_account=True)
    elif active == "inactive":
        query = query.filter_by(is_active_account=False)
    if search:
        query = query.filter(or_(User.full_name.ilike(f"%{search}%"), User.email.ilike(f"%{search}%")))

    pager = _paginate(query, User.created_at.desc())
    user_list = pager.items
    user_ids = [u.id for u in user_list]
    report_counts = {}
    assigned_counts = {}
    if user_ids:
        report_counts = dict(
            db.session.query(Incident.reporter_id, func.count(Incident.id))
            .filter(Incident.reporter_id.in_(user_ids))
            .group_by(Incident.reporter_id).all()
        )
        assigned_counts = dict(
            db.session.query(Incident.assigned_to_id, func.count(Incident.id))
            .filter(Incident.assigned_to_id.in_(user_ids))
            .group_by(Incident.assigned_to_id).all()
        )
    return render_template(
        "admin/users.html", pager=pager, users=user_list, selected_role=role,
        selected_active=active, search=search, report_counts=report_counts, assigned_counts=assigned_counts,
    )


@bp.route("/responders")
@roles_required("ADMIN")
def responders():
    search = request.args.get("q", "").strip()
    active = request.args.get("active", "")
    query = User.query.filter_by(role="RESPONDER")
    if active == "active":
        query = query.filter_by(is_active_account=True)
    elif active == "inactive":
        query = query.filter_by(is_active_account=False)
    if search:
        query = query.filter(or_(User.full_name.ilike(f"%{search}%"), User.email.ilike(f"%{search}%")))
    responder_list = query.order_by(User.full_name).all()

    workload = {}
    for responder in responder_list:
        assigned = Incident.query.filter_by(assigned_to_id=responder.id)
        workload[responder.id] = {
            "total": assigned.count(),
            "active": assigned.filter(Incident.status.notin_(["RESOLVED", "CLOSED"])).count(),
            "critical": assigned.filter_by(risk_level="CRITICAL").filter(Incident.status.notin_(["RESOLVED", "CLOSED"])).count(),
            "resolved": assigned.filter_by(status="RESOLVED").count(),
        }
    return render_template(
        "admin/responders.html", responders=responder_list, workload=workload,
        search=search, selected_active=active,
    )


@bp.route("/responders/new", methods=["GET", "POST"])
@roles_required("ADMIN")
def new_responder():
    form = ResponderCreateForm()
    if form.validate_on_submit():
        responder = User(
            full_name=form.full_name.data.strip(),
            email=form.email.data.strip().lower(),
            phone=form.phone.data.strip() if form.phone.data else None,
            role="RESPONDER",
        )
        responder.set_password(form.password.data)
        db.session.add(responder)
        db.session.commit()
        flash("Responder account created. Share the temporary password through a safe channel.", "success")
        return redirect(url_for("admin.responders"))
    return render_template("admin/new_responder.html", form=form)


@bp.post("/users/<int:user_id>/toggle")
@roles_required("ADMIN")
def toggle_user(user_id):
    user = db.get_or_404(User, user_id)
    if user.id == current_user.id:
        flash("You cannot deactivate your own account.", "error")
    else:
        user.is_active_account = not user.is_active_account
        db.session.commit()
        flash("Account status updated.", "success")
    return redirect(request.referrer or url_for("admin.users"))


@bp.route("/activity")
@roles_required("ADMIN")
def activity():
    case_search = request.args.get("q", "").strip()
    update_type = request.args.get("update_type", "")
    visibility = request.args.get("visibility", "")
    date_filter = request.args.get("date", "")

    query = CaseUpdate.query.join(Incident)
    if case_search:
        query = query.filter(Incident.case_number.ilike(f"%{case_search}%"))
    if update_type:
        query = query.filter(CaseUpdate.update_type == update_type)
    if visibility:
        query = query.filter(CaseUpdate.visibility == visibility)
    if date_filter:
        try:
            day = datetime.strptime(date_filter, "%Y-%m-%d").date()
            query = query.filter(func.date(CaseUpdate.created_at) == day.isoformat())
        except ValueError:
            pass

    pager = _paginate(query, CaseUpdate.created_at.desc())
    update_types = [row[0] for row in db.session.query(CaseUpdate.update_type).distinct().order_by(CaseUpdate.update_type).all()]
    return render_template(
        "admin/activity.html", pager=pager, updates=pager.items, update_types=update_types,
        visibilities=["INTERNAL", "REPORTER_VISIBLE", "SYSTEM"], case_search=case_search,
        selected_update_type=update_type, selected_visibility=visibility, selected_date=date_filter,
    )


@bp.route("/services", methods=["GET", "POST"])
@roles_required("ADMIN")
def services():
    form = SupportServiceForm()
    if form.validate_on_submit():
        service = SupportService()
        form.populate_obj(service)
        db.session.add(service)
        db.session.commit()
        flash("Support service added.", "success")
        return redirect(url_for("admin.services"))
    return render_template("admin/services.html", form=form, services=SupportService.query.order_by(SupportService.name).all())


@bp.route("/services/<int:service_id>/edit", methods=["GET", "POST"])
@roles_required("ADMIN")
def edit_service(service_id):
    service = db.get_or_404(SupportService, service_id)
    form = SupportServiceForm(obj=service)
    if form.validate_on_submit():
        form.populate_obj(service)
        db.session.commit()
        flash("Support service updated.", "success")
        return redirect(url_for("admin.services"))
    return render_template("admin/edit_service.html", form=form, service=service)


@bp.post("/services/<int:service_id>/toggle")
@roles_required("ADMIN")
def toggle_service(service_id):
    service = db.get_or_404(SupportService, service_id)
    service.is_active = not service.is_active
    db.session.commit()
    flash("Service visibility updated.", "success")
    return redirect(url_for("admin.services"))


@bp.route("/contacts", methods=["GET", "POST"])
@roles_required("ADMIN")
def contacts():
    form = ContactForm()
    if form.validate_on_submit():
        if form.is_primary.data:
            EmergencyContact.query.update({EmergencyContact.is_primary: False})
        contact = EmergencyContact()
        form.populate_obj(contact)
        db.session.add(contact)
        db.session.commit()
        flash("Emergency contact added.", "success")
        return redirect(url_for("admin.contacts"))
    return render_template("admin/contacts.html", form=form, contacts=EmergencyContact.query.order_by(EmergencyContact.is_primary.desc(), EmergencyContact.name).all())


@bp.route("/contacts/<int:contact_id>/edit", methods=["GET", "POST"])
@roles_required("ADMIN")
def edit_contact(contact_id):
    contact = db.get_or_404(EmergencyContact, contact_id)
    form = ContactForm(obj=contact)
    if form.validate_on_submit():
        if form.is_primary.data:
            EmergencyContact.query.filter(EmergencyContact.id != contact.id).update(
                {EmergencyContact.is_primary: False}
            )
        form.populate_obj(contact)
        db.session.commit()
        flash("Emergency contact updated.", "success")
        return redirect(url_for("admin.contacts"))
    return render_template("admin/edit_contact.html", form=form, contact=contact)


@bp.post("/contacts/<int:contact_id>/toggle")
@roles_required("ADMIN")
def toggle_contact(contact_id):
    contact = db.get_or_404(EmergencyContact, contact_id)
    contact.is_active = not contact.is_active
    db.session.commit()
    flash("Contact visibility updated.", "success")
    return redirect(url_for("admin.contacts"))
