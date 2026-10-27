#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""60s API 公共请求模块（供 60s_news/ 下的各个脚本复用）

- 多实例回退：主域名 60s.viki.moe 部分地区被墙，失败后按公共实例列表继续试
- 成功实例缓存 12 小时，下次优先使用，避免每次都从头超时
- 统一返回 data 字段，调用方只关心业务

环境变量
    SIXTY_API_BASES  逗号分隔的实例地址，优先尝试（默认用内置公共实例列表）
    SIXTY_TIMEOUT    单次请求超时秒数，默认 8
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

USER_AGENT = "Mozilla/5.0 (compatible; daidai-panel/60s-api)"

# 主域名 + 文档里列出的公共实例，按顺序回退
DEFAULT_BASES = (
    "https://60s.viki.moe",
    "https://60s.crystelf.top",
    "https://api.elysiayanyu.top",
    "https://60s.7se.cn",
    "https://60s.okbaike.com",
    "https://60s.zellon.top",
)

TIMEOUT = float(os.getenv("SIXTY_TIMEOUT") or 8)
CACHE_TTL = 12 * 3600
_DIR = os.path.dirname(os.path.abspath(__file__))


def bases() -> list[str]:
    raw = os.getenv("SIXTY_API_BASES", "").strip()
    if raw:
        items = [u.strip().rstrip("/") for u in raw.replace(";", ",").split(",") if u.strip()]
        if items:
            return items
    return list(DEFAULT_BASES)


def _cache_path(name: str) -> str:
    safe = "".join(ch if ch.isalnum() else "_" for ch in name)
    return os.path.join(_DIR, f".cache_{safe}.json")


def _load_cached_base(name: str) -> str:
    try:
        with open(_cache_path(name), encoding="utf-8") as fh:
            payload = json.load(fh)
        if time.time() - float(payload.get("ts", 0)) < CACHE_TTL:
            return str(payload.get("base") or "")
    except Exception:  # noqa: BLE001 缓存损坏无所谓
        pass
    return ""


def _save_cached_base(name: str, base: str) -> None:
    try:
        with open(_cache_path(name), "w", encoding="utf-8") as fh:
            json.dump({"base": base, "ts": time.time()}, fh)
    except Exception:  # noqa: BLE001 写不了不影响主流程
        pass


def get(path: str, params: dict | None = None, cache_key: str = ""):
    """请求 60s API，返回 data 字段（可能是 dict 也可能直接是 list）；全部实例失败时抛 RuntimeError。"""
    clean = {k: v for k, v in (params or {}).items() if v not in (None, "")}
    query = ("?" + urllib.parse.urlencode(clean)) if clean else ""
    key = cache_key or path.strip("/").replace("/", "_")

    order = bases()
    cached = _load_cached_base(key)
    if cached:
        order = [cached] + [b for b in order if b != cached]

    errors: list[str] = []
    for base in order:
        url = f"{base}{path}{query}"
        started = time.monotonic()
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                payload = json.loads(resp.read().decode("utf-8", "replace"))
            if isinstance(payload, dict) and payload.get("code", 200) != 200:
                raise ValueError(f"code={payload.get('code')} message={payload.get('message')}")
            data = payload.get("data") if isinstance(payload, dict) else payload
            if not isinstance(data, (dict, list)):
                raise ValueError("返回结构异常：缺少 data 字段")
            print(f"  ✓ {url} ({int((time.monotonic() - started) * 1000)} ms)")
            _save_cached_base(key, base)
            return data
        except (urllib.error.URLError, urllib.error.HTTPError, ValueError, OSError, json.JSONDecodeError) as exc:
            errors.append(f"{url} -> {type(exc).__name__}: {exc}")
            print(f"  ✗ {url} 失败：{type(exc).__name__}: {exc}", file=sys.stderr)
    raise RuntimeError(f"{path} 全部实例请求失败：\n  " + "\n  ".join(errors))


def notify(title: str, content: str, content_type: str = "markdown") -> None:
    """调用面板通知组件（notify.py 在脚本根目录）。"""
    scripts_dir = os.environ.get("DAIDAI_SCRIPTS_DIR")
    if scripts_dir and scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    from notify import send  # noqa: PLC0415

    send(title, content, content_type=content_type)
