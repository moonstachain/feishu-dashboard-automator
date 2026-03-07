#!/usr/bin/env python3
"""Shared engine for Feishu dashboard automation MVP."""

from __future__ import annotations

import argparse
import json
import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from urllib import error, parse, request

import yaml

try:
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
    from playwright.sync_api import sync_playwright
except Exception:  # pragma: no cover - optional dependency for link probing
    PlaywrightTimeoutError = RuntimeError
    sync_playwright = None


CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
LOGIN_HINTS = ("accounts.feishu.cn", "passport.feishu.cn", "login")
FEISHU_OPENAPI_BASE = "https://open.feishu.cn"
SKILL_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_STATE_DIR = SKILL_ROOT / "state" / "browser-profile"
DEFAULT_ARTIFACT_DIR = Path.cwd() / "artifacts" / "feishu-dashboard-automator"


def now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_markdown(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def looks_like_login(url: str) -> bool:
    lowered = (url or "").lower()
    return any(token in lowered for token in LOGIN_HINTS)


def parse_link_params(link: str) -> dict[str, Optional[str]]:
    parsed = parse.urlparse(link)
    params = parse.parse_qs(parsed.query)
    path_parts = [part for part in parsed.path.split("/") if part]
    obj_token = None
    if "wiki" in path_parts:
        idx = path_parts.index("wiki")
        if idx + 1 < len(path_parts):
            obj_token = path_parts[idx + 1]
    elif "base" in path_parts:
        idx = path_parts.index("base")
        if idx + 1 < len(path_parts):
            obj_token = path_parts[idx + 1]
    return {
        "obj_token": obj_token,
        "table_id": params.get("table", [None])[0],
        "view_id": params.get("view", [None])[0],
    }


def json_request(url: str, method: str, payload: Optional[dict[str, Any]], headers: dict[str, str]) -> dict[str, Any]:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json; charset=utf-8")
    req.add_header("Accept", "application/json")
    for key, value in headers.items():
        req.add_header(key, value)
    try:
        with request.urlopen(req, timeout=30) as response:
            raw = response.read().decode("utf-8")
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {url} failed: {exc.code} {detail}") from exc
    return json.loads(raw) if raw else {}


def require_openapi_success(data: dict[str, Any], context: str) -> dict[str, Any]:
    if data.get("code", 0) not in (0, None):
        raise RuntimeError(f"{context} failed: {json.dumps(data, ensure_ascii=False)}")
    return data.get("data") or {}


def fetch_tenant_access_token(app_id: str, app_secret: str) -> str:
    payload = {"app_id": app_id, "app_secret": app_secret}
    data = json_request(
        f"{FEISHU_OPENAPI_BASE}/open-apis/auth/v3/tenant_access_token/internal",
        "POST",
        payload,
        {},
    )
    token = data.get("tenant_access_token")
    if not token:
        raise RuntimeError(f"Failed to obtain tenant_access_token: {json.dumps(data, ensure_ascii=False)}")
    return token


def openapi_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def paged_get(url: str, headers: dict[str, str], *, item_key: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    page_token: Optional[str] = None
    while True:
        parsed = parse.urlparse(url)
        params = parse.parse_qs(parsed.query)
        if page_token:
            params["page_token"] = [page_token]
        params.setdefault("page_size", ["500"])
        encoded = parse.urlencode({key: values[0] for key, values in params.items()})
        page_url = parse.urlunparse(parsed._replace(query=encoded))
        data = require_openapi_success(json_request(page_url, "GET", None, headers), f"GET {page_url}")
        items.extend(data.get(item_key) or [])
        if not data.get("has_more"):
            break
        page_token = data.get("page_token")
        if not page_token:
            break
    return items


def list_bitable_tables(app_token: str, headers: dict[str, str]) -> list[dict[str, Any]]:
    return paged_get(
        f"{FEISHU_OPENAPI_BASE}/open-apis/bitable/v1/apps/{app_token}/tables",
        headers,
        item_key="items",
    )


def list_bitable_fields(app_token: str, table_id: str, headers: dict[str, str]) -> list[dict[str, Any]]:
    return paged_get(
        f"{FEISHU_OPENAPI_BASE}/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/fields",
        headers,
        item_key="items",
    )


def list_bitable_views(app_token: str, table_id: str, headers: dict[str, str]) -> list[dict[str, Any]]:
    return paged_get(
        f"{FEISHU_OPENAPI_BASE}/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/views",
        headers,
        item_key="items",
    )


def create_bitable_view(app_token: str, table_id: str, view_name: str, headers: dict[str, str]) -> dict[str, Any]:
    data = json_request(
        f"{FEISHU_OPENAPI_BASE}/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/views",
        "POST",
        {"view_name": view_name, "view_type": "grid"},
        headers,
    )
    return require_openapi_success(data, f"create view {view_name}")


def update_bitable_view(
    app_token: str,
    table_id: str,
    view_id: str,
    *,
    view_name: str,
    conditions: list[dict[str, Any]],
    conjunction: str,
    headers: dict[str, str],
) -> dict[str, Any]:
    payload: dict[str, Any] = {"view_name": view_name}
    if conditions:
        payload["property"] = {"filter_info": {"conditions": conditions, "conjunction": conjunction}}
    data = json_request(
        f"{FEISHU_OPENAPI_BASE}/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/views/{view_id}",
        "PATCH",
        payload,
        headers,
    )
    return require_openapi_success(data, f"update view {view_name}")


def load_config(path: Path) -> dict[str, Any]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("dashboard config must be a mapping")
    return raw


def get_required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} is required")
    return value


def resolve_app_token_from_link(link: str, *, state_dir: Path, timeout_seconds: int = 300) -> dict[str, Any]:
    if sync_playwright is None:
        raise RuntimeError("Playwright is required to resolve app_token from a Feishu link")
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(state_dir),
            executable_path=CHROME_PATH,
            headless=False,
        )
        try:
            page = context.pages[0] if context.pages else context.new_page()
            page.goto(link, wait_until="domcontentloaded", timeout=60000)
            start = time.time()
            while time.time() - start < timeout_seconds:
                try:
                    page.wait_for_load_state("domcontentloaded", timeout=5000)
                except PlaywrightTimeoutError:
                    pass
                if not looks_like_login(page.url):
                    break
                time.sleep(5)
            if looks_like_login(page.url):
                raise RuntimeError("Feishu is still on the login page; complete login and retry")
            params = parse_link_params(page.url)
            runtime = page.evaluate(
                """() => {
                    const currentSpaceWiki = window.current_space_wiki || null;
                    const baseFirstBlockInfo = window.baseFirstBlockInfo || null;
                    return {
                        title: document.title,
                        current_url: window.location.href,
                        obj_token: currentSpaceWiki?.obj_token || null,
                        base_first_block_info: baseFirstBlockInfo,
                    };
                }"""
            )
            app_token = runtime.get("obj_token") or params["obj_token"]
            if not app_token:
                raise RuntimeError("Could not resolve app_token from Feishu page runtime")
            return {
                "app_token": app_token,
                "base_url": runtime.get("current_url") or link,
                "title": runtime.get("title"),
                "table_id": params.get("table_id"),
                "view_id": params.get("view_id"),
            }
        finally:
            context.close()


