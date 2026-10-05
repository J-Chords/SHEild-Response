from datetime import datetime

from .extensions import db
from .models import EmergencyAlert, Incident


def next_case_number():
    year = datetime.now().year
    prefix = f"SHR-{year}-"
    latest = (
        Incident.query.filter(Incident.case_number.like(f"{prefix}%"))
        .order_by(Incident.case_number.desc())
        .first()
    )
    sequence = int(latest.case_number.rsplit("-", 1)[-1]) + 1 if latest else 1
    return f"{prefix}{sequence:04d}"


def next_alert_number():
    year = datetime.now().year
    prefix = f"SOS-{year}-"
    latest = (
        EmergencyAlert.query.filter(EmergencyAlert.alert_number.like(f"{prefix}%"))
        .order_by(EmergencyAlert.alert_number.desc())
        .first()
    )
    sequence = int(latest.alert_number.rsplit("-", 1)[-1]) + 1 if latest else 1
    return f"{prefix}{sequence:04d}"
