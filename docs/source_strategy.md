# v2 信息源策略

## 第一版保留和暂停

### 保留：主新闻源

这些来源进入公开早报候选池：

| source_id | 名称 | 获取方式 | 定位 |
| --- | --- | --- | --- |
| `openclaw_tavily` | OpenClaw/Tavily 搜索 | 搜索计划 + Tavily 结果回填 | 补全球新闻、产品发布、商业化和前沿进展 |
| `github_high_stars` | GitHub 高星项目 | GitHub Search API | 发现近期高星开源项目，stars/forks 只作为元数据 |
| `hackernews_top` | Hacker News 热门故事 | HN Firebase API | 发现开发者社区正在讨论的技术线索 |
| `cn_media_search` | 中文媒体搜索聚合 | baidu-search skill 定向站内搜索 | 只覆盖机器之心、新智元、量子位三家中文 AI 媒体 |

### 保留：背景源

这些来源可以进候选池，但默认不能进头条：

| source_id | 名称 | 获取方式 | 定位 |
| --- | --- | --- | --- |
| `sec_press_releases` | SEC 新闻稿 | RSS | 宏观监管背景 |
| `fed_press_all` | 美联储新闻稿 | RSS | 宏观环境背景 |
| `fed_press_monetary` | 美联储货币政策 | RSS | 宏观环境背景 |

### 暂停

| source_id | 名称 | 原因 |
| --- | --- | --- |
| `github_security_advisories` | GitHub Advisory | 第一版先不用。安全公告容易把 AI 早报带成漏洞简报，且旧链路里安全公告摘要经常污染页面。后续如恢复，建议单独做“安全风险”栏目。 |
| `executive_mailbox` | 邮箱告警 | 私有提醒不适合默认混入公开早报。 |

## 中文媒体接入策略

第一版只采用一种方式：`baidu-search` 定向站内搜索。

原因：

- 三家站点首页结构可能调整，直接抓列表容易不稳定。
- 搜索 query 可以固定在对应域名下，覆盖近期文章入口。
- 搜索结果只作为“发现 URL”的线索，后续仍要进入正文抓取和证据检查。
- 不同时保留“站点列表抓取”和“搜索聚合”，避免同一媒体重复进候选池。

## GitHub / Hacker News 接入策略

第一版沿用旧项目的直接平台采集方式，但把热度数据严格放进 `raw_metadata`。

原因：

- GitHub 高星项目需要 stars、forks、language、topics 等结构化元数据。
- Hacker News 需要 score、comments、author 等社区热度信号。
- 这些字段只能进入 `raw_metadata`，不能进入正式摘要字段。

初始配置：

```yaml
fixed_sources:
  - id: github_high_stars
    source_type: github_high_stars
    endpoint: https://api.github.com/search/repositories
    since_days: 3
    min_stars: 80
  - id: hackernews_top
    source_type: hackernews_top
    endpoint: https://hacker-news.firebaseio.com/v0
```

边界：

- 如果 query 发现的是 HN 评论页，正文阶段要优先追踪原文 URL；HN 只作为社区热度证据。
- HN 如果有外链，`url` 使用外链，`raw_metadata.hn_url` 保留讨论页。
- GitHub stars/forks 不能被写成“新闻正文”，只能作为筛选和排序信号。

## 中文搜索聚合方案

### 查询配置

```python
MEDIA_QUERIES = [
    "机器之心 site:jiqizhixin.com",
    "新智元 site:aiera.com",
    "量子位 site:qbitai.com",
]

SEARCH_TOP_K = 10
NEWS_COUNT = 10
```

含义：

- 每个 query 最多拿 10 条搜索结果。
- 聚合后最多保留 10 条新闻候选。
- `site:` 查询用于控制来源，减少泛搜索噪声。

### baidu-search 调用方式

```python
def search_news(query):
    cmd = [
        "python3", "search.py",
        json.dumps({
            "query": query,
            "search_recency_filter": "day",
            "resource_type_filter": [{"type": "web", "top_k": SEARCH_TOP_K}]
        })
    ]
```

运行位置：

```text
/root/.openclaw/workspace/skills/baidu-search/scripts
```

v2 约定：

- 搜索 recency 先用 `week`，后续可加 `day` 模式做每日早报。
- 搜索结果只作为候选线索，不作为正文证据。
- 搜索返回摘要只能进入 `raw_snippet`，不能进入 `summary_main`。
- 搜索失败要记录到 `runtime/search_report.md`，不能静默吞掉后继续假装覆盖完整。

### 搜索结果字段

`cn_media_search` 统一输出：

```json
{
  "source_id": "cn_media_search",
  "source_name": "中文媒体搜索",
  "source_group": "primary",
  "source_type": "cn_media_search",
  "query": "机器之心 site:jiqizhixin.com",
  "media_name": "机器之心",
  "title": "...",
  "url": "...",
  "raw_snippet": "...",
  "published_at": "",
  "raw_metadata": {
    "search_engine": "baidu-search",
    "rank": 1
  }
}
```

### 聚合流程

```text
MEDIA_QUERIES
  -> baidu-search
  -> 解析搜索结果
  -> 按 query/domain 标记媒体名
  -> URL 去重
  -> 进入 collected_raw.json
  -> 后续正文获取
```

### 注意

搜索聚合能补覆盖，但也更容易带来旧文、转载和标题党。因此它必须后接：

- 发布时间识别。
- 原文正文抓取。
- AI 相关性判断。
- 去重合并。
- 发布前质量闸门。

## 采集层统一字段

每个来源输出统一结构：

```json
{
  "item_id": "...",
  "source_id": "qbitai",
  "source_name": "量子位",
  "source_group": "primary",
  "source_type": "cn_media_search",
  "title": "...",
  "url": "...",
  "published_at": "...",
  "raw_snippet": "...",
  "raw_metadata": {
    "author": "...",
    "tags": ["..."],
    "section": "..."
  },
  "fetched_at": "..."
}
```

## 第一版排序倾向

- 国内 AI 媒体作为主新闻源，但不自动加权到前列。
- 同一事件如果 Tavily、HN、中文媒体都有报道，应合并为一个条目。
- 中文媒体的价值主要是补国内产业、产品和应用落地信号。
- 国际前沿模型、论文、开源项目仍优先用原始来源或可信英文主源。
