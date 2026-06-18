"""Gradio UI for the Failure Diagnosis Agent, for Hugging Face Spaces.

Users bring their own Anthropic API key (password field). The key is used only for that
request and is never stored. Agent steps stream live; the report renders as Markdown.
"""

import gradio as gr
import anthropic

from src.agent import run_agent_stream

MODELS = ["claude-sonnet-4-6", "claude-opus-4-8"]

EXAMPLES = [
    "A structural steel bolt in a bridge snapped in winter. The fracture was flat and bright with no bending, and it failed suddenly in the cold.",
    "An aluminium aircraft bracket cracked after years of service. The fracture shows clear beach marks starting at a bolt hole, with no overall bending.",
    "A 304 stainless steel pipe carrying hot chloride solution developed fine branching cracks after a few months, with almost no corrosion or deformation visible.",
    "A high-strength steel fastener cracked two days after it was installed, with a flat brittle fracture. It had been electroplated.",
]

INTRO = """
# Failure Diagnosis Agent

Describe a component failure and this agent works it like a forensic engineer. It pulls out the
evidence, screens the likely failure modes (fatigue, brittle fracture, corrosion, SCC, creep,
and more), checks the material, and writes a ranked diagnosis with a fishbone and the tests that
would confirm it.

Part of the **Agentic Matter** series by [Ibtisam Ahmed Khan](https://linkedin.com/in/ibtisam-ahmed-khan).
Bring your own Anthropic API key. It is used only for your request and is never stored. This is a
screening aid, not a substitute for physical examination.
"""


def go(api_key, case, model):
    key = (api_key or "").strip()
    c = (case or "").strip()
    if not key.startswith("sk-"):
        yield "Paste your Anthropic API key (it starts with sk-ant-). It is used only for this request and never stored.", ""
        return
    if not c:
        yield "Describe the failure first.", ""
        return
    try:
        for log, report in run_agent_stream(c, api_key=key, model=model):
            yield log, report
    except anthropic.AuthenticationError:
        yield "That API key was rejected. Check that it is correct and has credit.", ""
    except Exception as e:
        yield f"Something went wrong: {e}", ""


with gr.Blocks(title="Failure Diagnosis Agent") as demo:
    gr.Markdown(INTRO)
    with gr.Row():
        api_key = gr.Textbox(label="Anthropic API key", type="password", placeholder="sk-ant-...", scale=3)
        model = gr.Dropdown(MODELS, value=MODELS[0], label="Model", scale=1)
    case = gr.Textbox(label="Describe the failure", lines=4, placeholder=EXAMPLES[0])
    run_btn = gr.Button("Diagnose", variant="primary")
    gr.Examples(examples=[[e] for e in EXAMPLES], inputs=case, label="Example cases")
    gr.Markdown("Your key is used only for this request and is never stored.")
    with gr.Row():
        steps = gr.Textbox(label="Agent steps (live)", lines=14, max_lines=30)
        report = gr.Markdown(label="Diagnosis")
    run_btn.click(go, [api_key, case, model], [steps, report])

if __name__ == "__main__":
    demo.launch()
