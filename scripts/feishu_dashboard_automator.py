#!/usr/bin/env python3
"""Top-level helper that describes available Feishu dashboard automation commands."""

from __future__ import annotations

import json


def main() -> None:
    payload = {
        "skill": "feishu-dashboard-automator",
        "phase_1": [
            "inspect_dashboard_schema.py",
            "sync_source_views.py",
            "export_dashboard_spec.py",
            "build_dashboard_mvp.py",
        ],
        "phase_2": ["apply_dashboard_cards.py (experimental)"],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
