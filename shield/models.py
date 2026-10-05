from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(180), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(30))
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="REPORTER", index=True)
    is_active_account = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    reported_incidents = db.relationship(
        "Incident", foreign_keys="Incident.reporter_id", back_populates="reporter"
    )
    assigned_incidents = db.relationship(
        "Incident", foreign_keys="Incident.assigned_to_id", back_populates="assigned_to"
    )

    @property
    def is_active(self):
        return self.is_active_account

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Incident(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    case_number = db.Column(db.String(24), unique=True, nullable=False, index=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    category = db.Column(db.String(80), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(180), nullable=False)
    incident_date = db.Column(db.Date, nullable=False)
    safe_contact = db.Column(db.String(120))
    preferred_contact_method = db.Column(db.String(40))
    is_anonymous = db.Column(db.Boolean, default=False, nullable=False)
    immediate_danger = db.Column(db.Boolean, default=False, nullable=False)
    threat_to_life = db.Column(db.Boolean, default=False, nullable=False)
    weapon_involved = db.Column(db.Boolean, default=False, nullable=False)
    medical_attention = db.Column(db.Boolean, default=False, nullable=False)
    dependants_at_risk = db.Column(db.Boolean, default=False, nullable=False)
    risk_level = db.Column(db.String(20), default="MEDIUM", nullable=False, index=True)
    status = db.Column(db.String(30), default="RECEIVED", nullable=False, index=True)
    source = db.Column(db.String(20), default="REPORT", nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    reporter = db.relationship(
        "User", foreign_keys=[reporter_id], back_populates="reported_incidents"
    )
    assigned_to = db.relationship(
        "User", foreign_keys=[assigned_to_id], back_populates="assigned_incidents"
    )
    updates = db.relationship(
        "CaseUpdate", back_populates="incident", cascade="all, delete-orphan",
        order_by="CaseUpdate.created_at.asc()"
    )


class EmergencyAlert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    alert_number = db.Column(db.String(24), unique=True, nullable=False, index=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    incident_id = db.Column(db.Integer, db.ForeignKey("incident.id"), nullable=True)
    location = db.Column(db.String(180), nullable=False)
    safe_contact = db.Column(db.String(120))
    message = db.Column(db.String(500))
    status = db.Column(db.String(20), default="NEW", nullable=False, index=True)
    acknowledged_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    reporter = db.relationship("User", foreign_keys=[reporter_id])
    assigned_to = db.relationship("User", foreign_keys=[assigned_to_id])
    incident = db.relationship("Incident")


class CaseUpdate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    incident_id = db.Column(db.Integer, db.ForeignKey("incident.id"), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    support_service_id = db.Column(db.Integer, db.ForeignKey("support_service.id"), nullable=True)
    status = db.Column(db.String(30), nullable=False)
    note = db.Column(db.Text, nullable=False)
    update_type = db.Column(db.String(30), default="STATUS", nullable=False)
    visibility = db.Column(db.String(20), default="REPORTER_VISIBLE", nullable=False)
    visible_to_reporter = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    incident = db.relationship("Incident", back_populates="updates")
    author = db.relationship("User")
    support_service = db.relationship("SupportService")


class SupportService(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(80), nullable=False)
    description = db.Column(db.Text, nullable=False)
    phone = db.Column(db.String(40))
    email = db.Column(db.String(180))
    website = db.Column(db.String(255))
    hours = db.Column(db.String(120))
    is_active = db.Column(db.Boolean, default=True, nullable=False)


class EmergencyContact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(40), nullable=False)
    description = db.Column(db.String(255))
    is_primary = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)


CASE_STATUSES = [
    "RECEIVED", "UNDER_REVIEW", "RESPONDER_ASSIGNED", "IN_PROGRESS",
    "REFERRED", "RESOLVED", "CLOSED"
]
ALERT_STATUSES = ["NEW", "ACKNOWLEDGED", "RESPONDING", "RESOLVED"]
RISK_LEVELS = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
INCIDENT_CATEGORIES = [
    "Physical Violence", "Sexual Violence", "Domestic Violence",
    "Emotional/Psychological Abuse", "Stalking", "Threat to Life",
    "Forced Marriage", "Economic Abuse", "Online Harassment", "Other"
]
INCIDENT_SOURCES = ["REPORT", "SOS"]
UPDATE_VISIBILITIES = ["INTERNAL", "REPORTER_VISIBLE", "SYSTEM"]
RESPONSE_ACTION_TYPES = [
    "CONTACT_ATTEMPT", "SAFETY_CHECK", "REFERRAL", "MEDICAL_REFERRAL",
    "COUNSELLING_REFERRAL", "LEGAL_REFERRAL", "FOLLOW_UP_SCHEDULED", "OTHER_ACTION",
]
RESPONSE_ACTION_LABELS = {
    "CONTACT_ATTEMPT": "Contact attempt",
    "SAFETY_CHECK": "Safety check",
    "REFERRAL": "Referral",
    "MEDICAL_REFERRAL": "Medical support referral",
    "COUNSELLING_REFERRAL": "Counselling/support referral",
    "LEGAL_REFERRAL": "Legal support referral",
    "FOLLOW_UP_SCHEDULED": "Follow-up scheduled",
    "OTHER_ACTION": "Other",
}
UPDATE_TYPE_LABELS = {
    "NOTE": "Internal note",
    "REPORTER_UPDATE": "Update for reporter",
    "ASSIGNMENT": "Case assigned",
    "ACKNOWLEDGEMENT": "Emergency acknowledged",
    "RESPONSE_STARTED": "Response started",
    "ALERT_RESOLVED": "Emergency alert resolved",
    "ADMIN_ACTION": "Administrator update",
    "ADMIN_ASSIGNMENT": "Assigned by administrator",
    "ADMIN_REASSIGNMENT": "Reassigned by administrator",
    "ADMIN_UNASSIGNMENT": "Unassigned by administrator",
    **RESPONSE_ACTION_LABELS,
}


def describe_update(update):
    """A human-friendly timeline heading for a CaseUpdate, by update_type when meaningful, else by status."""
    return UPDATE_TYPE_LABELS.get(update.update_type, update.status.replace("_", " ").title())


def update_type_label(update_type):
    """A human-friendly label for a raw update_type string, for use outside a CaseUpdate instance (e.g. filter options)."""
    return UPDATE_TYPE_LABELS.get(update_type, update_type.replace("_", " ").title())


def update_author_label(update):
    """Author display name for a CaseUpdate, never revealing a reporter's identity on an anonymous case."""
    incident = update.incident
    if incident and incident.is_anonymous and update.author_id == incident.reporter_id:
        return "Reporter"
    return update.author.full_name if update.author else "System"


def risk_priority_order(column=None):
    """Case expression ranking risk levels by actual severity, not alphabetically."""
    column = column if column is not None else Incident.risk_level
    whens = [(column == level, index) for index, level in enumerate(RISK_LEVELS)]
    return db.case(*whens, else_=-1)
