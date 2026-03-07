#!/usr/bin/env python3
"""Experimental Phase 2 entrypoint for browser-driven dashboard card creation."""

from __future__ import annotations

import json
from pathlib import Path

from dashboard_engine import common_parser, load_config, now_stamp, write_json


def main() -> None:
    parser = common_parser("Experimental browser automation hook for Feishu dashboard cards.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--spec-file", required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    config = load_config(Path(args.config).expanduser().resolve())
    spec_path = Path(args.spec_file).expanduser().resolve()
    artifact_dir = Path(args.artifact_dir).expanduser().resolve()
    payload = {
        "status": "experimental",
        "mode": "dry-run" if args.dry_run else "apply",
        "base_name": config.get("base_name"),
        "base_url": config.get("base_url"),
        "spec_file": str(spec_path),
        "message": "Phase 2 browser-driven card creation is reserved but not implemented in the MVP. Use the exported checklist to bind cards manually, or extend this script when UI automation is explicitly required.",
    }
    output_path = artifact_dir / f"dashboard-card-apply-{now_stamp()}.json"
    write_json(output_path, payload)
    if args.apply:
        raise SystemExit(
            "apply-dashboard-cards is experimental and not implemented in the MVP. See the generated JSON for the intended Phase 2 contract."
        )
    payload["output_path"] = str(output_path)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
