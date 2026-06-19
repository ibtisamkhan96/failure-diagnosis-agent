---
title: Failure Diagnosis Agent
emoji: 🔧
colorFrom: red
colorTo: gray
sdk: gradio
app_file: app.py
pinned: false
license: mit
---

# Failure Diagnosis Agent

**Live demo:** a Gradio app on Hugging Face Spaces (bring your own Anthropic key, never stored). **Code and a no-key demo:** this repo.

Describe a component failure, or upload a photo of it, and this agent works the case like a forensic engineer. It pulls out the evidence, screens the likely failure modes, checks the material, looks up real precedents, and writes a ranked diagnosis with a fishbone and the standard tests that would confirm it.

Second project in my **Agentic Matter** series, applying agentic AI to materials and mechanical engineering. It pairs with my Engineering Failures, Decoded series: the same forensic thinking, turned into a tool.

## What makes it an agent, not a chatbot

It runs a tool loop and decides its own path: read the case (and photo), screen, then dig into the strongest candidates and find a precedent before it commits.

```
Failure description (+ optional photo)
   │
   ▼
┌────────────────────────────────────────────────┐
│  Claude (agent loop, reads the photo natively)   │
│   extracts structured evidence                   │
│   ├─ screen_failure_modes  ── rule engine ────►  │  ranked first pass over 16 modes
│   ├─ failure_mode_info     ── knowledge ──────►  │  signatures, fractography, ASTM tests
│   ├─ lookup_material       ── knowledge ──────►  │  a material's typical failure modes
│   ├─ search_failure_cases  ── NASA NTRS ──────►  │  real public-domain precedents
│   └─ reason, then write the report               │
└────────────────────────────────────────────────┘
   │
   ▼
Ranked diagnosis (cause · evidence for and against · other candidates · fishbone · next tests + standards)
```

## What is inside

| Piece | Detail |
|------|--------|
| Failure modes | **16**: fatigue, brittle fracture, ductile overload, general/pitting/crevice/intergranular/galvanic corrosion, SCC, corrosion fatigue, hydrogen embrittlement, creep, wear, erosion, fretting, thermal fatigue |
| Each mode carries | a **fractography layer** (macro, camera-visible, vs SEM-only micro features) and the **ASTM/ASM standards** that confirm it (E23, E466, E647, G36, E139, F519, ...) |
| Materials | **33** common alloys with rough property ranges and the modes to watch |
| Screener | a deterministic, dependency-free rule engine that ranks modes from structured evidence and shows the clue behind every score |
| Case precedents | live search of **NASA NTRS** technical reports (public domain), with NTSB as a further source |
| Vision | upload a photo; the model reads macro features and feeds them in, flagging that micron detail needs an SEM |
| Standard report | the output follows the **ASM-style failure-analysis report** structure (Summary, Background, Examination and observations, Discussion, Conclusion/root cause, Recommendations, References) and exports as a **downloadable Word .docx**. A sample is in [`examples/sample_report.docx`](examples/sample_report.docx) |
| Agent | Anthropic Python SDK, manual tool-use loop. Model `claude-opus-4-8` by default, set `MODEL` to override |

## Run it

**Offline screener (no API key needed).** Proves the failure-mode logic:

```bash
python -m src.cli --demo
python -m src.cli --screen '{"loading":"static","environment":"marine","fracture_surface":"branched","material_class":"stainless"}'
```

A real captured run is in [`examples/screener_demo.txt`](examples/screener_demo.txt).

**Full agent (needs a key).** Describe a failure, optionally with a photo:

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...        # or copy .env.example to .env
python -m src.cli "A 304 stainless pipe in hot chloride developed fine branching cracks after a few months, with little corrosion or deformation."
python -m src.cli --image fracture.jpg "This shaft snapped in service."
python -m src.cli --report diagnosis.docx "A 4340 steel fastener cracked two days after plating."
```

The `--report` flag (and the Download button in the app) saves a formatted ASM-style Word report. Every report carries a disclaimer that it is a preliminary screening, that the recommended tests have not been performed, and that conclusions need hands-on confirmation.

## On the photo feature, honestly

A photograph shows **macro** evidence: gross deformation, fracture orientation, large beach marks, corrosion and oxide colour, pits, scoring. It cannot show the **micron-scale** features that actually confirm a mechanism (fatigue striations, ductile dimples, cleavage facets), which need an SEM. The agent is told to read only what is visible, to flag the SEM step, and not to over-read an image. It is a screening aid, not fractography.

## What is verified

- The deterministic screener runs with no key and ranks the right mode first across modes: cold flat-bright steel scores brittle fracture, branched cracks in stainless score SCC, dissimilar metals in seawater score galvanic corrosion, a clamped joint with oxide debris scores fretting, and a hot sustained-load superalloy scores creep (see the example file).
- The NASA NTRS case search is tested live and returns real technical reports.
- The agent loop and image encoding are built against the Anthropic SDK and import cleanly. The reasoning step needs your key, so run the commands above for the full report.

## Sources

Mechanisms and fractography follow standard references, principally ASM Handbook Volume 11 (Failure Analysis and Prevention) and Volume 12 (Fractography). Confirming tests cite ASTM standards by number (their text is copyrighted and is not reproduced). Case precedents come from NASA NTRS (public domain). Material values are rough engineering ranges for screening, not design data.

---

*Built by Ibtisam Ahmed Khan · June 2026 · [linkedin.com/in/ibtisam-ahmed-khan](https://linkedin.com/in/ibtisam-ahmed-khan) · part of the Agentic Matter series*
