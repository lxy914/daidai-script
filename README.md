# daidai-script

呆呆面板（Dumb-Panel）定时任务脚本合集，基于 [60s API](https://docs.60s-api.viki.moe/) 做资讯与热搜推送。

每个接口一个脚本、每个脚本一个面板任务，方便单独开关、单独调时间。

## 目录结构

```
60s_news/
├── sixty_api.py        公共请求模块：多实例回退 + 成功实例缓存 12h + notify()
├── daily_60s.py        每天 60 秒读懂世界      GET /v2/60s
├── ai_news.py          AI 资讯快报            GET /v2/ai-news
└── hot/
    ├── hot_common.py   榜单公共渲染（热度归一化、摘要裁剪）
    ├── weibo.py        微博热搜               GET /v2/weibo
    ├── douyin.py       抖音热搜               GET /v2/douyin
    ├── zhihu.py        知乎热榜               GET /v2/zhihu
    ├── bilibili.py     哔哩哔哩热搜           GET /v2/bili
    ├── baidu.py        百度热搜               GET /v2/baidu/hot
    ├── toutiao.py      头条热搜               GET /v2/toutiao
    ├── rednote.py      小红书热点             GET /v2/rednote
    ├── it_news.py      IT之家热门榜           GET /v2/it-news/rank
    └── hacker_news.py  Hacker News 热帖       GET /v2/hacker-news/top
```

## 面板任务

| 脚本 | 建议 Cron | 说明 |
| --- | --- | --- |
| `60s_news/daily_60s.py` | `30 7 * * *` | 每天 60 秒读懂世界 |
| `60s_news/ai_news.py` | `35 7 * * *` | AI 资讯快报（默认前一天） |
| `60s_news/hot/weibo.py` | `0 8 * * *` | 微博热搜 |
| `60s_news/hot/douyin.py` | `5 8 * * *` | 抖音热搜 |
| `60s_news/hot/zhihu.py` | `10 8 * * *` | 知乎热榜 |
| `60s_news/hot/bilibili.py` | `15 8 * * *` | 哔哩哔哩热搜 |
| `60s_news/hot/baidu.py` | `20 8 * * *` | 百度热搜 |
| `60s_news/hot/toutiao.py` | `25 8 * * *` | 头条热搜 |
| `60s_news/hot/rednote.py` | `30 8 * * *` | 小红书热点 |
| `60s_news/hot/it_news.py` | `35 8 * * *` | IT之家热门榜 |
| `60s_news/hot/hacker_news.py` | `40 8 * * *` | Hacker News 热帖 |

时间错开 5 分钟，避免同一时刻并发打到上游被限流。

## 用法

```bash
# 正式推送（调用面板 notify.py）
python3 60s_news/daily_60s.py

# 只打印，不发通知
python3 60s_news/hot/weibo.py --dry-run
```

通用参数：

| 参数 | 说明 |
| --- | --- |
| `--dry-run` | 只打印到 stdout，不发通知 |
| `--max-items N` | 最多显示 N 条，`0` 表示全部（热搜默认 10） |
| `--links` | 标题/末尾带上原文链接（默认纯文本，不带链接） |

分脚本参数：

- `daily_60s.py`：`--no-tip` 不带每日寄语
- `ai_news.py`：`--date YYYY-MM-DD` 指定日期、`--no-detail` 只发标题、`--skip-empty` 当天无资讯不推送
- 热搜类：`--no-desc` 不显示摘要

## 环境变量

| 变量 | 说明 |
| --- | --- |
| `SIXTY_API_BASES` | 逗号分隔的 60s API 实例地址，优先尝试（默认内置主域名 + 公共实例列表） |
| `SIXTY_TIMEOUT` | 单次请求超时秒数，默认 8 |

主域名 `60s.viki.moe` 部分地区无法访问，脚本会自动回退到文档里的公共实例，并把成功实例缓存 12 小时（`.cache_*.json`）。

## 约定

- 正常信息走 stdout，错误走 stderr，退出码决定任务成败
- 拉不到数据 → 退出码 1（触发面板失败通知）
- 榜单为空 → 退出码 0，跳过推送
- 通知通过面板注入的 `notify.py` 发送，正文为 markdown

## 数据来源

[60s API](https://docs.60s-api.viki.moe/)（开源、免费）。
