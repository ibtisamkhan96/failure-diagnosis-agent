"""The agentic loop: Claude works a failure case like a forensic engineer.

Manual, framework-free tool-use loop (Anthropic Python SDK) so the mechanics stay visible. The
first message may include a photo of the failure; the model reads it natively (no separate
vision model). `run_agent_stream` is the single source of truth, used by the CLI and the app.
"""

import os
from .tools import TOOLS, ToolBox
from .vision import build_user_content

# Default to the most capable model per the claude-api guidance; override with MODEL or --model.
DEFAULT_MODEL = os.environ.get("MODEL", "claude-opus-4-8")

SYSTEM = (
    "You are a forensic failure-analysis engineer. Given a described component failure, and "
    "sometimes a photo of it, you work the case methodically.\n\n"
    "If a photo is provided, first describe only the MACRO features you can clearly see: gross "
    "deformation or necking, whether the fracture is flat or on a slant, large beach marks, "
    "corrosion product, rust or oxide colour, pits, scoring, or heat discoloration. Be explicit "
    "that micron-scale features (fatigue striations, ductile dimples, cleavage facets, "
    "intergranular detail) cannot be judged from a photograph and need an SEM. Do not claim to "
    "see features you cannot. Mark low confidence where the image is unclear.\n\n"
    "Then:\n"
    "1. Pull the evidence into the structured fields: loading, temperature, environment, "
    "fracture_surface, deformation, onset, joint, hydrogen_source, thermal_cycling, material_class.\n"
    "2. Call screen_failure_modes with that evidence for a ranked first pass.\n"
    "3. Call failure_mode_info on the top one or two candidates and lookup_material on the "
    "material to confirm or challenge them. Optionally call search_failure_cases for a real NASA "
    "precedent you can cite.\n"
    "4. Note what evidence is missing that would change the answer.\n\n"
    "Then write the report in Markdown using this standard failure-analysis structure, with each "
    "numbered section as a level-2 Markdown heading (## ):\n\n"
    "## 1. Summary\n"
    "One short paragraph: the item, how it failed, and the most likely cause.\n\n"
    "## 2. Background\n"
    "The component, its material and service history, and the reported circumstances of failure, "
    "as far as they are known. State clearly what is unknown.\n\n"
    "## 3. Examination and observations\n"
    "Only what was actually reported or visible in the photo. If from a photo, macro features only, "
    "and state that micron-scale fractography (SEM) was not available. Do not record any test as "
    "performed that was not done.\n\n"
    "## 4. Discussion and analysis\n"
    "Interpret the evidence. Include a fishbone of contributing factors under Material, Design, "
    "Manufacturing, Service and environment, and Maintenance. Compare the leading failure modes and "
    "how to tell them apart.\n\n"
    "## 5. Conclusion: most likely root cause\n"
    "The single most likely mechanism, with the confidence the evidence warrants, and the key "
    "evidence for and against it.\n\n"
    "## 6. Recommendations and next tests\n"
    "The concrete tests that would confirm the cause, naming the relevant ASTM or ASM standards "
    "(for example E23 Charpy, E466 fatigue, G36 SCC, E139 creep, F519 hydrogen), plus corrective and "
    "preventive actions. State clearly that these tests are recommended, not yet done.\n\n"
    "## References\n"
    "The standards named above and any NASA NTRS precedent you cited.\n\n"
    "Rules: reason only from the case, the photo, and what the tools return. Do not invent "
    "material data, numbers, or test results, and do not over-read a photo. If evidence is thin, "
    "say so and give your best ranked hypothesis with the assumptions stated. This is a screening "
    "and reasoning aid, not a substitute for physical examination, fractography, and lab testing. "
    "Do not use em dashes; use commas, colons, or periods."
)


def run_agent_stream(case, api_key=None, model=None, max_steps=12, image=None):
    """Run the agent on a failure case (optionally with a photo), yielding (log, report)."""
    import anthropic

    client = anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()
    model = model or DEFAULT_MODEL

    log = []

    def on_event(kind, detail):
        log.append(f"  -> {kind}: {detail}")

    box = ToolBox(on_event=on_event)
    messages = [{"role": "user", "content": build_user_content(case, image)}]
    log.append(("Working the case (with photo): " if image else "Working the case: ") + case)
    yield "\n".join(log), ""

    for step in range(max_steps):
        log.append(f"[step {step + 1}] reasoning ...")
        yield "\n".join(log), ""

        resp = client.messages.create(
            model=model,
            max_tokens=8000,
            thinking={"type": "adaptive"},
            system=SYSTEM,
            tools=TOOLS,
            messages=messages,
        )
        messages.append({"role": "assistant", "content": resp.content})

        if resp.stop_reason == "refusal":
            yield "\n".join(log + ["[the model declined this request]"]), "The model declined to answer this request."
            return
        if resp.stop_reason != "tool_use":
            text = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text").strip()
            log.append("[done] wrote the diagnosis")
            yield "\n".join(log), text
            return

        tool_results = []
        for block in resp.content:
            if getattr(block, "type", None) == "tool_use":
                result = box.run(block.name, block.input)
                tool_results.append({"type": "tool_result", "tool_use_id": block.id, "content": result})
        messages.append({"role": "user", "content": tool_results})
        yield "\n".join(log), ""

    yield "\n".join(log + ["[stopped at the step limit]"]), "Stopped after the step limit. Try giving more specific evidence."


def run_agent(case, model=None, max_steps=12, verbose=True, image=None):
    """CLI helper: consume the stream, print new log lines live, return the final report."""
    final, printed = "", 0
    for log, report in run_agent_stream(case, model=model, max_steps=max_steps, image=image):
        if verbose:
            lines = log.split("\n")
            for line in lines[printed:]:
                print(line)
            printed = len(lines)
        if report:
            final = report
    return final, []
