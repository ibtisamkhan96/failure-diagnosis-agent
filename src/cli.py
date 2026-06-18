"""Command-line entry point for the failure-diagnosis agent.

Examples:
  python -m src.cli "A structural steel bolt in a bridge snapped in winter with a flat, bright
                     fracture and no bending. It happened suddenly in cold weather."
  python -m src.cli --demo
  python -m src.cli --screen '{"loading":"cyclic","fracture_surface":"beach_marks","onset":"progressive"}'

--demo and --screen run the deterministic screener only, with NO API key required. They are the
offline way to see the failure-mode ranking work. The full agent (reasoning, fishbone, report)
needs ANTHROPIC_API_KEY set.
"""

import argparse
import json
import sys

from .screen import format_screen
from .agent import run_agent, DEFAULT_MODEL

DEMO_CASE = {
    "material_class": "bcc_steel",
    "temperature": "low",
    "loading": "impact",
    "fracture_surface": "flat_bright",
    "deformation": "none",
    "onset": "sudden",
}


def main(argv=None):
    ap = argparse.ArgumentParser(description="Agentic failure-diagnosis assistant for materials and mechanical failures.")
    ap.add_argument("case", nargs="?", help="A free-text description of the failure")
    ap.add_argument("--screen", metavar="JSON", help="Run the rule-based screener on a JSON evidence object (no key needed)")
    ap.add_argument("--demo", action="store_true", help="Run the screener on a built-in cold brittle-fracture case (no key needed)")
    ap.add_argument("--model", default=None, help=f"Override model (default {DEFAULT_MODEL})")
    args = ap.parse_args(argv)

    if args.demo:
        print("Demo case (a cold, BCC steel, impact, flat-bright, no-deformation, sudden failure):\n")
        print("Evidence: " + ", ".join(f"{k}={v}" for k, v in DEMO_CASE.items()) + "\n")
        print(format_screen(DEMO_CASE))
        return

    if args.screen:
        try:
            evidence = json.loads(args.screen)
        except json.JSONDecodeError as e:
            print(f"Could not parse the JSON evidence: {e}")
            return
        print(format_screen(evidence))
        return

    if not args.case:
        ap.error("provide a case description, or use --demo / --screen for the no-key screener")

    print(f"Case: {args.case}\nModel: {args.model or DEFAULT_MODEL}\n")
    report, _ = run_agent(args.case, model=args.model)
    print("\n" + "=" * 70 + "\nFAILURE DIAGNOSIS\n" + "=" * 70 + "\n")
    print(report)


if __name__ == "__main__":
    main(sys.argv[1:])