def inspect_dashboard_schema(config: Optional[dict[str, Any]] = None, *, app_token: Optional[str] = None, link: Optional[str] = None, state_dir: Optional[Path] = None) -> dict[str, Any]:
    if not app_token:
        if config and config.get("app_token"):
            app_token = str(config["app_token"])
        elif link:
            resolved = resolve_app_token_from_link(link, state_dir=state_dir or DEFAULT_STATE_DIR)
            app_token = resolved["app_token"]
        else:
            raise RuntimeError("Provide app_token, config with app_token, or a Feishu link")

    app_id = get_required_env("FEISHU_APP_ID")
    app_secret = get_required_env("FEISHU_APP_SECRET")
    token = fetch_tenant_access_token(app_id, app_secret)
    headers = openapi_headers(token)

    tables_payload = []
    for table in list_bitable_tables(app_token, headers):
        table_id = table["table_id"]
        fields = list_bitable_fields(app_token, table_id, headers)
        views = list_bitable_views(app_token, table_id, headers)
        tables_payload.append(
            {
                "table_id": table_id,
                "table_name": table.get("name"),
                "default_view_id": table.get("default_view_id"),
                "fields": fields,
                "views": views,
            }
        )
    return {
        "base_url": config.get("base_url") if config else link,
        "app_token": app_token,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "tables": tables_payload,
    }


