# Morning Newspaper Assistant

Morning Newspaper Assistant 是一个面向中文 AI 早报生产的流水线项目。

它把“新闻源采集、正文抓取、标题粗筛、中文成稿、Top10 精排、页面发布、邮箱提醒”拆成一组可检查、可回填、可重跑的模块。项目的重点不是一次性把所有步骤藏进一个黑盒脚本，而是让每天早报生产过程中的中间产物都能被看见、修正和复用。

## 项目定位

这个项目解决的是 AI 早报生产里最容易失控的三件事：

- 候选来源多，但原始网页里常有导航、英文碎片、广告和无关文本。
- 标题粗筛、正文成稿、最终排序都需要模型判断，但模型结果必须有清晰输入输出边界。
- 最终页面应该只读取发布层数据，不能把半成品、fallback 文本或抓取噪音直接展示给读者。

因此，项目采用“数据采集层 -> 内容加工层 -> 编辑回填层 -> 发布展示层”的结构。每一步都会写入 `runtime/`，下一步只消费明确约定的文件。

## 整体架构

```text
config/sources.yaml
        |
        v
scripts/collect_raw.py
        |
        v
runtime/collected_raw.json
        |
        v
scripts/enrich_content.py
        |
        v
runtime/content_enriched.json
        |
        v
scripts/prepare_title_shortlist.py
        |
        +--> runtime/title_candidates.json
        +--> runtime/title_shortlist_prompt.txt
        |
        v
人工或模型填写 runtime/title_shortlist_result.json
        |
        v
scripts/apply_title_shortlist.py
        |
        v
runtime/shortlist.json
        |
        v
scripts/prepare_draft_input.py
        |
        +--> runtime/draft_input.json
        +--> runtime/draft_prompt.txt
        |
        v
人工或模型填写 runtime/draft_result.json
        |
        v
scripts/apply_draft_results.py
        |
        v
runtime/drafted_items.json
        |
        v
scripts/prepare_top10_ranking.py
        |
        +--> runtime/top10_ranking_input.json
        +--> runtime/top10_ranking_prompt.txt
        |
        v
人工或模型填写 runtime/top10_ranking_result.json
        |
        v
scripts/apply_top10_ranking.py
        |
        v
runtime/top10_publishable.json
        |
        v
scripts/build_dashboard.py
        |
        v
runtime/dashboard.html
```

邮箱提醒是一条独立侧链：

```text
163 邮箱 -> scripts/collect_mailbox.py -> runtime/mail_event_queue.json
                                      -> runtime/executive_mailbox.json
                                      -> 页面右侧“今日待办提醒”
```

邮箱提醒不参与 Top10 排序，只给看板补充个人待办、会议、截止日期和重要邮件信号。

## 模块职责

| 模块 | 主要文件 | 职责 |
| --- | --- | --- |
| 配置层 | `config/sources.yaml` | 定义采集窗口、固定来源、Tavily 搜索计划、中文媒体搜索、邮箱配置和关键词规则。 |
| 采集器层 | `src/morning_v2/collectors/` | 从 GitHub、Hacker News、RSS、中文媒体搜索、Tavily 结果中生成统一的 `RawItem`。 |
| 内容抓取层 | `src/morning_v2/content_fetch.py` | 为候选 URL 抓取正文；GitHub 项目优先读 README API，普通网页走 HTML 主体抽取和噪音清理。 |
| 编辑准备层 | `scripts/prepare_*.py` | 把候选整理成适合模型或人工处理的 JSON，并生成对应 prompt。 |
| 编辑应用层 | `scripts/apply_*.py` | 把人工或模型结果合并回原始候选，保证标题、摘要、排序都能追溯到输入文件。 |
| 邮箱提醒层 | `src/morning_v2/mailbox.py`、`scripts/collect_mailbox.py` | 读取 163 邮箱，识别紧急/重要邮件和日期事项，生成看板侧栏数据。 |
| 发布层 | `src/morning_v2/dashboard.py`、`scripts/build_dashboard.py` | 只读取最终发布数据和邮箱提醒数据，生成静态 HTML 看板。 |
| 动态看板 | `dashboard_app.py`、`run_dashboard.cmd` | 用 Streamlit 读取同一套 `runtime/` 数据，提供本地动态页面。 |
| Skill 入口 | `skills/morning-newspaper-assistant-skill/` | 给 OpenClaw/Codex 调用的一键编排入口，会自动停在需要人工或模型回填的步骤。 |

