"""The agentic loop: Claude works a failure case like a forensic engineer.

Manual, framework-free tool-use loop (Anthropic Python SDK) so the mechanics stay visible.
`run_agent_stream` is the single source of truth, consumed by the CLI and the Gradio app.
"""

import os
from .tools import TOOLS, ToolBox

# Default to the most capable model per the claude-api guidance; override with MODEL or --model.
DEFAULT_MODEL = os.environ.get("MODEL", "claude-opus-4-8")

SYSTEM = (
    "You are a forensic failure-analysis engineer. Given a described component failure, you work "
    "it methodically:\n"
    "1. Pull out the evidence: material, loading, temperature, environment, fracture or surface "
    "appearance, deformation, and whether failure was sudden, progressive, or delayed.\n"
    "2. Call screen_failure_modes with that evidence to get a ranked first pass.\n"
    "3. Call failure_mode_info on the top one or two candidates, and lookup_material on the "
    "material, to confirm or challenge them.\n"
    "4. Note what evidence is missing that would change the answer, and say what test would settle it.\n\n"
    "Then write a structured report with these sections:\n"
    "- Most likely cause: the top failure mode and a one-line why.\n"
    "- Evidence for and against: bullet the supporting clues and anything that does not fit.\n"
    "- Other candidates: the next one or two modes and how to tell them apart.\n"
    "- Fishbone: likely contributing factors under Material, Design, Manufacturing, Service and "
    "environment, and Maintenance.\n"
    "- Recommended next tests: the concrete checks that would confirm the cause.\n\n"
    "Rules: reason only from the case and what the tools return. Do not invent material data, "
    "numbers, or test results. If the evidence is thin, say so and give your best ranked hypothesis "
    "with the assumptions stated. This is a screening aid, not a substitute for physical "
    "examination, so keep it honest. Do not use em dashes; use commas, colons, or periods. "
    "Format the report in Markdown."
)


def run_agent_stream(case, api_key=None, model=None, max_steps=12):
    """Run the agent on a failure case, yielding (log_text, report_markdown) as it works."""
    import anthropic

    client = anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()
    model = model or DEFAULT_MODEL

    log = []

    def on_event(kind, detail):
        log.append(f"  -> {kind}: {detail}")

    box = ToolBox(on_event=on_event)
    messages = [{"role": "user", "content": case}]
    log.append(f"Working the case: {case}")
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


def run_agent(case, model=None, max_steps=12, verbose=True):
    """CLI helper: consume the stream, print new log lines live, return the final report."""
    final, printed = "", 0
    for log, report in run_agent_stream(case, model=model, max_steps=max_steps):
        if verbose:
            lines = log.split("\n")
            for line in lines[printed:]:
                print(line)
            printed = len(lines)
        if report:
            final = report
    return final, []
