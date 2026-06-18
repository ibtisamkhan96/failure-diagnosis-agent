"""Tool definitions and dispatch for the failure-diagnosis agent.

Three tools:
  - screen_failure_modes: rule-based ranking of likely failure modes from structured evidence
  - failure_mode_info: the reference card for one mode (conditions, evidence, tests, prevention)
  - lookup_material: rough properties and the failure modes to watch for a material
"""

from .knowledge import FAILURE_MODES, MATERIALS
from .screen import screen, EVIDENCE_FIELDS

TOOLS = [
    {
        "name": "screen_failure_modes",
        "description": (
            "Score the likely failure modes from structured evidence. Fill in whatever you can "
            "infer from the case; leave the rest out. Returns a ranked list with the clues that "
            "drove each score. Use this as a first pass, then read the top modes in detail."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "loading": {"type": "string", "enum": EVIDENCE_FIELDS["loading"], "description": "How it was loaded"},
                "temperature": {"type": "string", "enum": EVIDENCE_FIELDS["temperature"], "description": "Service temperature band"},
                "environment": {"type": "string", "enum": EVIDENCE_FIELDS["environment"]},
                "fracture_surface": {"type": "string", "enum": EVIDENCE_FIELDS["fracture_surface"], "description": "Appearance of the fracture or surface"},
                "deformation": {"type": "string", "enum": EVIDENCE_FIELDS["deformation"]},
                "onset": {"type": "string", "enum": EVIDENCE_FIELDS["onset"], "description": "sudden, progressive, or delayed"},
                "material_class": {"type": "string", "enum": EVIDENCE_FIELDS["material_class"]},
                "hydrogen_source": {"type": "string", "enum": EVIDENCE_FIELDS["hydrogen_source"]},
            },
        },
    },
    {
        "name": "failure_mode_info",
        "description": "Get the full reference card for one failure mode: summary, conditions, tell-tale evidence, recommended tests, and prevention.",
        "input_schema": {
            "type": "object",
            "properties": {"mode": {"type": "string", "enum": list(FAILURE_MODES.keys())}},
            "required": ["mode"],
        },
    },
    {
        "name": "lookup_material",
        "description": "Get rough properties and the failure modes to watch for a material (e.g. 'mild steel', '304 stainless', 'aluminium 7075', 'brass').",
        "input_schema": {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        },
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
        return f"Unknown tool: {name}"

    def _screen(self, evidence):
        rows = screen(evidence)
        given = ", ".join(f"{k}={v}" for k, v in evidence.items() if v)
        self.on_event("screen_failure_modes", given or "no evidence given")
        if not rows:
            return "No mode scored above zero. Add evidence such as loading, temperature, environment, fracture surface, deformation, or onset."
        out = ["Ranked candidates (score, relative confidence):"]
        for r in rows:
            out.append(f"- {r['name']} (mode id: {r['mode']}): score {r['score']}, confidence {r['confidence']}. Clues: " + ", ".join(r["matched"]))
        return "\n".join(out)

    def _mode_info(self, mode):
        self.on_event("failure_mode_info", mode)
        m = FAILURE_MODES.get(mode)
        if not m:
            return f"Unknown mode '{mode}'. Options: " + ", ".join(FAILURE_MODES.keys())
        return (
            f"{m['name']}\nSummary: {m['summary']}\n"
            f"Conditions: {'; '.join(m['conditions'])}\n"
            f"Tell-tale evidence: {'; '.join(m['evidence'])}\n"
            f"Recommended tests: {'; '.join(m['tests'])}\n"
            f"Prevention: {'; '.join(m['prevent'])}"
        )

    def _material(self, name):
        self.on_event("lookup_material", name)
        key = name.strip().lower()
        mat = MATERIALS.get(key)
        if not mat:  # forgiving partial match
            for k, v in MATERIALS.items():
                if key and (key in k or k in key):
                    mat, key = v, k
                    break
        if not mat:
            return f"No entry for '{name}'. Known materials: " + ", ".join(MATERIALS.keys())
        watch = ", ".join(FAILURE_MODES[w]["name"] for w in mat["watch"])
        return (f"{key}: class {mat['class']}, UTS approx {mat['uts_mpa']} MPa.\n"
                f"Notes: {mat['notes']}\nWatch for: {watch}")
