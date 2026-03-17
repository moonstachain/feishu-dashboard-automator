---
name: feishu-dashboard-automator
description: >
  自动化搭建飞书妙搭仪表盘，根据数据蓝图生成仪表盘配置、区块布局和数据绑定。
  当用户说"搭建仪表盘"、"做一个妙搭页面"、"驾驶舱搭建"、"自动化妙搭"时使用。
  NOT for 直接读写多维表数据（用 feishu-bitable-bridge）。
---

# Feishu Dashboard Automator

Use this skill to automate the stable part of Feishu dashboard delivery:

- inspect a Feishu base
- create or update dashboard source views
- export a reusable dashboard card checklist

This is the Phase 1 MVP of Feishu dashboard automation. It is designed to be reused across multiple business bases, not only the current Odyssey sample.

## When To Use

Use when the user wants to:

- automatically prepare a Feishu dashboard module
- standardize dashboard source views before manual card binding
- convert one validated dashboard workflow into a reusable template
- reuse the same dashboard automation flow on another base

## Entry Commands

```bash
python3 scripts/inspect_dashboard_schema.py --link 'https://h52xu4gwob.feishu.cn/wiki/...'
```

```bash
python3 scripts/sync_source_views.py --config inputs/odyssey-dashboard-config.yaml --dry-run
```

```bash
python3 scripts/sync_source_views.py --config inputs/odyssey-dashboard-config.yaml --apply
```

```bash
python3 scripts/export_dashboard_spec.py --config inputs/odyssey-dashboard-config.yaml --views-result artifacts/views.json
```

```bash
python3 scripts/build_dashboard_mvp.py --config inputs/odyssey-dashboard-config.yaml --apply
```

```bash
python3 scripts/apply_dashboard_cards.py --config inputs/odyssey-dashboard-config.yaml --spec-file artifacts/feishu-dashboard-automator/dashboard-view-config-*.json --dry-run
```

## Constraints

- 首版只保证源视图创建与卡片配置清单导出，不默认自动创建飞书仪表盘卡片。
- 视图配置必须参数化，允许替换 base、table、field 与 option 映射，而不是写死某个业务。
- 对需要浏览器层完成的卡片创建步骤，必须输出明确的可执行清单，不允许隐式失败。
- 不把飞书登录态、密钥、运行产物和调试截图提交到仓库。

## References

- `references/view-filter-syntax.md`
- `references/dashboard-card-layout.md`
- `references/odyssey-dashboard-sample.md`
- `references/odyssey-dashboard-config.example.yaml`

## Phase Policy

- Phase 1: source views + card checklist
- Phase 2: browser-driven card creation and binding
- `apply_dashboard_cards.py` is reserved for Phase 2 and marked experimental in the MVP

## Expected Outputs

- 一个可复用的飞书 dashboard automation skill，本地可直接复用到其他业务 base。
- 一个 dashboard 视图同步结果 JSON，以及一个卡片配置清单 Markdown。
- 一套当前奥德赛经营总览的 dashboard config 样板与参考资料。

## Notes

- Keep this skill self-contained and deterministic.
- Update this file when trigger conditions or outputs change.