## 目录结构

```text
Morning-Newspaper-Assistant/
├── config/
│   └── sources.yaml                         # 新闻源、搜索主题、邮箱提醒、运行窗口配置
├── docs/
│   ├── source_strategy.md                   # 来源策略与覆盖范围说明
│   ├── rewrite_plan.md                      # README/文档重写计划
│   └── pipeline_rebuild_plan.md             # 早报流水线重构计划
├── references/
│   └── editorial_rules.md                   # 早报编辑规则、筛选口径、成稿风格参考
├── runtime/                                 # 每日运行产物目录，主流程围绕这里读写
│   ├── collected_raw.json                   # 原始候选池，来自 GitHub/HN/RSS/搜索结果
│   ├── collect_report.json                  # 各来源采集状态、数量、异常信息
│   ├── content_enriched.json                # 已抓正文的候选，含 fetch_status/body_text
│   ├── title_candidates.json                # 标题粗筛输入，只保留标题和基础元信息
│   ├── title_shortlist_prompt.txt           # 标题粗筛 prompt
│   ├── title_shortlist_result.json          # 人工/模型回填的标题粗筛结果
│   ├── shortlist.json                       # 粗筛后候选池，重新带回正文和来源信息
│   ├── draft_input.json                     # 中文成稿输入，含正文片段
│   ├── draft_prompt.txt                     # 中文成稿 prompt
│   ├── draft_result.json                    # 人工/模型回填的中文标题和摘要
│   ├── drafted_items.json                   # 已完成中文成稿的候选
│   ├── top10_ranking_input.json             # Top10 精排输入
│   ├── top10_ranking_prompt.txt             # Top10 精排 prompt
│   ├── top10_ranking_result.json            # 人工/模型回填的最终排序
│   ├── top10_publishable.json               # 最终发布层数据，页面只读这个文件
│   ├── executive_mailbox.json               # 页面右侧邮箱提醒卡片
│   ├── mail_event_queue.json                # 邮件中识别出的未来事项队列
│   └── dashboard.html                       # 可直接打开的静态早报页面
├── scripts/
│   ├── collect_mailbox.py                   # 采集 163 邮箱提醒，生成提醒卡片和事项队列
│   ├── collect_raw.py                       # 采集新闻候选，写 collected_raw/collect_report
│   ├── enrich_content.py                    # 对候选 URL 做正文抓取和网页噪音清洗
│   ├── prepare_title_shortlist.py           # 准备标题粗筛输入和 prompt
│   ├── apply_title_shortlist.py             # 应用标题粗筛结果，生成 shortlist
│   ├── prepare_draft_input.py               # 准备中文成稿输入和 prompt
│   ├── apply_draft_results.py               # 应用中文成稿结果，生成 drafted_items
│   ├── prepare_top10_ranking.py             # 准备 Top10 精排输入和 prompt
│   ├── apply_top10_ranking.py               # 应用最终排序，生成 top10_publishable
│   ├── build_dashboard.py                   # 根据发布层数据生成静态 HTML 看板
│   └── run_tavily_plan.py                   # 执行/衔接 Tavily 搜索计划结果
├── skills/
│   └── morning-newspaper-assistant-skill/
│       ├── SKILL.md                         # OpenClaw/Codex 调用说明
│       └── scripts/
│           └── run_morning_report_v2.py     # 一键编排入口，会停在缺少回填文件的步骤
├── src/
│   └── morning_v2/
│       ├── collectors/
│       │   ├── orchestrator.py              # 统一调度各来源采集器、过滤时间窗口、去重
│       │   ├── github.py                    # GitHub Search API 高星项目采集
│       │   ├── hackernews.py                # Hacker News Firebase API 热门故事采集
│       │   ├── rss.py                       # RSS/Atom XML 解析采集
│       │   ├── cn_media.py                  # 中文媒体搜索结果转换为 RawItem
│       │   ├── baidu_search.py              # 调用外部 baidu-search 脚本
│       │   ├── tavily.py                    # 生成 Tavily 搜索计划并读取搜索结果
│       │   └── items.py                     # RawItem 构造与候选去重工具
│       ├── common.py                        # JSON/YAML/.env/HTTP/文本清洗通用函数
│       ├── content_fetch.py                 # 正文抓取、主体抽取、网页噪音过滤
│       ├── dashboard.py                     # 看板 payload 组装与静态 HTML 渲染
│       ├── mailbox.py                       # IMAP/POP3 邮箱提醒采集与事项识别
│       └── models.py                        # RawItem 数据模型和 item_id 生成
├── dashboard_app.py                         # Streamlit 动态看板，读取 runtime 数据
├── run_dashboard.cmd                        # Windows 本地动态看板启动脚本
├── .env.example                             # 本地环境变量示例
├── requirements.txt                         # 主采集链路 Python 依赖
└── README.md
```

