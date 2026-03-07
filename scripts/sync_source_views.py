#!/usr/bin/env python3
"""Create or update Feishu dashboard source views from config."""

from __future__ import annotations

import json
from pathlib import Path

from dashboard_engine import common_parser, load_config, now_stamp, sync_source_views, write_json


def main() -> None:
    parser = common_parser("Create or update Feishu dashboard source views.")
    parser.add_argument("--config", required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    config = load_config(Path(args.config).expanduser().resolve())
    artifact_dir = Path(args.artifact_dir).expanduser().resolve()
    payload = sync_source_views(config, apply_changes=args.apply)
    suffix = "apply" if args.apply else "preview"
    output_path = artifact_dir / f"dashboard-source-views-{suffix}-{now_stamp()}.json"
    write_json(output_path, payload)
    payload["output_path"] = str(output_path)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
