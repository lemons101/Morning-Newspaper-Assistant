---
name: morning-newspaper-assistant-skill
description: 当 OpenClaw 需要运行 Morning-Newspaper-Assistant 的中文 AI 早报生产链路，完成标题粗筛与正文成稿协作、生成 Top10 页面数据，并返回可点击的本地看板链接时使用。
---

# Morning Newspaper Assistant Skill

当用户希望运行中文 AI 早报助手链路、生成 `top10_publishable.json`、输出静态页面、启动本地看板，或继续完善早报成稿时，使用本 Skill。

## 工作流程

1. 运行候选采集：
   - `runtime/collected_raw.json`
2. 运行正文抓取：
   - `runtime/content_enriched.json`
3. 准备标题粗筛输入：
   - `runtime/title_candidates.json`
   - `runtime/title_shortlist_prompt.txt`
4. 根据模型返回的 `runtime/title_shortlist_result.json` 应用粗筛结果：
   - `runtime/shortlist.json`
5. 准备正文成稿输入：
   - `runtime/draft_input.json`
   - `runtime/draft_prompt.txt`
6. 根据模型返回的 `runtime/draft_result.json` 应用成稿结果：
   - `runtime/drafted_items.json`
7. 准备 Top10 精排输入：
   - `runtime/top10_ranking_input.json`
   - `runtime/top10_ranking_prompt.txt`
8. 根据模型返回的 `runtime/top10_ranking_result.json` 生成最终发布层：
   - `runtime/top10_publishable.json`
9. 生成静态页面：
   - `runtime/dashboard.html`
10. 如需动态网页，则启动本地 Streamlit 看板：
   - `dashboard_app.py`
   - `run_dashboard.cmd`

## 运行命令

```bash
python Morning-Newspaper-Assistant/skills/morning-newspaper-assistant-skill/scripts/run_morning_report_v2.py --project-root D:\Openclaw\Morning-Newspaper-Assistant
```

## 输入与人工协作点

当前 Skill 会自动完成采集、正文抓取、标题候选准备、页面生成前的脚本串联；但以下三个文件仍可由模型或人工回填：

- `runtime/title_shortlist_result.json`
- `runtime/draft_result.json`
- `runtime/top10_ranking_result.json`

如果这些文件不存在，Skill 会保留对应 prompt 与输入文件，并在结果里明确指出缺的是哪一步。

## 页面输出

- 静态页面：`runtime/dashboard.html`
- 动态页面入口：`run_dashboard.cmd`
- 默认本地地址：`http://127.0.0.1:8502`

## 回复要求

- 必须说明当前链路已经完成到哪一步。
- 必须给出静态页面文件路径：`runtime/dashboard.html`
- 必须给出动态看板地址或说明启动状态。
- 必须说明采集总数、候选池数量、成稿数量、Top10 数量、异常来源数量。
- 如果缺少模型回填文件，应明确指出缺的是哪一个。
