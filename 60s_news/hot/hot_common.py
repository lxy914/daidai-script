#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""热搜 / 榜单类脚本的公共抓取与渲染（供 60s_news/hot/ 下各脚本复用）

各平台接口返回结构不完全一致，这里统一做一次归一化：
    title  标题
    hot    热度（hot_value / score / rating 等，数字自动转「万」）
    link   原文链接
    desc   摘要（过短或占位文本会忽略）

单个平台脚本只需要给出 SPEC（接口路径、榜单名、缓存键），
其余拉取、渲染、推送、退出码逻辑都在 run() 里。
"""

from __future__ import annotations

import os
import sys
import time
from datetime import datetime

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))  # 60s_news/
from sixty_api import get, notify  # noqa: E402

HOT_KEYS = ("hot_value_desc", "hot_value", "score_desc", "score", "hot", "rating", "heat")
LINK_KEYS = ("link", "url", "href")
DESC_KEYS = ("desc", "abstract", "summary", "detail")
# 这些摘要没信息量，直接忽略
NOISE = ("", "-", "[2 张图片]", "[1 张图片]", "[3 张图片]")


def humanize(value) -> str:
    """热度数字转可读文本：1098729 -> 109.9万。"""
    if value in (None, ""):
        return ""
    text = str(value).strip()
    try:
        num = float(text.replace(",", ""))
    except ValueError:
        return text  # 已经是 "947.5w"、"1094 万热度" 这类文本
    if num >= 100_000_000:
        return f"{num / 100_000_000:.1f}亿"
    if num >= 10_000:
        return f"{num / 10_000:.1f}万"
    return str(int(num)) if num == int(num) else f"{num:g}"


def pick(item: dict, keys: tuple[str, ...]) -> object:
    for key in keys:
        value = item.get(key)
        if value not in (None, ""):
            return value
    return ""


def normalize(item) -> dict:
    if isinstance(item, str):
        return {"title": item.strip(), "hot": "", "link": "", "desc": ""}

    title = str(pick(item, ("title", "name", "word")) or "").strip()
    desc = str(pick(item, DESC_KEYS) or "").strip()
    if desc in NOISE or desc.startswith("[") and desc.endswith("]"):
        desc = ""
    if len(desc) > 80:
        desc = desc[:80].rstrip() + "…"

    return {
        "title": title,
        "hot": humanize(pick(item, HOT_KEYS)),
        "link": str(pick(item, LINK_KEYS) or "").strip(),
        "desc": desc,
        "answer_cnt": item.get("answer_cnt") if isinstance(item, dict) else None,
    }


def render(board: str, raw_items: list, max_items: int, with_desc: bool, with_link: bool = False) -> tuple[str, str, int]:
    """返回 (通知标题, markdown 正文, 总条数)。"""
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    title = f"{board} · {stamp}"

    items = [normalize(i) for i in raw_items]
    items = [i for i in items if i["title"]]
    total = len(items)
    if not items:
        return title, f"**{board}**\n\n本次没有拿到榜单数据。", 0

    shown = items if max_items <= 0 else items[:max_items]
    lines = [f"**{board} · {stamp}**", ""]
    for idx, item in enumerate(shown, 1):
        head = item["title"]
        if with_link and item["link"]:
            head = f"[{item['title']}]({item['link']})"
        line = f"{idx}. {head}"
        if item["hot"]:
            line += f" `{item['hot']}`"
        if item["answer_cnt"]:
            line += f" · {item['answer_cnt']} 回答"
        lines.append(line)
        if with_desc and item["desc"]:
            lines.append(f"   {item['desc']}")

    if len(shown) < total:
        lines.append(f"\n（共 {total} 条，已省略 {total - len(shown)} 条）")
    return title, "\n".join(lines), total


def run(
    *,
    path: str,
    board: str,
    cache_key: str,
    params: dict | None = None,
    argv: list[str] | None = None,
) -> int:
    """标准流程：解析 --max-items / --no-desc / --dry-run，拉取、渲染、推送。"""
    import argparse

    parser = argparse.ArgumentParser(description=board)
    parser.add_argument("--max-items", type=int, default=10, help="最多显示条数，0 表示全部")
    parser.add_argument("--no-desc", action="store_true", help="不显示摘要")
    parser.add_argument("--links", action="store_true", help="标题带上原文链接（默认纯文本）")
    parser.add_argument("--dry-run", action="store_true", help="只打印，不发通知")
    args = parser.parse_args(argv)

    started = time.monotonic()
    print(f"=== {board} {datetime.now():%Y-%m-%d %H:%M:%S} ===")

    try:
        data = get(path, params, cache_key=cache_key)
    except Exception as exc:  # noqa: BLE001
        print(f"数据获取失败：{exc}", file=sys.stderr)
        return 1

    raw_items = data.get("list") if isinstance(data, dict) else data
    if not isinstance(raw_items, list):
        print(f"返回结构异常：{type(raw_items).__name__}", file=sys.stderr)
        return 1

    title, body, total = render(board, raw_items, args.max_items, not args.no_desc, args.links)
    print("-" * 60)
    print(body)
    print("-" * 60)

    if total == 0:
        print("榜单为空，跳过推送")
        return 0

    if args.dry_run:
        print("dry-run：跳过通知发送")
    else:
        try:
            notify(title, body)
            print(f"✓ 通知已发送：{title}")
        except Exception as exc:  # noqa: BLE001
            print(f"✗ 通知发送失败：{type(exc).__name__}: {exc}", file=sys.stderr)
            return 1

    print(f"结果：成功，耗时 {int((time.monotonic() - started) * 1000)} ms")
    return 0
