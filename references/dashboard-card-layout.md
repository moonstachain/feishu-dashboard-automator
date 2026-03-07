# Dashboard Card Layout

Use the same layout pattern for every dashboard group:

1. First row: overview cards
   - aggregate charts
   - stage / structure / trend cards
2. Second row: diagnosis cards
   - bias, anomaly, weak point, mismatch
3. Third row: action cards
   - detail cards that jump into a source view

Rules:

- Every detail card must link to a source view, not the raw table root.
- Avoid putting long text or attachment payloads into a chart dimension.
- Keep one card focused on one management question.
- Prefer stable source views over ad-hoc filters inside the dashboard UI.

For the current Odyssey sample:

- `交付运营看板`
  - Row 1: `交付阶段分布` / `各期次人数` / `交付类型结构`
  - Row 2-3: `待复训名单` / `高私董概率客户` / `已邀请复训客户` / `已成交未入交付异常`
- `目标预算看板`
  - Row 1: `月目标 vs 实际` / `服务线目标达成` / `周节奏完成情况`
  - Row 2-3: `日节奏趋势` / `节奏偏差大项` / `ARPU观察` / `本月订单金额`
- `流量转化看板`
  - Row 1: `总加私趋势` / `私域流水趋势` / `平台内容播放表现`
  - Row 2-3: `分账号加私结构` / `高流水日` / `高互动内容` / `高播放内容` / `订单来源结构`
