from dataclasses import dataclass


@dataclass(frozen=True)
class RiskAssessment:
    level: str
    score: int
    factors: tuple[str, ...]

    @property
    def explanation(self):
        if not self.factors:
            return "No immediate safety indicators were selected; the case still requires review."
        return "Risk level is based on: " + "; ".join(self.factors) + "."


RISK_RULES = (
    ("immediate_danger", 4, "possible immediate danger"),
    ("threat_to_life", 4, "threats to life"),
    ("weapon_involved", 4, "weapon involvement or mention"),
    ("medical_attention", 2, "possible need for medical attention"),
    ("dependants_at_risk", 2, "children or dependants possibly at immediate risk"),
)


def assess_incident_risk(indicators):
    """Return a deterministic, explainable risk classification from safety indicators."""
    score = 0
    factors = []
    for field, points, label in RISK_RULES:
        value = indicators.get(field, False) if isinstance(indicators, dict) else getattr(indicators, field, False)
        if value:
            score += points
            factors.append(label)

    if score == 0:
        level = "LOW"
    elif score <= 3:
        level = "MEDIUM"
    elif score <= 7:
        level = "HIGH"
    else:
        level = "CRITICAL"
    return RiskAssessment(level=level, score=score, factors=tuple(factors))
