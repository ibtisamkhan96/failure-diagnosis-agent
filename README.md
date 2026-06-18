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

Describe a component failure and this agent works it like a forensic engineer. It pulls out the evidence, screens the likely failure modes, checks the material, and writes a ranked diagnosis with a fishbone and the tests that would confirm it. Second project in my **Agentic Matter** series, applying agentic AI to materials and mechanical engineering. It pairs with my [Engineering Failures, Decoded](https://github.com/ibtisamkhan96) series: the same forensic thinking, turned into a tool.

## What makes it an agent, not a chatbot

It runs a tool loop and decides its own path: extract evidence, screen, then dig into the strongest candidates before it commits.

```
Failure description
   │
   ▼
┌───────────────────────────────────────────────┐
│  Claude (agent loop)                            │
│   extracts structured evidence                  │
│   ├─ tool: screen_failure_modes ── rule-based ► │  ranked first pass over 9 modes
│   ├─ tool: failure_mode_info    ── knowledge ►  │  confirm / challenge the top candidates
│   ├─ tool: lookup_material      ── knowledge ►  │  material's typical failure modes
│   └─ reason, then write the report              │
└───────────────────────────────────────────────┘
   │
   ▼
Ranked diagnosis (cause · evidence for and against · other candidates · fishbone · next tests)
```

It is told to reason only from the case and the tools, to flag missing evidence, and never to invent material data or test results.

## What is inside

| Piece | What it is |
|------|-----------|
| Failure modes | 9 mechanisms: fatigue, brittle fracture, ductile overload, general/pitting corrosion, SCC, corrosion fatigue, creep, wear/erosion, hydrogen embrittlement |
| Screener | A deterministic, dependency-free rule engine that ranks modes from structured evidence and shows which clues drove each score |
| Material reference | 12 common engineering materials with rough properties and the modes to watch |
| Agent | Anthropic Python SDK, manual tool-use loop. Model `claude-opus-4-8` by default, set `MODEL` to override |

## Run it

**Offline screener (no API key needed).** Proves the failure-mode logic:

```bash
python -m src.cli --demo
python -m src.cli --screen '{"loading":"cyclic","fracture_surface":"beach_marks","onset":"progressive"}'
```

A real captured run is in [`examples/screener_demo.txt`](examples/screener_demo.txt).

**Full agent (needs a key).** Describe a failure in plain English:

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...        # or copy .env.example to .env
python -m src.cli "A structural steel bolt in a bridge snapped in winter with a flat, bright fracture and no bending. It failed suddenly in the cold."
```

The agent prints each tool call, then the diagnosis.

## What is verified

- The deterministic screener runs end to end with no key and ranks the right mode on test cases: a cold flat-bright steel failure scores brittle fracture first, a beach-marked cyclic failure scores fatigue first, and a branched-crack stainless-in-chloride case scores stress corrosion cracking first (see the example file).
- The agent loop is built against the Anthropic SDK and imports and wires up cleanly. The reasoning step needs your key, so run the command above for the full report.

## Honest notes

- This is a screening and reasoning aid, not a substitute for physical examination, fractography, or lab testing. It is meant to structure a hypothesis and the next steps, not to close a case.
- The knowledge base is curated and covers the common modes and materials, not every alloy or mechanism. Unknowns are reported as unknown.
- The screener is a transparent rule engine on purpose, so every score traces back to a named clue.

## Sources

Failure-mode signatures follow standard failure-analysis references, principally ASM Handbook Volume 11, Failure Analysis and Prevention. Material values are rough engineering ranges for screening, not design data.

---

*Built by Ibtisam Ahmed Khan · June 2026 · [linkedin.com/in/ibtisam-ahmed-khan](https://linkedin.com/in/ibtisam-ahmed-khan) · part of the Agentic Matter series*
