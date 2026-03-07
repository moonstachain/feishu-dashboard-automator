#!/usr/bin/env python3
"""Export dashboard card checklist and view config artifacts."""

from __future__ import annotations

import json
from pathlib import Path

from dashboard_engine import common_parser, export_dashboard_spec, load_config


def main() -> None:
    parser = common_parser("Export Feishu dashboard card checklist from config and view results.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--views-result", required=True)
    args = parser.parse_args()

    config = load_config(Path(args.config).expanduser().resolve())
    views_result = json.loads(Path(args.views_result).expanduser().resolve().read_text(encoding="utf-8"))
    artifact_dir = Path(args.artifact_dir).expanduser().resolve()
    payload = export_dashboard_spec(config, views_result, artifact_dir=artifact_dir)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
