"""Gradio UI for the Failure Diagnosis Agent, for Hugging Face Spaces.

Users bring their own Anthropic API key (password field). The key is used only for that
request and is never stored. Agent steps stream live; the report renders as Markdown.
"""

import tempfile

import gradio as gr
import anthropic

from src.agent import run_agent_stream
from src.report import markdown_to_docx

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

You can also upload a photo of the failure. The model reads its macro features (deformation,
fracture orientation, corrosion, large beach marks), but a photo cannot show the micron-scale
features that need an SEM, and the agent says so.

Part of the **Agentic Matter** series by [Ibtisam Ahmed Khan](https://linkedin.com/in/ibtisam-ahmed-khan).
Bring your own Anthropic API key. It is used only for your request and is never stored. This is a
screening aid, not a substitute for physical examination.
"""


def go(api_key, case, image, model):
    key = (api_key or "").strip()
    c = (case or "").strip()
    if not key.startswith("sk-"):
        yield "Paste your Anthropic API key (it starts with sk-ant-). It is used only for this request and never stored.", "", None
        return
    if not c and not image:
        yield "Describe the failure, or upload a photo of it.", "", None
        return
    if not c:
        c = "Diagnose this component failure from the photo and any context provided."

    last_log, last_report = "", ""
    try:
        for log, report in run_agent_stream(c, api_key=key, model=model, image=image):
            last_log, last_report = log, report or last_report
            yield log, report, None
    except anthropic.AuthenticationError:
        yield "That API key was rejected. Check that it is correct and has credit.", "", None
        return
    except Exception as e:
        yield f"Something went wrong: {e}", "", None
        return

    # Build the downloadable Word report once the diagnosis is complete.
    docx_path = None
    if last_report:
        try:
            tmp = tempfile.NamedTemporaryFile(suffix=".docx", delete=False, prefix="failure_report_")
            tmp.close()
            markdown_to_docx(last_report, tmp.name, used_photo=bool(image))
            docx_path = tmp.name
        except Exception:
            docx_path = None
    yield last_log, last_report, docx_path


with gr.Blocks(title="Failure Diagnosis Agent") as demo:
    gr.Markdown(INTRO)
    with gr.Row():
        api_key = gr.Textbox(label="Anthropic API key", type="password", placeholder="sk-ant-...", scale=3)
        model = gr.Dropdown(MODELS, value=MODELS[0], label="Model", scale=1)
    with gr.Row():
        case = gr.Textbox(label="Describe the failure", lines=5, placeholder=EXAMPLES[0], scale=2)
        image = gr.Image(label="Photo of the failure (optional)", type="filepath", scale=1)
    run_btn = gr.Button("Diagnose", variant="primary")
    gr.Examples(examples=[[e] for e in EXAMPLES], inputs=case, label="Example cases")
    gr.Markdown("Your key is used only for this request and is never stored. A photo shows macro features only, not SEM-level detail.")
    with gr.Row():
        steps = gr.Textbox(label="Agent steps (live)", lines=14, max_lines=30)
        report = gr.Markdown(label="Diagnosis")
    download = gr.File(label="Download the failure-analysis report (.docx)")
    run_btn.click(go, [api_key, case, image, model], [steps, report, download])

if __name__ == "__main__":
    demo.launch()
