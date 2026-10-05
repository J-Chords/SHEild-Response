from sqlalchemy import inspect, text

from .extensions import db


INCIDENT_COLUMNS = {
    "preferred_contact_method": "VARCHAR(40)",
    "threat_to_life": "BOOLEAN NOT NULL DEFAULT 0",
    "weapon_involved": "BOOLEAN NOT NULL DEFAULT 0",
    "medical_attention": "BOOLEAN NOT NULL DEFAULT 0",
    "dependants_at_risk": "BOOLEAN NOT NULL DEFAULT 0",
    "source": "VARCHAR(20) NOT NULL DEFAULT 'REPORT'",
}

EMERGENCY_ALERT_COLUMNS = {
    "incident_id": "INTEGER REFERENCES incident (id)",
    "acknowledged_at": "DATETIME",
}

CASE_UPDATE_COLUMNS = {
    "visibility": "VARCHAR(20) NOT NULL DEFAULT 'REPORTER_VISIBLE'",
    "support_service_id": "INTEGER REFERENCES support_service (id)",
}


def _add_missing_columns(inspector, table, columns):
    if table not in inspector.get_table_names():
        return set()
    existing = {column["name"] for column in inspector.get_columns(table)}
    added = set()
    for name, definition in columns.items():
        if name not in existing:
            db.session.execute(text(f'ALTER TABLE {table} ADD COLUMN "{name}" {definition}'))
            added.add(name)
    return added


def ensure_schema():
    """Apply small, repeat-safe SQLite additions while the prototype has no migration tool."""
    if db.engine.dialect.name != "sqlite":
        return
    inspector = inspect(db.engine)
    _add_missing_columns(inspector, "incident", INCIDENT_COLUMNS)
    _add_missing_columns(inspector, "emergency_alert", EMERGENCY_ALERT_COLUMNS)
    case_update_added = _add_missing_columns(inspector, "case_update", CASE_UPDATE_COLUMNS)
    if "visibility" in case_update_added:
        db.session.execute(text(
            "UPDATE case_update SET visibility = CASE WHEN visible_to_reporter = 1 "
            "THEN 'REPORTER_VISIBLE' ELSE 'INTERNAL' END"
        ))
    db.session.commit()
