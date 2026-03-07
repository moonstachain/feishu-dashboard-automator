#!/usr/bin/env python3
"""Run the Phase 1 dashboard automation MVP: inspect, sync views, export spec."""

from __future__ import annotations

import json
from pathlib import Path

from dashboard_engine import build_dashboard_mvp, common_parser


def main() -> None:
    parser = common_parser("Build the Feishu dashboard MVP bundle from a config file.")
    parser.add_argument("--config", required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    payload = build_dashboard_mvp(
        Path(args.config).expanduser().resolve(),
        apply_changes=args.apply,
        artifact_dir=Path(args.artifact_dir).expanduser().resolve(),
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