def resolve_macro(value: str) -> str:
    if value == "{{current_month}}":
        return datetime.now().strftime("%Y-%m")
    return value


def resolve_condition(table_config: dict[str, Any], condition: dict[str, Any]) -> dict[str, Any]:
    field_name = condition["field"]
    field_config = table_config["fields"][field_name]
    operator = condition["operator"]
    payload: dict[str, Any] = {
        "field_id": field_config["field_id"],
        "operator": operator,
    }
    if operator in {"isEmpty", "isNotEmpty"}:
        return payload
    values = [resolve_macro(str(item)) for item in condition.get("values", [])]
    field_type = field_config.get("type", "text")
    if field_type == "single_select":
        raw_values = [field_config["options"][item] for item in values]
    elif field_type == "link":
        raw_values = [field_config["linked_records"][item] for item in values]
    else:
        raw_values = values
    payload["value"] = json.dumps(raw_values, ensure_ascii=False)
    return payload


def build_resolved_views(config: dict[str, Any]) -> list[dict[str, Any]]:
    resolved = []
    for view in config["view_specs"]:
        table_config = config["tables"][view["table"]]
        resolved.append(
            {
                "dashboard": view["dashboard"],
                "table_name": view["table"],
                "table_id": table_config["table_id"],
                "view_name": view["view_name"],
                "conjunction": view.get("conjunction", "and"),
                "display_fields": view.get("display_fields", []),
                "sort_notes": view.get("sort_notes", []),
                "conditions": [resolve_condition(table_config, condition) for condition in view.get("conditions", [])],
            }
        )
    return resolved


def sync_source_views(config: dict[str, Any], *, apply_changes: bool) -> dict[str, Any]:
    resolved_views = build_resolved_views(config)
    if not apply_changes:
        return {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "base_url": config["base_url"],
            "app_token": config["app_token"],
            "views": [
                {
                    **item,
                    "action": "planned",
                    "view_id": None,
                    "view_url": f"{config['base_url']}?table={item['table_id']}",
                }
                for item in resolved_views
            ],
        }

    token = fetch_tenant_access_token(get_required_env("FEISHU_APP_ID"), get_required_env("FEISHU_APP_SECRET"))
    headers = openapi_headers(token)
    views_by_table: dict[str, dict[str, dict[str, Any]]] = {}
    result_views = []
    for item in resolved_views:
        table_id = item["table_id"]
        views_by_table.setdefault(
            table_id,
            {row["view_name"]: row for row in list_bitable_views(config["app_token"], table_id, headers)},
        )
        existing = views_by_table[table_id].get(item["view_name"])
        if existing:
            view_id = existing["view_id"]
            action = "updated"
        else:
            created = create_bitable_view(config["app_token"], table_id, item["view_name"], headers)
            created_view = created.get("view") or created
            view_id = created_view["view_id"]
            views_by_table[table_id][item["view_name"]] = created_view
            action = "created"
        update_bitable_view(
            config["app_token"],
            table_id,
            view_id,
            view_name=item["view_name"],
            conditions=item["conditions"],
            conjunction=item["conjunction"],
            headers=headers,
        )
        result_views.append(
            {
                **item,
                "action": action,
                "view_id": view_id,
                "view_url": f"{config['base_url']}?table={table_id}&view={view_id}",
            }
        )
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "base_url": config["base_url"],
        "app_token": config["app_token"],
        "views": result_views,
    }


