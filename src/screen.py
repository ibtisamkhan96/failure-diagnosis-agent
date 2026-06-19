"""Rule-based failure-mode screener.

Deterministic and dependency-free, so it runs and is verifiable with no API key. It scores the
failure modes against structured evidence and explains which clues drove each score. The agent
uses this as a first pass, then reasons over it; an engineer can run it directly.
"""

from .knowledge import FAILURE_MODES

# Evidence fields and their allowed values. Unknown values simply score nothing.
EVIDENCE_FIELDS = {
    "loading": ["static", "cyclic", "impact", "sustained", "sliding", "flow"],
    "temperature": ["cryogenic", "low", "ambient", "elevated", "high"],
    "environment": ["dry", "humid", "marine", "acidic", "alkaline", "high_purity"],
    "fracture_surface": ["flat_bright", "dimpled_fibrous", "beach_marks", "branched", "pits",
                          "crevice_attack", "intergranular", "uniform_thinning", "grooves_scoring",
                          "wavy_smooth", "oxide_debris", "crack_network", "none"],
    "deformation": ["none", "slight", "gross_necking"],
    "onset": ["sudden", "progressive", "delayed"],
    "material_class": ["bcc_steel", "stainless", "aluminium", "titanium", "cast_iron",
                        "copper_alloy", "high_strength_steel", "superalloy", "magnesium", "zinc", "solder"],
    "joint": ["none", "dissimilar_metals", "crevice_or_gasket", "press_fit_clamped"],
    "hydrogen_source": ["yes", "no"],
    "thermal_cycling": ["yes", "no"],
}

