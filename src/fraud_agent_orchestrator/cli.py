"""CLI entrypoint for running fraud orchestrator."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from fraud_agent_orchestrator.workflows import FraudOrchestrator


def _load_alerts(input_path: Path) -> list[dict[str, Any]]:
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and "alerts" in payload and isinstance(payload["alerts"], list):
        return payload["alerts"]
    raise ValueError("Input JSON must be a list of alerts or {'alerts': [...]} object.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="fraud-agent-orchestrator")
    sub = parser.add_subparsers(dest="command", required=True)
    run_parser = sub.add_parser("run", help="Run triage on a JSON file.")
    run_parser.add_argument("--input", required=True, type=Path, help="Path to input JSON.")
    run_parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "run":
        alerts = _load_alerts(args.input)
        orchestrator = FraudOrchestrator()
        output = orchestrator.run_batch(alerts)
        if args.pretty:
            print(json.dumps(output, indent=2))
        else:
            print(json.dumps(output))


if __name__ == "__main__":
    main()