## 核心数据产物

| 文件 | 由谁生成 | 内容 |
| --- | --- | --- |
| `runtime/collected_raw.json` | `scripts/collect_raw.py` | 统一格式的原始候选列表。 |
| `runtime/collect_report.json` / `.md` | `scripts/collect_raw.py` | 每个来源的采集状态和数量。 |
| `runtime/content_enriched.json` | `scripts/enrich_content.py` | 补充了正文、抓取状态、抽取方式和正文长度的候选列表。 |
| `runtime/title_candidates.json` | `scripts/prepare_title_shortlist.py` | 只包含标题和基础元信息，用于标题粗筛。 |
| `runtime/title_shortlist_result.json` | 人工或模型 | 标题粗筛结果，通常保留 10 到 15 条。 |
| `runtime/shortlist.json` | `scripts/apply_title_shortlist.py` | 与正文内容重新合并后的候选池。 |
| `runtime/draft_input.json` | `scripts/prepare_draft_input.py` | 给中文成稿使用的标题、来源、正文片段。 |
| `runtime/draft_result.json` | 人工或模型 | 中文标题和中文摘要草稿。 |
| `runtime/drafted_items.json` | `scripts/apply_draft_results.py` | 已完成中文成稿的候选。 |
| `runtime/top10_ranking_input.json` | `scripts/prepare_top10_ranking.py` | 给最终精排使用的候选列表。 |
| `runtime/top10_ranking_result.json` | 人工或模型 | Top10 最终排序结果。 |
| `runtime/top10_publishable.json` | `scripts/apply_top10_ranking.py` | 页面发布层，只包含最终标题、摘要、来源、链接和排序。 |
| `runtime/dashboard.html` | `scripts/build_dashboard.py` | 可直接打开的静态早报页面。 |
| `runtime/executive_mailbox.json` | `scripts/collect_mailbox.py` | 看板右侧展示的今日提醒卡片。 |
| `runtime/mail_event_queue.json` | `scripts/collect_mailbox.py` | 从邮件中识别出的未来会议、截止、提醒事项队列。 |

## 运行方式

安装依赖：

```bash
pip install -r requirements.txt
```

`requirements.txt` 覆盖主采集链路需要的依赖。动态看板使用 Streamlit，如果当前环境没有安装，需要额外执行：

```bash
pip install streamlit
```

查看采集计划，不真正请求网络：

```bash
python scripts/collect_raw.py --dry-run
```

运行完整编排入口：

```bash
python skills/morning-newspaper-assistant-skill/scripts/run_morning_report_v2.py --project-root D:\Openclaw\Morning-Newspaper-Assistant
```

默认情况下，编排入口会跳过 Tavily 的真实搜索执行，只使用固定来源和已有 Tavily 结果文件。如果中间缺少下列任一模型/人工结果文件，它会停在可继续回填的阶段，并在输出 JSON 中列出缺失步骤：

- `runtime/title_shortlist_result.json`
- `runtime/draft_result.json`
- `runtime/top10_ranking_result.json`

单步运行时，可以按流水线顺序执行：

