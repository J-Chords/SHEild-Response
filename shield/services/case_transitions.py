ALLOWED_TRANSITIONS = {
    "RECEIVED": {"UNDER_REVIEW", "RESPONDER_ASSIGNED"},
    "UNDER_REVIEW": {"RESPONDER_ASSIGNED", "IN_PROGRESS"},
    "RESPONDER_ASSIGNED": {"IN_PROGRESS"},
    "IN_PROGRESS": {"REFERRED", "RESOLVED"},
    "REFERRED": {"IN_PROGRESS", "RESOLVED"},
    "RESOLVED": {"CLOSED", "IN_PROGRESS"},
    "CLOSED": set(),
}


def is_transition_allowed(current_status, new_status):
    """Whether a responder may move a case from current_status to new_status.

    Keeping a status unchanged is always allowed, since that covers updates
    that only touch risk level or notes. Admin is not bound by this helper;
    it is enforced only for responder-driven status changes.
    """
    if current_status == new_status:
        return True
    return new_status in ALLOWED_TRANSITIONS.get(current_status, set())


def allowed_next_statuses(current_status):
    return sorted(ALLOWED_TRANSITIONS.get(current_status, set()) | {current_status})
