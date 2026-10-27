#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""每天 60 秒读懂世界（60s API）

接口：GET /v2/60s
文档：https://docs.60s-api.viki.moe/254026209e0

用法
    python3 60s_news/daily_60s.py                  # 抓取并推送通知
    python3 60s_news/daily_60s.py --dry-run        # 只打印，不发通知
    python3 60s_news/daily_60s.py --max-items 10   # 只显示前 10 条（0 表示全部）
    python3 60s_news/daily_60s.py --no-tip         # 不带末尾的每日寄语

约定
    正常信息走 stdout，错误走 stderr；拉不到数据时退出码为 1。
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sixty_api import get, notify  # noqa: E402


def build_message(data: dict, max_items: int, with_tip: bool, with_link: bool = False) -> tuple[str, str]:
    date = data.get("date") or datetime.now().strftime("%Y-%m-%d")
    title = f"每天 60 秒读懂世界 · {date}"

    news = [str(n).strip() for n in (data.get("news") or []) if str(n).strip()]
    lines = [" ".join(x for x in (date, data.get("day_of_week") or "", data.get("lunar_date") or "") if x), ""]

    if not news:
        lines.append("今日内容暂未更新。")
    else:
        shown = news if max_items <= 0 else news[:max_items]
        for idx, item in enumerate(shown, 1):
            lines.append(f"{idx}. {item}")
        if len(shown) < len(news):
            lines.append(f"\n（共 {len(news)} 条，已省略 {len(news) - len(shown)} 条）")

    if with_tip and (data.get("tip") or "").strip():
        lines.append(f"\n> {data['tip'].strip()}")

    meta = []
    if data.get("updated"):
        meta.append(f"更新 {data['updated']}")
    if with_link and data.get("link"):
        meta.append(f"[原文]({data['link']})")
    if meta:
        lines.append("\n" + " · ".join(meta))
    return title, "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="每天 60 秒读懂世界")
    parser.add_argument("--max-items", type=int, default=20, help="最多显示条数，0 表示不限制")
    parser.add_argument("--no-tip", action="store_true", help="不带每日寄语")
    parser.add_argument("--links", action="store_true", help="末尾带上原文链接（默认不带）")
    parser.add_argument("--dry-run", action="store_true", help="只打印，不发通知")
    args = parser.parse_args()

    started = time.monotonic()
    print(f"=== 60 秒读懂世界 {datetime.now():%Y-%m-%d %H:%M:%S} ===")

    try:
        data = get("/v2/60s", cache_key="daily_60s")
    except Exception as exc:  # noqa: BLE001
        print(f"数据获取失败：{exc}", file=sys.stderr)
        return 1

    title, body = build_message(data, args.max_items, not args.no_tip, args.links)
    print("-" * 60)
    print(body)
    print("-" * 60)

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


if __name__ == "__main__":
    sys.exit(main())
