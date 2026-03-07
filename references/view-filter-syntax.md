# View Filter Syntax

`feishu-dashboard-automator` resolves high-level filter conditions from config into Feishu OpenAPI view filters.

Supported condition shapes:

- Text fields
  - `operator: is`
  - `operator: isNot`
- Single select fields
  - `operator: is`
  - `values` use option labels from the config, not option ids
- Link fields
  - `operator: is`
  - `operator: isEmpty`
  - `operator: isNotEmpty`
  - `values` use linked record labels from the config, not record ids
- Date fields
  - `operator: isEmpty`
  - `operator: isNotEmpty`
- Number fields
  - `operator: isNot`
  - use `values: ['0']` to represent a non-zero filter

Macros:

- `{{current_month}}`
  - resolves to the current month in `YYYY-MM` format

Conjunction:

- `and` is the default
- `or` is supported per view spec

Notes:

- Sort order is not fully automated in the MVP. Keep sort requirements in `sort_notes`.
- If a target field is renamed in Feishu, update the config mapping first; do not patch the engine for a business-specific rename.