def render_dashboard_markdown(config: dict[str, Any], views_result: dict[str, Any]) -> str:
    view_lookup = {(item["dashboard"], item["table_name"], item["view_name"]): item for item in views_result["views"]}
    lines = [
        "# Feishu Dashboard Card Checklist",
        "",
        f"- Base: `{config['base_name']}`",
        f"- Base URL: {config['base_url']}",
        "- This checklist binds dashboard cards to source views created or planned by the skill.",
        "",
    ]
    for group in config["dashboard_groups"]:
        group_name = group["name"]
        lines.append(f"## {group_name}")
        lines.append("")
        lines.append("### Source Views")
        lines.append("")
        for item in [row for row in views_result["views"] if row["dashboard"] == group_name]:
            lines.append(f"- `{item['table_name']} / {item['view_name']}`: {item['view_url']}")
            for note in item.get("sort_notes") or []:
                lines.append(f"  - 排序说明：{note}")
        lines.append("")
        lines.append("### Cards")
        lines.append("")
        for card in config["card_specs"][group_name]:
            bound = view_lookup[(group_name, card["table"], card["view"])]
            lines.append(f"- `{card['name']}`")
            lines.append(f"  - 类型：{card['type']}")
            lines.append(f"  - 数据源：`{card['table']} / {card['view']}`")
            lines.append(f"  - 入口：{bound['view_url']}")
            if "dimension" in card:
                lines.append(f"  - 维度：`{card['dimension']}`")
            if "metric" in card:
                metric = card["metric"]
                if isinstance(metric, list):
                    metric = " / ".join(metric)
                lines.append(f"  - 指标：`{metric}`")
            if "series" in card:
                lines.append(f"  - 序列：`{card['series']}`")
            if "fields" in card:
                lines.append(f"  - 展示字段：`{'`、`'.join(card['fields'])}`")
            lines.append(f"  - 作用：{card['purpose']}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def export_dashboard_spec(config: dict[str, Any], views_result: dict[str, Any], *, artifact_dir: Path) -> dict[str, str]:
    stamp = now_stamp()
    artifact_dir.mkdir(parents=True, exist_ok=True)
    json_path = artifact_dir / f"dashboard-view-config-{stamp}.json"
    md_path = artifact_dir / f"dashboard-card-checklist-{stamp}.md"
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "base_url": config["base_url"],
        "base_name": config.get("base_name"),
        "views": views_result["views"],
        "cards": config["card_specs"],
    }
    write_json(json_path, payload)
    write_markdown(md_path, render_dashboard_markdown(config, views_result))
    return {"json_path": str(json_path), "markdown_path": str(md_path)}


def build_dashboard_mvp(config_path: Path, *, apply_changes: bool, artifact_dir: Path) -> dict[str, Any]:
    config = load_config(config_path)
    try:
        schema = inspect_dashboard_schema(config)
    except RuntimeError as exc:
        if apply_changes:
            raise
        schema = {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "base_url": config["base_url"],
            "app_token": config["app_token"],
            "status": "skipped",
            "reason": str(exc),
        }
    schema_path = artifact_dir / f"dashboard-schema-{now_stamp()}.json"
    write_json(schema_path, schema)
    views_result = sync_source_views(config, apply_changes=apply_changes)
    views_path = artifact_dir / f"dashboard-views-{now_stamp()}.json"
    write_json(views_path, views_result)
    export_paths = export_dashboard_spec(config, views_result, artifact_dir=artifact_dir)
    return {
        "schema_path": str(schema_path),
        "views_path": str(views_path),
        **export_paths,
    }


def common_parser(description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--artifact-dir", default=str(DEFAULT_ARTIFACT_DIR))
    return parser