```bash
python scripts/collect_mailbox.py
python scripts/collect_raw.py --skip-tavily
python scripts/enrich_content.py
python scripts/prepare_title_shortlist.py
python scripts/apply_title_shortlist.py
python scripts/prepare_draft_input.py
python scripts/apply_draft_results.py
python scripts/prepare_top10_ranking.py
python scripts/apply_top10_ranking.py
python scripts/build_dashboard.py
```

其中 `apply_*` 步骤依赖对应的人工或模型结果文件。没有结果文件时，先打开 `runtime/*_prompt.txt` 和对应输入 JSON，让模型或人工生成结果，再继续执行。

## 回填文件格式

标题粗筛结果：

```json
{
  "selected_titles": ["原标题 1", "原标题 2"]
}
```

正文成稿结果：

```json
{
  "drafts": [
    {
      "title": "原标题",
      "title_zh": "中文标题",
      "summary_main": "2到3句中文摘要",
      "published_at": "原始发布时间",
      "url": "原始访问链接"
    }
  ]
}
```

Top10 精排结果：

```json
{
  "top10_rank_ids": ["ID3", "ID7"],
  "top10_titles": ["标题1", "标题2"]
}
```

推荐优先使用 `top10_rank_ids`，因为它和 `runtime/top10_ranking_input.json` 里的 `rank_id` 一一对应，比标题匹配更稳定。

## 看板输出

静态页面：

```bash
python scripts/build_dashboard.py
```

生成文件：

```text
runtime/dashboard.html
```

本地动态看板：

```bash
run_dashboard.cmd
```

默认地址：

```text
http://127.0.0.1:8502
```

静态页面和动态看板都读取同一套 `runtime/` 数据。区别是静态页面适合快速查看和分享文件，Streamlit 看板适合本地调试。

## 新闻来源与采集方法

所有新闻来源都在 `config/sources.yaml` 里配置。采集后会统一转换成 `RawItem`，写入 `runtime/collected_raw.json`，再进入正文抓取和编辑链路。

| 来源类型 | 当前配置 | 采集方法 | 进入主链方式 |
| --- | --- | --- | --- |
| GitHub 高星项目 | `fixed_sources.github_high_stars` | 调用 GitHub Search API，按 `created`、`stars`、`language`、`topic` 查询近几天新增的高星项目。 | 直接生成候选，正文抓取时优先通过 GitHub README API 获取项目说明。 |
| Hacker News 热门故事 | `fixed_sources.hackernews_top` | 调用 Hacker News Firebase API，先取 `topstories` ID 列表，再逐条获取 story 详情。 | 直接生成候选，后续再访问原始链接抓正文。 |
| RSS / Atom Feed | `fixed_sources.*.source_type=rss` | 请求 RSS/Atom XML，用 `title`、`link`、`description/summary`、`pubDate/published/updated` 生成候选。 | 直接生成候选，后续再访问原文链接抓正文。 |
| 中文媒体搜索 | `cn_media_search` | 调用外部 `baidu-search` 脚本，按关键词搜索中文网页结果，并记录查询词、搜索排名、识别到的媒体来源。 | 默认关闭；开启后作为主候选来源进入采集池。 |
| OpenClaw Tavily 搜索 | `openclaw_tavily` | 先根据配置写出 `runtime/tavily_search_plan.json`，由 OpenClaw/Tavily skill 执行搜索，再读取 `runtime/tavily_search_results.json`。 | 适合补充 AI 前沿、Agent、商业化、融资产品等主题搜索结果。 |
| 邮箱提醒 | `assistant_mailbox` | 通过 IMAP 读取 163 邮箱，失败时可回退 POP3；用关键词和日期识别会议、截止、紧急事项。 | 不进入新闻 Top10，只进入右侧提醒栏。 |

当前固定来源包括：

- `github_high_stars`：GitHub 高星项目，默认覆盖 Python、TypeScript、Go、Rust，以及 `topic:ai`、`topic:agent`。
- `hackernews_top`：Hacker News 热门故事。
- `sec_press_releases`：SEC 新闻稿 RSS。
- `fed_press_all`：美联储新闻稿 RSS。
- `qbitai_rss`：量子位 RSS。

