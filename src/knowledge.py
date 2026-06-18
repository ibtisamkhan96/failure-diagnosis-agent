"""Curated failure-analysis knowledge base.

Failure-mode signatures follow standard failure-analysis references (ASM Handbook Vol 11,
Failure Analysis and Prevention). Material entries are rough engineering values for screening,
not design data. Keep claims standard and honest; the agent is told to flag anything uncertain.
"""

# ---------------------------------------------------------------------------
# Failure modes: the nine most common mechanical/materials failure mechanisms.
# Each card drives both the rule-based screener and the agent's explanations.
# ---------------------------------------------------------------------------
FAILURE_MODES = {
    "fatigue": {
        "name": "Fatigue",
        "summary": "Cracks initiate and grow under repeated (cyclic) loading at stresses below the yield strength, then fail suddenly once the remaining section can no longer carry the load.",
        "conditions": ["Cyclic or fluctuating load", "Stress concentration (notch, hole, weld toe, fillet)", "Often well below yield stress"],
        "evidence": ["Beach marks / clamshell marks", "Microscopic striations", "A flat fatigue zone plus a rough final-overload zone", "Little or no gross plastic deformation", "Crack starts at a surface stress raiser"],
        "tests": ["Fractography (SEM) for striations", "Map the initiation site and stress raiser", "Cyclic stress and S-N estimate", "Check surface finish and residual stress"],
        "prevent": ["Remove stress concentrations and improve fillet radii", "Improve surface finish; shot peen for compressive residual stress", "Lower the cyclic stress range or add redundancy"],
    },
    "brittle_fracture": {
        "name": "Brittle fracture",
        "summary": "Sudden fracture with almost no plastic deformation, usually when a material is below its ductile-to-brittle transition temperature, loaded fast, or contains a sharp flaw.",
        "conditions": ["Low temperature (below the transition temperature)", "High strain rate or impact", "Pre-existing flaw or sharp notch", "Low-toughness material (many BCC steels, cast iron, high-strength steel)"],
        "evidence": ["Flat, bright, faceted (cleavage) surface", "Chevron marks pointing back to the origin", "No necking or thinning", "Fast, often loud, single-event failure"],
        "tests": ["Charpy impact across temperature (find the transition)", "Fracture toughness", "Check service temperature vs transition temperature", "Look for the initiating flaw"],
        "prevent": ["Use a tougher material or one with a lower transition temperature", "Keep service temperature above the transition", "Reduce section thickness and sharp notches; control flaws"],
    },
    "ductile_overload": {
        "name": "Ductile overload",
        "summary": "A single load exceeded the strength of the part, which yielded and tore after visible plastic deformation.",
        "conditions": ["Single overload above yield, then ultimate strength", "Often an unexpected or off-design load", "Undersized section or wrong material"],
        "evidence": ["Gross plastic deformation, necking or bending", "Dull, fibrous, dimpled fracture surface", "Shear lips at the edges", "Failure traces to one overload event"],
        "tests": ["Confirm section size and actual loads", "Tensile test to confirm strength", "Dimpled rupture under SEM", "Reconstruct the loading event"],
        "prevent": ["Increase section or use a stronger material", "Confirm real service loads and add a margin", "Protect against off-design overloads"],
    },
    "general_corrosion": {
        "name": "General / pitting corrosion",
        "summary": "Electrochemical loss of material in a corrosive environment, either fairly uniform thinning or localised pitting, which reduces the load-bearing section over time.",
        "conditions": ["Corrosive environment (humid, marine, acidic, alkaline)", "Unprotected or galvanically unfavourable material", "Stagnant or chloride-rich conditions for pitting"],
        "evidence": ["Material loss, thinning, or pits", "Oxide, rust, or corrosion product", "Roughened or perforated surface", "Progressive loss over service time"],
        "tests": ["Identify the environment and corrosion product", "Measure wall loss and pit depth", "Check alloy vs environment compatibility", "Look for galvanic couples"],
        "prevent": ["Select a compatible alloy or add coatings/inhibitors", "Control the environment (drainage, chlorides, pH)", "Avoid galvanic couples and crevices"],
    },
    "stress_corrosion_cracking": {
        "name": "Stress corrosion cracking (SCC)",
        "summary": "Cracking from the combination of a sustained tensile stress, a specific corrosive environment, and a susceptible alloy, even when each factor alone would be harmless.",
        "conditions": ["Sustained tensile stress (applied or residual)", "Specific environment (chlorides for austenitic stainless, ammonia for brass)", "Susceptible alloy"],
        "evidence": ["Fine, often branched cracks", "Little visible corrosion or deformation", "Cracking transgranular or intergranular under the microscope", "Develops over time under steady stress"],
        "tests": ["Identify the environment (chlorides, ammonia, caustic)", "Measure residual stress", "Metallography of crack path", "Confirm alloy susceptibility"],
        "prevent": ["Remove the specific environment or the residual stress (stress relief)", "Change to a resistant alloy", "Add coatings or cathodic protection"],
    },
    "corrosion_fatigue": {
        "name": "Corrosion fatigue",
        "summary": "Cyclic loading in a corrosive environment, which lowers the fatigue strength and removes the usual fatigue limit, so cracks grow faster than in air.",
        "conditions": ["Cyclic load plus a corrosive environment", "No safe fatigue limit (unlike fatigue in air)", "Often marine, humid, or chemical service"],
        "evidence": ["Fatigue-like cracking with corrosion products in the crack", "Multiple initiation sites and pits", "Faster growth than dry fatigue"],
        "tests": ["Fractography with chemistry of the crack faces", "Identify the environment", "Estimate cyclic stress and pit-to-crack transition"],
        "prevent": ["Protect the surface (coatings, inhibitors, cathodic protection)", "Reduce cyclic stress", "Select a more resistant alloy"],
    },
    "creep": {
        "name": "Creep",
        "summary": "Slow, time-dependent deformation under sustained load at high temperature (typically above about 0.4 of the melting temperature), ending in rupture.",
        "conditions": ["High temperature (boilers, turbines, engines)", "Sustained load over long times", "Stress that is safe at room temperature"],
        "evidence": ["Gradual elongation, bulging, or sagging", "Grain-boundary cavities and voids", "Oxidised, often intergranular fracture", "Long time to failure"],
        "tests": ["Confirm metal temperature and time at temperature", "Metallography for creep voids", "Compare with creep-rupture data"],
        "prevent": ["Lower the metal temperature or stress", "Use a creep-resistant alloy (superalloy)", "Set and respect a service-life limit"],
    },
    "wear_erosion": {
        "name": "Wear / erosion",
        "summary": "Progressive surface loss from relative motion (sliding, rolling) or impacting particles and fluid, which changes dimensions and can trigger a secondary failure.",
        "conditions": ["Sliding, rolling, or particle/fluid impingement", "Inadequate lubrication or hardness", "Abrasive or high-velocity media"],
        "evidence": ["Surface loss, grooves, scoring, or polishing", "Dimensional change at contact surfaces", "Debris or galling", "No bulk fracture at first"],
        "tests": ["Inspect contact surfaces and measure loss", "Check lubrication and hardness", "Identify the abrasive or erodent"],
        "prevent": ["Improve lubrication and surface hardness or coatings", "Reduce contact stress and abrasive ingress", "Select wear-resistant materials"],
    },
    "hydrogen_embrittlement": {
        "name": "Hydrogen embrittlement",
        "summary": "Loss of ductility and delayed cracking in high-strength steels when atomic hydrogen (from plating, pickling, welding, or service) enters the metal under stress.",
        "conditions": ["High-strength steel (roughly above 1000 MPa)", "Hydrogen source (electroplating, acid pickling, cathodic protection, H2S service)", "Sustained tensile stress"],
        "evidence": ["Delayed, sudden brittle cracking after loading", "Flat fracture, often intergranular", "Little deformation despite a normally ductile steel", "Failure hours to days after assembly"],
        "tests": ["Check for a hydrogen source in processing or service", "Hardness/strength level of the steel", "Intergranular fracture under SEM"],
        "prevent": ["Bake out hydrogen after plating", "Avoid hydrogen-charging processes for high-strength parts", "Lower the strength level or sustained stress"],
    },
}

