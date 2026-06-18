"""Rule-based failure-mode screener.

Deterministic and dependency-free, so it runs and is verifiable with no API key. It scores the
nine failure modes against structured evidence and explains which clues drove each score. The
agent uses this as a first pass, then reasons over it; an engineer can also run it directly.
"""

from .knowledge import FAILURE_MODES

# Evidence fields and their allowed values (free-form is tolerated, unknown values just score 0).
EVIDENCE_FIELDS = {
    "loading": ["static", "cyclic", "impact", "sustained", "sliding"],
    "temperature": ["cryogenic", "low", "ambient", "elevated", "high"],
    "environment": ["dry", "humid", "marine", "acidic", "alkaline", "high_purity"],
    "fracture_surface": ["flat_bright", "dimpled_fibrous", "beach_marks", "branched", "thinning_pits", "rough_torn", "none"],
    "deformation": ["none", "slight", "gross_necking"],
    "onset": ["sudden", "progressive", "delayed"],
    "material_class": ["bcc_steel", "stainless", "aluminium", "titanium", "cast_iron", "copper_alloy", "high_strength_steel", "superalloy"],
    "hydrogen_source": ["yes", "no"],
}

# Positive indicators per mode: (field, value, weight, short reason).
RULES = {
    "fatigue": [
        ("loading", "cyclic", 3, "cyclic loading"),
        ("fracture_surface", "beach_marks", 4, "beach marks on the fracture"),
        ("deformation", "none", 1, "no gross deformation"),
        ("onset", "progressive", 2, "progressive cracking"),
    ],
    "brittle_fracture": [
        ("fracture_surface", "flat_bright", 4, "flat bright cleavage surface"),
        ("temperature", "low", 2, "low service temperature"),
        ("temperature", "cryogenic", 3, "cryogenic temperature"),
        ("material_class", "bcc_steel", 1, "BCC steel, has a transition temperature"),
        ("material_class", "cast_iron", 1, "low-toughness cast iron"),
        ("material_class", "high_strength_steel", 1, "notch-sensitive high-strength steel"),
        ("deformation", "none", 2, "no plastic deformation"),
        ("onset", "sudden", 1, "sudden single-event failure"),
        ("loading", "impact", 1, "impact / high strain rate"),
    ],
    "ductile_overload": [
        ("deformation", "gross_necking", 4, "gross necking / bending"),
        ("fracture_surface", "dimpled_fibrous", 3, "dimpled fibrous surface"),
        ("loading", "static", 1, "single static overload"),
        ("loading", "impact", 1, "overload event"),
        ("onset", "sudden", 1, "single event"),
    ],
    "general_corrosion": [
        ("fracture_surface", "thinning_pits", 3, "thinning and pitting"),
        ("environment", "humid", 2, "humid environment"),
        ("environment", "marine", 3, "marine / chloride environment"),
        ("environment", "acidic", 3, "acidic environment"),
        ("environment", "alkaline", 2, "alkaline environment"),
        ("onset", "progressive", 2, "progressive loss over time"),
    ],
    "stress_corrosion_cracking": [
        ("fracture_surface", "branched", 4, "fine branched cracks"),
        ("environment", "marine", 2, "chloride environment"),
        ("environment", "acidic", 2, "aggressive environment"),
        ("environment", "alkaline", 2, "caustic environment"),
        ("loading", "static", 2, "sustained tensile stress"),
        ("loading", "sustained", 2, "sustained tensile stress"),
        ("material_class", "stainless", 2, "SCC-susceptible austenitic stainless"),
        ("material_class", "aluminium", 1, "SCC-susceptible aluminium temper"),
        ("material_class", "copper_alloy", 2, "ammonia SCC in brass"),
        ("deformation", "none", 1, "little deformation"),
    ],
    "corrosion_fatigue": [
        ("loading", "cyclic", 2, "cyclic loading"),
        ("environment", "marine", 3, "marine environment"),
        ("environment", "humid", 2, "humid environment"),
        ("environment", "acidic", 2, "aggressive environment"),
        ("fracture_surface", "beach_marks", 2, "fatigue features"),
        ("fracture_surface", "thinning_pits", 2, "pitting plus cracking"),
    ],
    "creep": [
        ("temperature", "high", 4, "high metal temperature"),
        ("temperature", "elevated", 3, "elevated temperature"),
        ("loading", "sustained", 3, "sustained load"),
        ("onset", "progressive", 2, "slow time-dependent change"),
        ("onset", "delayed", 1, "long time to failure"),
        ("deformation", "slight", 1, "gradual elongation"),
        ("material_class", "superalloy", 1, "high-temperature alloy in service"),
    ],
    "wear_erosion": [
        ("loading", "sliding", 4, "sliding / rolling contact"),
        ("fracture_surface", "rough_torn", 1, "scored surface"),
        ("fracture_surface", "none", 1, "surface loss without bulk fracture"),
        ("onset", "progressive", 2, "progressive surface loss"),
        ("deformation", "none", 1, "no bulk deformation"),
    ],
    "hydrogen_embrittlement": [
        ("material_class", "high_strength_steel", 3, "high-strength steel"),
        ("hydrogen_source", "yes", 3, "a hydrogen source is present"),
        ("onset", "delayed", 3, "delayed cracking after loading"),
        ("fracture_surface", "flat_bright", 2, "flat brittle, often intergranular, surface"),
        ("environment", "acidic", 1, "acidic / charging environment"),
        ("deformation", "none", 1, "brittle despite a normally ductile steel"),
    ],
}


def screen(evidence):
    """Score every failure mode against the evidence dict. Returns a sorted list of results."""
    results = []
    for mode, rules in RULES.items():
        score, reasons = 0, []
        for field, value, weight, reason in rules:
            if str(evidence.get(field, "")).lower() == value:
                score += weight
                reasons.append(reason)
        if score > 0:
            results.append({"mode": mode, "name": FAILURE_MODES[mode]["name"], "score": score, "matched": reasons})
    if not results:
        return []
    top = max(r["score"] for r in results)
    for r in results:
        r["confidence"] = round(r["score"] / top, 2)  # relative to the strongest candidate
    results.sort(key=lambda r: r["score"], reverse=True)
    return results


def format_screen(evidence):
    rows = screen(evidence)
    if not rows:
        return "No failure mode scored above zero. Provide more evidence (loading, temperature, environment, fracture surface, deformation, onset, material)."
    out = ["Ranked failure modes (relative confidence in brackets):"]
    for r in rows:
        out.append(f"  {r['name']}  score {r['score']} [{r['confidence']}]  <- " + ", ".join(r["matched"]))
    return "\n".join(out)
