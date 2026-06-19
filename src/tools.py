"""Tool definitions and dispatch for the failure-diagnosis agent.

Four tools:
  - screen_failure_modes: rule-based ranking of likely failure modes from structured evidence
  - failure_mode_info: the reference card for one mode (signatures, fractography, ASTM tests)
  - lookup_material: rough properties and the modes to watch for a material
  - search_failure_cases: real NASA NTRS technical reports for precedent (public domain)
"""

from .knowledge import FAILURE_MODES, MATERIALS
from .screen import screen, EVIDENCE_FIELDS
from .ntrs import search_ntrs

TOOLS = [
    {
        "name": "screen_failure_modes",
        "description": (
            "Score the likely failure modes from structured evidence. Fill in whatever you can "
            "infer from the case or the photo; leave the rest out. Returns a ranked list with the "
            "clues that drove each score. Use it as a first pass, then read the top modes in detail."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "loading": {"type": "string", "enum": EVIDENCE_FIELDS["loading"], "description": "How it was loaded (flow = fluid/particle flow)"},
                "temperature": {"type": "string", "enum": EVIDENCE_FIELDS["temperature"]},
                "environment": {"type": "string", "enum": EVIDENCE_FIELDS["environment"]},
                "fracture_surface": {"type": "string", "enum": EVIDENCE_FIELDS["fracture_surface"], "description": "Appearance of the fracture or surface"},
                "deformation": {"type": "string", "enum": EVIDENCE_FIELDS["deformation"]},
                "onset": {"type": "string", "enum": EVIDENCE_FIELDS["onset"]},
                "material_class": {"type": "string", "enum": EVIDENCE_FIELDS["material_class"]},
                "joint": {"type": "string", "enum": EVIDENCE_FIELDS["joint"], "description": "Joint type, for crevice / galvanic / fretting"},
                "hydrogen_source": {"type": "string", "enum": EVIDENCE_FIELDS["hydrogen_source"]},
                "thermal_cycling": {"type": "string", "enum": EVIDENCE_FIELDS["thermal_cycling"]},
            },
        },
    },
    {
        "name": "failure_mode_info",
        "description": "Get the full reference card for one failure mode: summary, conditions, evidence, fractography (macro vs SEM), the ASTM/ASM tests that confirm it, and prevention.",
        "input_schema": {"type": "object", "properties": {"mode": {"type": "string", "enum": list(FAILURE_MODES.keys())}}, "required": ["mode"]},
    },
    {
        "name": "lookup_material",
        "description": "Get rough properties and the failure modes to watch for a material (e.g. 'mild steel', '316 stainless', 'aluminium 7075', '4340 alloy steel', 'brass', 'inconel 718').",
        "input_schema": {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]},
    },
    {
        "name": "search_failure_cases",
        "description": "Search NASA NTRS technical reports (public domain) for real failure-analysis precedents and fractography studies relevant to the case. Use it to find prior cases and to cite a real source.",
        "input_schema": {"type": "object", "properties": {"query": {"type": "string", "description": "e.g. 'fatigue fracture aluminium rivet hole'"}}, "required": ["query"]},
    },
]


class ToolBox:
    def __init__(self, on_event=None):
        self.on_event = on_event or (lambda *_: None)

    def run(self, name, args):
        if name == "screen_failure_modes":
            return self._screen(args)
        if name == "failure_mode_info":
            return self._mode_info(args.get("mode", ""))
        if name == "lookup_material":
            return self._material(args.get("name", ""))
        if name == "search_failure_cases":
            return self._cases(args.get("query", ""))
        return f"Unknown tool: {name}"

    def _screen(self, evidence):
        rows = screen(evidence)
        given = ", ".join(f"{k}={v}" for k, v in evidence.items() if v)
        self.on_event("screen_failure_modes", given or "no evidence given")
        if not rows:
            return "No mode scored above zero. Add evidence such as loading, temperature, environment, fracture surface, deformation, onset, joint, or material."
        out = ["Ranked candidates (score, relative confidence):"]
        for r in rows:
            out.append(f"- {r['name']} (mode id: {r['mode']}): score {r['score']}, confidence {r['confidence']}. Clues: " + ", ".join(r["matched"]))
        return "\n".join(out)

    def _mode_info(self, mode):
        self.on_event("failure_mode_info", mode)
        m = FAILURE_MODES.get(mode)
        if not m:
            return f"Unknown mode '{mode}'. Options: " + ", ".join(FAILURE_MODES.keys())
        fr = m["fractography"]
        return (
            f"{m['name']}\nSummary: {m['summary']}\n"
            f"Conditions: {'; '.join(m['conditions'])}\n"
            f"Evidence: {'; '.join(m['evidence'])}\n"
            f"Fractography, macro (camera): {fr['macro']}\n"
            f"Fractography, micro (SEM only): {fr['micro']}\n"
            f"Confirming standards: {'; '.join(m['astm'])}\n"
            f"Other tests: {'; '.join(m['tests'])}\n"
            f"Prevention: {'; '.join(m['prevent'])}"
        )

    def _material(self, name):
        self.on_event("lookup_material", name)
        key = name.strip().lower()
        mat = MATERIALS.get(key)
        if not mat:
            for k, v in MATERIALS.items():
                if key and (key in k or k in key):
                    mat, key = v, k
                    break
        if not mat:
            return f"No entry for '{name}'. Known materials: " + ", ".join(MATERIALS.keys())
        watch = ", ".join(FAILURE_MODES[w]["name"] for w in mat["watch"])
        return f"{key}: class {mat['class']}, UTS approx {mat['uts_mpa']} MPa.\nNotes: {mat['notes']}\nWatch for: {watch}"

    def _cases(self, query):
        self.on_event("search_failure_cases", query)
        try:
            cases = search_ntrs(query, 6)
        except Exception as e:
            return f"search_failure_cases failed: {e}"
        if not cases:
            return f"No NASA NTRS reports found for {query!r}."
        out = ["NASA NTRS technical reports (public domain):"]
        for c in cases:
            out.append(f"- ({c['year']}) {c['title']} [{c['url']}]\n  {c['abstract'][:300]}")
        return "\n".join(out)
