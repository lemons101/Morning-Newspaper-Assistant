# 早报 v2 逐环节重建方案

## 目标

v2 的目标不是推翻旧项目，而是按旧项目的大体架构重新走一遍：

```text
信息源
  -> 采集
  -> 标准化
  -> 去重
  -> 初筛
  -> 正文获取
  -> 证据包
  -> 中文成稿
  -> 主编排序
  -> 发布层
  -> 页面/推送
```

旧项目的问题大多不是某一个函数坏了，而是多个环节都允许“脏内容继续往后流”。v2 要做的是在每个环节设边界、设产物、设质量检查，让问题停在出现的地方。

## 核心原则

1. 每个环节只做一件事。
2. 每个环节都输出一个可审计文件。
3. 旧字段不能默认可信，尤其是摘要字段。
4. 失败要显式标记，不要用英文片段、网页 dump、乱码兜底。
5. 页面层只展示发布层产物，不再临场修文案。

## Stage 0：信息源配置

### 旧问题

- AI 早报主线、宏观背景、邮箱提醒混在同一条候选链路里。
- RSS/财经/监管类内容容易凭“新鲜度”进入 Top10，但和 AI 主线弱相关。
- Tavily 搜索主题有价值，但返回结果质量不稳定。

### v2 修正

把来源分成三类：

- 主新闻源：Tavily/OpenClaw 搜索、GitHub 高星项目、Hacker News 热门故事、中文媒体搜索聚合。
- 背景源：SEC、美联储、宏观监管、云厂商财报等。
- 私有提醒源：邮箱告警，默认不进入公开早报。
- 暂停源：GitHub Advisory。安全公告容易把早报带成漏洞简报，v2 第一版先不接入；后续如果要恢复，应放到单独的“安全风险”栏目，而不是默认进入 Top10 主榜。

### 产物

```text
runtime/source_plan.json
```

### 质量闸门

- 每个 source 必须有 `source_group`：`primary`、`background`、`private`。
- `private` 默认不进入公开早报。
- `background` 不能进入头条，除非和 AI 有明确强关系。
- `paused` 来源不参与采集和排序。

## Stage 1：采集

### 旧问题

- 旧链路里 HN 采集摘要会混入 score/comments/author。
- 旧链路里 GitHub repo 采集只拿元数据，容易把 stars/forks 当内容。
- Tavily 结果只是搜索摘要，不等于原文。
- 中文媒体页面列表可能混入广告、活动、转载、合作稿，需要在采集层标记来源和栏目。

### v2 修正

采集层只负责拿“原始卡片”，不写正式摘要。

每条 item 至少包含：

- `item_id`
- `source_type`
- `source_group`
- `title`
- `url`
- `published_at`
- `raw_snippet`
- `raw_metadata`

禁止在采集层生成 `summary_main`、`why_it_matters`、`key_points`。

中文媒体只保留一种接入方式：`baidu-search` 定向站内搜索。

- 用 `baidu-search` skill 执行定向 query，例如 `机器之心 site:jiqizhixin.com`、`新智元 site:aiera.com`、`量子位 site:qbitai.com`。
- 每个 query 暂定 `top_k=10`，聚合后最多保留 10 条候选。
- 第一版只保留机器之心、新智元、量子位三家；不再同时做网页列表抓取，避免重复。
- 不额外做媒体权重和黑名单；来源边界由 `site:` query 控制，质量判断放到后续正文和初筛环节。
- 搜索摘要只作为 `raw_snippet`，不能直接进入正式早报摘要。

GitHub 和 Hacker News 沿用旧项目的平台采集方式：

- GitHub 高星项目用 GitHub Search API，按创建时间、stars、语言和 topic 查找近期项目。
- Hacker News 用 Firebase API 拉取 topstories，再逐条取 story 信息。
- stars、forks、score、comments、author 只能进入 `raw_metadata`，不能进入正式摘要。

