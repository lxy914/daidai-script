#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AI 资讯快报（60s API）

接口：GET /v2/ai-news
文档：https://docs.60s-api.viki.moe/375130803e0
说明：默认取前一天的数据，可传 --date 取历史；不是每天都有重大 AI 资讯，空列表属正常。

用法
    python3 60s_news/ai_news.py                   # 抓取并推送通知
    python3 60s_news/ai_news.py --dry-run         # 只打印，不发通知
    python3 60s_news/ai_news.py --date 2026-01-01 # 指定日期
    python3 60s_news/ai_news.py --max-items 5     # 只显示前 5 条
    python3 60s_news/ai_news.py --no-detail       # 只发标题，不带摘要
    python3 60s_news/ai_news.py --skip-empty      # 当天无资讯时不发送（退出码 0）

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


def build_message(data: dict, max_items: int, with_detail: bool, with_link: bool = False) -> tuple[str, str, int]:
    """返回 (标题, markdown 正文, 资讯条数)。"""
    date = data.get("date") or datetime.now().strftime("%Y-%m-%d")
    title = f"AI 资讯快报 · {date}"
    news = data.get("news") or []
    count = len(news)

    lines = [f"**{date}**", ""]
    if not news:
        lines.append("今日没有重大 AI 资讯。")
        return title, "\n".join(lines), 0

    shown = news if max_items <= 0 else news[:max_items]
    for idx, item in enumerate(shown, 1):
        if isinstance(item, str):
            lines.append(f"{idx}. {item.strip()}")
            continue
        head = (item.get("title") or "").strip() or f"资讯 {idx}"
        source = (item.get("source") or "").strip()
        link = (item.get("link") or "").strip()
        detail = (item.get("detail") or "").strip()

        line = f"{idx}. **{head}**" + (f"（{source}）" if source else "")
        if with_link and link:
            line += f" [原文]({link})"
        lines.append(line)
        if with_detail and detail:
            lines.append(f"   {detail}")

    if len(shown) < count:
        lines.append(f"\n（共 {count} 条，已省略 {count - len(shown)} 条）")
    return title, "\n".join(lines), count


def main() -> int:
    parser = argparse.ArgumentParser(description="AI 资讯快报")
    parser.add_argument("--date", default="", help="日期 YYYY-MM-DD，默认前一天")
    parser.add_argument("--max-items", type=int, default=20, help="最多显示条数，0 表示不限制")
    parser.add_argument("--no-detail", action="store_true", help="不输出摘要，只发标题")
    parser.add_argument("--links", action="store_true", help="标题带上原文链接（默认纯文本）")
    parser.add_argument("--skip-empty", action="store_true", help="当天无资讯时不发送")
    parser.add_argument("--dry-run", action="store_true", help="只打印，不发通知")
    args = parser.parse_args()

    started = time.monotonic()
    print(f"=== AI 资讯快报 {datetime.now():%Y-%m-%d %H:%M:%S} ===")

    try:
        data = get("/v2/ai-news", {"date": args.date}, cache_key="ai_news")
    except Exception as exc:  # noqa: BLE001
        print(f"数据获取失败：{exc}", file=sys.stderr)
        return 1

    title, body, count = build_message(data, args.max_items, not args.no_detail, args.links)
    print("-" * 60)
    print(body)
    print("-" * 60)

    if count == 0 and args.skip_empty:
        print("当天无重大 AI 资讯，按 --skip-empty 跳过发送")
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


if __name__ == "__main__":
    sys.exit(main())
