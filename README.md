# Feishu Dashboard Automator

`feishu-dashboard-automator` is a local-first skill for Feishu dashboard automation.

Phase 1 is production-ready:

- inspect a Feishu base
- create or update dashboard source views
- export a dashboard card checklist

Phase 2 is reserved:

- browser-driven card creation and view binding

## Current sample

The skill ships with an Odyssey consulting-business sample config:

- [inputs/odyssey-dashboard-config.yaml](inputs/odyssey-dashboard-config.yaml)

## Commands

```bash
python3 scripts/inspect_dashboard_schema.py --config inputs/odyssey-dashboard-config.yaml
```

```bash
python3 scripts/sync_source_views.py --config inputs/odyssey-dashboard-config.yaml --dry-run
```

```bash
python3 scripts/sync_source_views.py --config inputs/odyssey-dashboard-config.yaml --apply
```

```bash
python3 scripts/export_dashboard_spec.py --config inputs/odyssey-dashboard-config.yaml --views-result artifacts/feishu-dashboard-automator/dashboard-source-views-apply-*.json
```

```bash
python3 scripts/build_dashboard_mvp.py --config inputs/odyssey-dashboard-config.yaml --apply
```

## Constraints

- Set `FEISHU_APP_ID` and `FEISHU_APP_SECRET` before any OpenAPI call.
- Keep dashboard-specific table and field ids in config, not inside the engine.
- Do not commit secrets, browser state, or generated artifacts.