# Positive indicators per mode: (field, value, weight, short reason).
RULES = {
    "fatigue": [
        ("loading", "cyclic", 3, "cyclic loading"), ("fracture_surface", "beach_marks", 4, "beach marks"),
        ("deformation", "none", 1, "no gross deformation"), ("onset", "progressive", 2, "progressive cracking"),
    ],
    "brittle_fracture": [
        ("fracture_surface", "flat_bright", 4, "flat bright cleavage surface"), ("temperature", "low", 2, "low temperature"),
        ("temperature", "cryogenic", 3, "cryogenic temperature"), ("material_class", "bcc_steel", 1, "BCC steel transition"),
        ("material_class", "cast_iron", 1, "low-toughness cast iron"), ("material_class", "high_strength_steel", 1, "notch-sensitive steel"),
        ("deformation", "none", 2, "no plastic deformation"), ("onset", "sudden", 1, "sudden failure"), ("loading", "impact", 1, "impact loading"),
    ],
    "ductile_overload": [
        ("deformation", "gross_necking", 4, "gross necking / bending"), ("fracture_surface", "dimpled_fibrous", 3, "dimpled fibrous surface"),
        ("loading", "static", 1, "single static overload"), ("loading", "impact", 1, "overload event"), ("onset", "sudden", 1, "single event"),
    ],
    "general_corrosion": [
        ("fracture_surface", "uniform_thinning", 4, "uniform thinning"), ("environment", "humid", 2, "humid environment"),
        ("environment", "marine", 2, "marine environment"), ("environment", "acidic", 3, "acidic environment"),
        ("environment", "alkaline", 2, "alkaline environment"), ("onset", "progressive", 2, "progressive loss"),
    ],
    "pitting_corrosion": [
        ("fracture_surface", "pits", 4, "discrete pits"), ("environment", "marine", 3, "chloride environment"),
        ("material_class", "stainless", 2, "passive stainless"), ("material_class", "aluminium", 1, "passive aluminium"),
        ("onset", "progressive", 2, "progressive over time"),
    ],
    "crevice_corrosion": [
        ("fracture_surface", "crevice_attack", 4, "attack at a crevice"), ("joint", "crevice_or_gasket", 3, "shielded crevice / gasket"),
        ("material_class", "stainless", 2, "passive alloy in a crevice"), ("environment", "marine", 2, "chloride environment"),
        ("onset", "progressive", 1, "progressive"),
    ],
    "intergranular_corrosion": [
        ("fracture_surface", "intergranular", 3, "grain-boundary attack"), ("material_class", "stainless", 3, "sensitised stainless"),
        ("environment", "acidic", 1, "aggressive environment"), ("environment", "marine", 1, "chloride environment"), ("onset", "progressive", 1, "progressive"),
    ],
    "galvanic_corrosion": [
        ("joint", "dissimilar_metals", 4, "dissimilar metals coupled"), ("environment", "marine", 2, "marine electrolyte"),
        ("environment", "humid", 1, "humid electrolyte"), ("fracture_surface", "uniform_thinning", 1, "preferential loss"), ("onset", "progressive", 2, "progressive"),
    ],
    "stress_corrosion_cracking": [
        ("fracture_surface", "branched", 4, "fine branched cracks"), ("environment", "marine", 2, "chloride environment"),
        ("environment", "acidic", 2, "aggressive environment"), ("environment", "alkaline", 2, "caustic environment"),
        ("loading", "static", 2, "sustained tensile stress"), ("loading", "sustained", 2, "sustained tensile stress"),
        ("material_class", "stainless", 2, "SCC-susceptible stainless"), ("material_class", "aluminium", 1, "SCC-susceptible aluminium"),
        ("material_class", "copper_alloy", 2, "ammonia SCC in brass"), ("deformation", "none", 1, "little deformation"),
    ],
    "corrosion_fatigue": [
        ("loading", "cyclic", 2, "cyclic loading"), ("environment", "marine", 3, "marine environment"),
        ("environment", "humid", 2, "humid environment"), ("environment", "acidic", 2, "aggressive environment"),
        ("fracture_surface", "beach_marks", 2, "fatigue features"), ("fracture_surface", "pits", 2, "pitting plus cracking"),
    ],
    "hydrogen_embrittlement": [
        ("material_class", "high_strength_steel", 3, "high-strength steel"), ("hydrogen_source", "yes", 3, "a hydrogen source"),
        ("onset", "delayed", 3, "delayed cracking"), ("fracture_surface", "flat_bright", 2, "flat brittle surface"),
        ("fracture_surface", "intergranular", 2, "intergranular fracture"), ("environment", "acidic", 1, "charging environment"), ("deformation", "none", 1, "brittle despite ductile steel"),
    ],
    "creep": [
        ("temperature", "high", 4, "high metal temperature"), ("temperature", "elevated", 3, "elevated temperature"),
        ("loading", "sustained", 3, "sustained load"), ("onset", "progressive", 2, "slow time-dependent change"),
        ("onset", "delayed", 1, "long time to failure"), ("deformation", "slight", 1, "gradual elongation"), ("material_class", "superalloy", 1, "high-temperature alloy"),
    ],
    "wear": [
        ("loading", "sliding", 4, "sliding / rolling contact"), ("fracture_surface", "grooves_scoring", 3, "grooves and scoring"),
        ("onset", "progressive", 2, "progressive surface loss"), ("deformation", "none", 1, "no bulk deformation"),
    ],
    "erosion": [
        ("loading", "flow", 4, "fluid or particle flow"), ("fracture_surface", "wavy_smooth", 3, "wavy eroded surface"),
        ("environment", "marine", 1, "flowing seawater"), ("onset", "progressive", 2, "progressive loss"),
    ],
    "fretting": [
        ("joint", "press_fit_clamped", 4, "clamped or press-fit joint"), ("fracture_surface", "oxide_debris", 4, "fretting oxide debris"),
        ("loading", "cyclic", 1, "vibration / micro-slip"), ("onset", "progressive", 1, "progressive"),
    ],
    "thermal_fatigue": [
        ("thermal_cycling", "yes", 4, "repeated thermal cycling"), ("fracture_surface", "crack_network", 4, "crazed crack network"),
        ("temperature", "high", 2, "high temperature"), ("temperature", "elevated", 1, "elevated temperature"), ("onset", "progressive", 1, "progressive"),
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
        return "No failure mode scored above zero. Provide more evidence (loading, temperature, environment, fracture surface, deformation, onset, joint, material)."
    out = ["Ranked failure modes (relative confidence in brackets):"]
    for r in rows:
        out.append(f"  {r['name']}  score {r['score']} [{r['confidence']}]  <- " + ", ".join(r["matched"]))
    return "\n".join(out)
