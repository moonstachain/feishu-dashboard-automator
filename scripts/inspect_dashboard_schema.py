#!/usr/bin/env python3
"""Inspect Feishu dashboard-relevant schema from app_token or link."""

from __future__ import annotations

import json
from pathlib import Path

from dashboard_engine import DEFAULT_ARTIFACT_DIR, DEFAULT_STATE_DIR, common_parser, inspect_dashboard_schema, load_config, now_stamp, write_json


def main() -> None:
    parser = common_parser("Inspect a Feishu base and export table/field/view schema.")
    parser.add_argument("--config")
    parser.add_argument("--app-token")
    parser.add_argument("--link")
    parser.add_argument("--state-dir", default=str(DEFAULT_STATE_DIR))
    args = parser.parse_args()

    config = load_config(Path(args.config).expanduser().resolve()) if args.config else None
    artifact_dir = Path(args.artifact_dir).expanduser().resolve() if args.artifact_dir else DEFAULT_ARTIFACT_DIR
    payload = inspect_dashboard_schema(
        config,
        app_token=args.app_token,
        link=args.link,
        state_dir=Path(args.state_dir).expanduser().resolve(),
    )
    output_path = artifact_dir / f"dashboard-schema-{now_stamp()}.json"
    write_json(output_path, payload)
    payload["output_path"] = str(output_path)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