### 产物

```text
runtime/collected_raw.json
```

### 质量闸门

- 没有 URL 的公开条目默认降级。
- HN 的 score/comments/author 只能进 `raw_metadata`。
- stars/forks 只能进 `raw_metadata`。
- 中文媒体的作者、栏目、标签只能进 `raw_metadata`，不能直接进入正式摘要。
- 活动推广、课程广告、商务合作稿默认降级为 `background` 或丢弃。
- 搜索聚合结果必须经过黑名单过滤和正文获取，不能只凭搜索摘要入榜。

## Stage 2：标准化与去重

### 旧问题

- 同一新闻可能从 HN、Tavily、原站重复进入。
- 去重后可能保留了较差来源，比如保留 HN 评论页而不是原文 URL。

### v2 修正

按 URL canonical、标题相似度、域名和主题合并重复项。

重复项合并时保留多来源证据：

- `primary_url`
- `supporting_sources`
- `source_votes`
- `best_source_reason`

### 产物

```text
runtime/normalized_items.json
runtime/dedup_report.md
```

### 质量闸门

- 同一事件只保留一个主条目。
- 如果 HN 指向原文，优先使用原文 URL，HN 作为热度证据。

## Stage 3：初筛

### 旧问题

- 旧系统会把“可成稿性”很差的条目送进 Top10。
- 只靠热度、关键词或元数据，容易把弱相关内容抬上来。

### v2 修正

初筛分两种分数：

- `news_value_score`：新闻价值、时效、来源可信度。
- `publishability_score`：能不能写成干净早报。

低可成稿性条目不直接进入主榜。

### 产物

```text
runtime/triage_candidates.json
runtime/triage_report.md
```

### 质量闸门

- `publishability_score` 低于阈值，只能进候补。
- `background` 来源不能占前 3。
- 非 AI 主线必须有明确 AI 连接点。

## Stage 4：正文获取

### 旧问题

- 当前正文抓取只是 `urlopen` + 正则抽文本，不是浏览器阅读。
- 很容易抓到导航、评论、广告、财经行情、GitHub 页面 chrome。
- 抓取失败后会退回旧 summary，污染后续成稿。

### v2 修正

正文获取层只产出证据，不产出正式摘要。

每条正文都要标记：

- `fetch_status`
- `content_type`
- `extract_method`
- `body_text`
- `body_length`
- `noise_flags`
- `evidence_quality`

### 产物

```text
runtime/content_enriched.json
runtime/fetch_report.md
```

### 质量闸门

- 网页噪声超过阈值，`evidence_quality=poor`。
- 正文不足时，不允许把 `raw_snippet` 冒充全文。
- GitHub Advisory 第一版暂停，不进入正文获取。

## Stage 5：证据包

### 旧问题

- LLM 直接看到混杂字段，容易把旧摘要、正文、网页噪声混在一起。
- `summary_zh`、`summary_main`、`key_points` 被当成事实来源，但它们可能已经污染。

### v2 修正

在成稿前生成干净 evidence packet。

只放这些：

- 标题
- URL
- 来源类型
- 发布时间
- 干净正文摘录
- 结构化事实
- 热度/来源证据
- 明确的不可信字段列表

### 产物

```text
runtime/evidence_packets.json
```

### 质量闸门

- `summary_main` 等旧摘要字段默认不进入 evidence。
- 如果必须引用旧摘要，字段名必须带 `_untrusted`。

## Stage 6：中文成稿

### 旧问题

- 摘要失败时 fallback 会输出英文片段。
- “为什么重要”经常被拿来填“主要内容”。
- key_points 经常塞网页噪声。

### v2 修正

中文成稿只从 evidence packet 生成：

- `title_zh`
- `summary_main`
- `why_it_matters`
- `key_points`
- `confidence`
- `warnings`

### 产物

```text
runtime/drafted_items.json
runtime/draft_quality_report.md
```

### 质量闸门