`runtime.lookback_days` 控制候选时间窗口，默认只保留近 3 天内容。采集结束后，`collect_all()` 会按 URL 和标题做精确去重，并把每个来源的状态写入 `runtime/collect_report.json`。

### 固定 API 来源

GitHub 和 Hacker News 属于结构化 API 来源。

GitHub 采集器会构造类似这样的查询：

```text
created:>=YYYY-MM-DD stars:>=80 archived:false is:public language:Python
```

它会读取仓库名、链接、简介、创建时间、stars、forks、语言、topics 等元信息。若配置了 `GITHUB_TOKEN`，会通过 `Authorization: Bearer ...` 调用 GitHub API；环境变量名由 `fixed_sources[].auth_env` 指定。

Hacker News 采集器会读取 story 标题、原始 URL、发布时间、分数、评论数、作者和 HN 讨论链接。没有外部 URL 的条目会回退到 `news.ycombinator.com/item?id=...`。

### RSS 来源

RSS 采集器使用 Python 标准库解析 XML，不依赖第三方 feed 库。它兼容常见 RSS 和 Atom 字段：

- 标题：`title`
- 链接：`link` 或 Atom `link.href`
- 摘要：`description`、`summary`
- 时间：`pubDate`、`published`、`updated`

RSS 本身只作为候选发现层，真正进入成稿前仍会由 `scripts/enrich_content.py` 访问原文链接抓取正文。

### 搜索型来源

搜索型来源分两种：

- `cn_media_search`：本地调用外部 `baidu-search` 脚本，适合按“AI、大模型、智能体、机器之心、新智元、量子位”等关键词补中文来源。
- `openclaw_tavily`：先生成搜索计划，再由 OpenClaw 调用 Tavily skill 执行搜索，适合按主题和域名白名单补国际来源。

Tavily 配置按主题拆分，目前包括：

- AI 前沿技术
- AI Agent 与开源工具
- AI 商业化与企业采用
- AI 创业融资与产品发布

这类来源不是直接在 `collect_raw.py` 里联网搜索。`collect_raw.py` 负责写计划和读结果，这样可以把外部搜索执行、搜索结果回填、后续早报流水线拆开。

### 正文二次抓取

候选进入 `runtime/collected_raw.json` 后，还会统一经过 `scripts/enrich_content.py` 做正文二次抓取。

正文抓取策略在 `src/morning_v2/content_fetch.py`：

- GitHub 仓库优先调用 `/repos/{owner}/{repo}/readme`，用 README 作为正文材料。
- 普通网页使用 `requests` 获取 HTML，再优先抽取 `article`、`main`、`post-content`、`entry-content`、`markdown-body` 等主体区域。
- 如果主体区域找不到，会尝试使用 meta description，最后才回退到整页文本。
- 清洗时会过滤导航、登录提示、隐私政策、订阅提示、广告、GitHub 页面噪音、政府站点通用页头等常见无关文本。
- 抓取结果会记录 `fetch_status`、`extract_method`、`body_text`、`body_length`、`note`，方便判断某条候选是否真的有可用正文。

这一步的目的不是直接生成摘要，而是给后续标题粗筛和中文成稿提供更干净的证据材料。

## 邮箱提醒配置

如果要启用 163 邮箱提醒，在项目根目录创建 `.env`：

```text
IMAP_USER=你的163邮箱地址
IMAP_PASS=你的163邮箱客户端授权码
```

`IMAP_PASS` 使用 163 邮箱后台生成的客户端授权码，不是网页登录密码。

默认邮箱连接配置已经写在 `config/sources.yaml`：

- IMAP：`imap.163.com:993`
- POP3 fallback：`pop.163.com:995`

临时关闭邮箱提醒：

```yaml
assistant_mailbox:
  enabled: false
```

## 设计原则

- 原始材料和发布成稿分离。
- 模型步骤不静默 fallback 成正式结果。
- 中间产物优先保留，方便检查、重跑和人工修正。
- 页面只读取 `top10_publishable.json` 和 `executive_mailbox.json` 这类发布层数据。
- 宁可少写，也不把脏文本、网页导航、乱码、长英文碎片直接放进早报。
