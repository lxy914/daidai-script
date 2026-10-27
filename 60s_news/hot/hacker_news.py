#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Hacker News 热帖（60s API）

接口：GET /v2/hacker-news/top
文档：https://docs.60s-api.viki.moe/343622824e0

用法
    python3 60s_news/hot/hacker_news.py
    python3 60s_news/hot/hacker_news.py --max-items 5     # 只看前 5 条
    python3 60s_news/hot/hacker_news.py --no-desc        # 不带摘要
    python3 60s_news/hot/hacker_news.py --dry-run        # 只打印，不发通知

约定
    正常信息走 stdout，错误走 stderr；拉不到数据时退出码为 1，榜单为空时退出码 0 且不推送。
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hot_common import run  # noqa: E402

if __name__ == "__main__":
    sys.exit(run(path="/v2/hacker-news/top", board="Hacker News 热帖", cache_key="hot_hn"))
