# v2 早报重写思路

## 1. 我们先解决什么

先不重构旧项目，也不直接修旧页面。v2 先只做一件事：把旧项目已经选出来的 Top10，重新写成一份可以发布的中文早报。

这意味着 v2 暂时不负责：

- 抓 GitHub、HN、RSS、Tavily。
- 做候选池排序。
- 管定时任务和推送。
- 生成复杂 dashboard。

v2 先负责：

- 读取旧项目产物。
- 判断每条材料证据够不够。
- 丢弃乱码、网页噪声和错误摘要。
- 重新写标题、主要内容、为什么重要、要点。
- 输出一份稳定的发布稿。

## 2. 输入优先级

建议按这个顺序读取旧项目材料：

1. `runtime/top10_editorial_ready_base.json`
   - 优点：通常有重抓正文和 `body_text`。
   - 缺点：可能已经混入旧摘要污染。

2. `runtime/triage_candidates_enriched.json`
   - 优点：更接近抓取后的证据层，有 `body_text_clean`。
   - 缺点：包含不止 Top10，需要按 `item_id` 对齐。

3. `runtime/ai_selected_top10.json`
   - 优点：给出最终 Top10 顺序。
   - 缺点：当前这份里有乱码、英文片段和 fallback 摘要，只能当索引，不能当成稿来源。

## 3. 字段可信度

高可信：

- `url`
- `title` / `title_en`
- `source_type`
- `published_at`
- `body_text` / `body_text_clean`，前提是通过噪声检查
- `summary_basis`
- `body_fetch_status`

低可信：

- `summary_zh`
- `summary_main`
- `why_it_matters`
- `key_points`
- `editorial_summary_hint`
- `card_summary`

原因：这些字段可能来自旧 fallback、错误 LLM 输出、乱码链路，不能直接照抄。

## 4. 每条新闻的处理流程

1. 对齐条目
   - 以 `ai_selected_top10.json` 的 `item_id` 和 rank 为准。
   - 从 enriched/base 文件补 `body_text` 和证据字段。

2. 证据检查
   - 正文长度是否足够。
   - 是否包含网页导航、评论区、行情页面、广告、GitHub chrome。
   - 是否出现乱码。
   - 是否与标题主题匹配。

3. 重新成稿
   - `title_zh`：一句中文标题，不写“值得关注”。
   - `summary_main`：2 到 3 句，先讲事实，再讲变化或影响。
   - `why_it_matters`：只讲价值，不重复主要内容。
   - `key_points`：最多 3 条；没有干净要点就留空。

4. 降级处理
   - 证据不足时，不写满。
   - 非 AI 主线条目，标记为边缘信号。
   - 明显不适合 Top10 的条目，可进入 `drop_candidates.md`，但不在第一版自动删除。

## 5. 成稿结构

建议先输出 Markdown：

```text
# 今日 AI 早报

## 今日看点
- 三条全局看点，每条来自 Top10 中最强的内容。

## Top10
### 1. 中文标题
主要内容：...
为什么重要：...
要点：
- ...

## 降级和疑点
- 哪些条目证据不足
- 哪些条目可能不该进 AI 早报
```

## 6. 第一版验收标准

- 页面正文不出现乱码。
- 不出现长英文原文片段。
- 不出现 Hacker News points、author、comments 作为正文。
- 不出现 GitHub Reviewed、Published May、Dependabot alerts 作为摘要。
- ODoH 条目不能写成 AT&T Room 641A。
- Claude for Small Business 不能混入历史监听内容。
- 安全公告必须写清楚受影响对象、漏洞类型、后果和修复动作。
- AWS、云需求这类条目要明确它是 AI 需求带来的云基础设施/收入信号，不要写成泛泛商业新闻。

## 7. 后续代码化方向

等人工重写稿满意后，再做脚本：

```text
load_old_runtime.py
  -> build_evidence_packets.py
  -> rewrite_with_rules_or_llm.py
  -> validate_publishable.py
  -> render_markdown.py
```

代码化时要坚持一个规则：校验失败就停止或降级，不要用旧脏字段兜底。