- `summary_main` 必须是中文。
- 不允许长英文原文片段。
- 不允许页面噪声。
- `why_it_matters` 不能替代 `summary_main`。
- `key_points` 不合格就留空。

## Stage 7：主编排序

### 旧问题

- 旧系统 Top10 有时是规则 fallback 排序，不是真正主编选择。
- 入选顺序没有充分考虑版面结构和主题重复。

### v2 修正

主编排序基于已经成稿的 `drafted_items`，而不是原始候选。

排序考虑：

- AI 主线强度
- 新闻新鲜度
- 来源可信度
- 成稿质量
- 版面多样性
- 是否重复同一事件

### 产物

```text
runtime/editorial_top10.json
runtime/editorial_decisions.md
```

### 质量闸门

- Top10 里不能有明显不适合公开早报的条目。
- 前 3 条必须是主线强、证据足、成稿好的内容。
- 如果候选质量不够，宁可少于 10 条，也不要硬凑。

## Stage 8：发布层

### 旧问题

- 页面层会继续从多个字段 fallback，导致脏字段又出现。
- 手工修好的内容可能被下一轮自动链路覆盖。

### v2 修正

新增正式发布层：

```text
runtime/top10_publishable.json
```

页面和推送只读取这个文件。

发布层字段固定：

- `rank`
- `title`
- `summary`
- `why_it_matters`
- `points`
- `source`
- `url`
- `published_at`
- `confidence`
- `warnings`

### 质量闸门

- 发布层不得引用旧 runtime 的任意 fallback 字段。
- 发布层生成后，页面只负责展示，不负责修内容。

## Stage 9：页面/推送

### 旧问题

- 页面展示逻辑和推送逻辑不一致。
- 今日看点、Top10 主卡片、Markdown 可能走不同摘要字段。

### v2 修正

页面、Markdown、推送统一从 `top10_publishable.json` 渲染。

### 产物

```text
runtime/final_newspaper.md
runtime/dashboard.html
runtime/push_digest.md
```

### 质量闸门

- 三个展示出口内容同源。
- 页面层没有摘要选择逻辑。
- 今日看点必须来自 Top10 前几条的正式 `summary`。

## 重点排查旧问题可能出现的环节

### 页面内容杂乱

可能环节：

- Stage 1：采集层把 metadata 写进 summary。
- Stage 4：正文抽取抓到页面噪声。
- Stage 6：成稿 fallback 把英文片段当摘要。
- Stage 9：页面层继续向脏字段 fallback。

v2 修正：

- metadata 不进正式摘要字段。
- 正文噪声要打 flags。
- 成稿失败就失败，不用脏字段兜底。
- 页面只读发布层。

### 条目跑题

可能环节：

- Stage 0：来源没有分组。
- Stage 3：初筛只看热度或关键词。
- Stage 7：主编排序没有主题约束。

v2 修正：

- `source_group` 分层。
- 增加 `publishability_score` 和 `ai_relevance_score`。
- Top10 前 3 必须强 AI 主线。

### 中文乱码

可能环节：

- 文件编码。
- 终端显示。
- LLM 输出解析。
- 旧 runtime 已污染字段复用。

v2 修正：

- 所有文件统一 UTF-8。
- runtime 增加乱码检测。
- 旧中文摘要字段默认不可信。

### 明明抓到正文却摘要很差

可能环节：

- Stage 5：证据包混入旧摘要。
- Stage 6：LLM 失败后规则 fallback 太宽。
- Stage 8：发布层没有质量闸门。

v2 修正：

- evidence packet 只放可信证据。
- 失败显式标记。
- 发布前统一校验。

## 推荐重建顺序

1. 先定来源分组和采集字段。
2. 再做正文获取和证据包。
3. 然后做中文成稿。
4. 再做 Top10 主编排序。
5. 最后做页面。

不要先做页面。页面漂亮不能解决内容脏的问题。
