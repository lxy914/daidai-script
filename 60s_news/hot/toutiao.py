#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""头条热搜（60s API）

接口：GET /v2/toutiao
文档：https://docs.60s-api.viki.moe/254038833e0

用法
    python3 60s_news/hot/toutiao.py
    python3 60s_news/hot/toutiao.py --max-items 5     # 只看前 5 条
    python3 60s_news/hot/toutiao.py --no-desc        # 不带摘要
    python3 60s_news/hot/toutiao.py --dry-run        # 只打印，不发通知

约定
    正常信息走 stdout，错误走 stderr；拉不到数据时退出码为 1，榜单为空时退出码 0 且不推送。
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hot_common import run  # noqa: E402

if __name__ == "__main__":
    sys.exit(run(path="/v2/toutiao", board="头条热搜", cache_key="hot_toutiao"))