# ---------------------------------------------------------------------------
# Material reference (rough screening values, not design data).
# ---------------------------------------------------------------------------
MATERIALS = {
    "mild steel": {"class": "bcc_steel", "uts_mpa": "400 to 550", "notes": "Ductile at room temperature but has a ductile-to-brittle transition; rusts readily.", "watch": ["brittle_fracture", "fatigue", "general_corrosion"]},
    "structural steel": {"class": "bcc_steel", "uts_mpa": "400 to 550", "notes": "BCC steel; tough above its transition temperature, brittle below it.", "watch": ["brittle_fracture", "fatigue"]},
    "high-strength steel": {"class": "high_strength_steel", "uts_mpa": "1000 to 2000", "notes": "Strong but notch-sensitive and prone to hydrogen embrittlement.", "watch": ["hydrogen_embrittlement", "brittle_fracture", "fatigue"]},
    "cast iron": {"class": "cast_iron", "uts_mpa": "150 to 400", "notes": "Brittle, low toughness, good in compression and wear, poor in tension/impact.", "watch": ["brittle_fracture", "wear_erosion"]},
    "304 stainless": {"class": "stainless", "uts_mpa": "500 to 700", "notes": "Austenitic; tough and corrosion resistant but susceptible to chloride SCC.", "watch": ["stress_corrosion_cracking", "general_corrosion", "fatigue"]},
    "316 stainless": {"class": "stainless", "uts_mpa": "500 to 700", "notes": "Better chloride resistance than 304 but still SCC-prone in hot chlorides.", "watch": ["stress_corrosion_cracking", "general_corrosion"]},
    "aluminium 6061": {"class": "aluminium", "uts_mpa": "250 to 310", "notes": "Light, no clear fatigue limit, can suffer SCC in some tempers.", "watch": ["fatigue", "corrosion_fatigue", "stress_corrosion_cracking"]},
    "aluminium 7075": {"class": "aluminium", "uts_mpa": "500 to 570", "notes": "High strength aluminium, notably SCC-susceptible in the peak-aged temper.", "watch": ["stress_corrosion_cracking", "fatigue"]},
    "titanium ti-6al-4v": {"class": "titanium", "uts_mpa": "900 to 1000", "notes": "Strong, light, corrosion resistant; watch fatigue and hot-salt effects.", "watch": ["fatigue"]},
    "brass": {"class": "copper_alloy", "uts_mpa": "300 to 550", "notes": "Copper-zinc alloy; classic ammonia SCC (season cracking) and dezincification.", "watch": ["stress_corrosion_cracking", "general_corrosion"]},
    "copper": {"class": "copper_alloy", "uts_mpa": "200 to 360", "notes": "Ductile, corrosion resistant in many environments, soft so wears.", "watch": ["wear_erosion", "fatigue"]},
    "nickel superalloy": {"class": "superalloy", "uts_mpa": "1000 to 1300", "notes": "For high-temperature service (turbines); creep and oxidation are the limits.", "watch": ["creep", "fatigue"]},
}
