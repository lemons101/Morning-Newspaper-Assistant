---
name: morning-newspaper-assistant-skill
description: 当 OpenClaw 需要运行 Morning-Newspaper-Assistant 的稳定 AI 晨报链路，生成 Top10 页面数据，并附带邮箱提醒侧栏时使用。
---

# Morning Newspaper Assistant Skill

当用户希望运行中文 AI 晨报助手链路、生成 `top10_publishable.json`、输出静态页面、启动 8510 固定链接，或者排查邮箱提醒与成稿稳定性时，使用本 Skill。

## 当前稳定目标

这套 Skill 的目标不是“尽量跑出点东西”，而是保证：

1. `runtime/top10_publishable.json` 稳定为 **10 条**
2. `runtime/dashboard.html` 稳定可生成
3. 8510 固定链接稳定指向 **Assistant** 项目，而不是旧 Manager 页面
4. 右侧“今日待办提醒”优先读取真实邮箱结果，而不是占位 JSON
5. 如果 IMAP 连通但收不到新邮件，自动继续走 **POP3 fallback**

## 稳定工作流

### A. 每日稳定主流程

优先使用：

```bash
python3 scripts/run_daily_pipeline.py
```

它会按顺序执行：

1. 采集邮箱提醒
   - `runtime/executive_mailbox.json`
   - `runtime/mail_event_queue.json`
2. 运行候选采集
   - `runtime/collected_raw.json`
3. 运行正文抓取
   - `runtime/content_enriched.json`
4. 准备标题粗筛输入
   - `runtime/title_candidates.json`
   - `runtime/title_shortlist_prompt.txt`
5. 应用标题粗筛结果
   - `runtime/title_shortlist_result.json`
   - `runtime/shortlist.json`
6. 准备正文成稿输入
   - `runtime/draft_input.json`
   - `runtime/draft_prompt.txt`
7. 应用成稿结果
   - `runtime/draft_result.json`
   - `runtime/drafted_items.json`
8. 准备 Top10 精排输入
   - `runtime/top10_ranking_input.json`
   - `runtime/top10_ranking_prompt.txt`
9. 应用 Top10 精排结果
   - `runtime/top10_ranking_result.json`
   - `runtime/top10_publishable.json`
10. 生成页面
   - `runtime/dashboard.html`
11. 运行稳定性检查
   - `scripts/check_runtime_status.py`

### B. 只重建页面

```bash
python3 scripts/run_daily_pipeline.py --rebuild-dashboard-only
```

### C. 8510 固定链接服务

```bash
./scripts/serve_dashboard_8510.sh
```

这个脚本会：
- 停掉旧 `Morning-Newspaper-Manager` 的 8510 静态服务
- 停掉旧 `Assistant` 8510 服务实例
- 启动 `Morning-Newspaper-Assistant/runtime/static_dashboard_server.py`

## 人工或模型回填点

以下 3 个结果文件当前仍可由模型或人工回填：

- `runtime/title_shortlist_result.json`
- `runtime/draft_result.json`
- `runtime/top10_ranking_result.json`

如果缺少这些文件，Skill 不应假装完成，而应明确指出缺的是哪一步。

## 页面与数据规则

- `Top10` 必须完整展示 **10 条**
- `summary`/`summary_main` 不允许是 `[TEST] 标题` 这类占位文本
- Tavily 条目没有发布时间时，页面可以显示 `-`，**不要额外加“待确认”文案**
- Tavily 图标不应退回默认 `•`
  - HN → `📰`
  - GitHub → `🧰`
  - 官方模型/研究页 → `🧠`
  - 商业/融资新闻 → `💼`
  - 其他 Tavily → `🔎`
- 邮箱提醒区如果没有真实提醒，应显示空态；不要保留“邮箱模块已切换为独立区域”这种占位卡片

## 邮箱规则

- 真实邮箱提醒写入：`runtime/executive_mailbox.json`
- 事件队列写入：`runtime/mail_event_queue.json`
- 采集报告写入：`runtime/mailbox_collect_report.json`
- 若 IMAP 成功但 `alerts/events` 都为空，且已开启 `pop3_fallback_enabled`，则必须继续尝试 POP3

## 163 邮箱配置

项目根目录 `.env` 至少需要：

```text
IMAP_USER=你的163邮箱地址
IMAP_PASS=你的163邮箱客户端授权码
```

注意：`IMAP_PASS` 必须使用 163 邮箱后台生成的客户端授权码，不是网页登录密码。

## 页面输出

- 静态页面：`runtime/dashboard.html`
- 固定分享链接：`http://101.47.152.44:8510/dashboard.html`
- Streamlit 看板入口：`dashboard_app.py`

## 回复要求

执行完后，至少汇报：

- 当前链路完成到了哪一步
- `runtime/dashboard.html` 是否已更新
- 8510 是否已指向 Assistant 页面
- 采集总数、候选池数量、成稿数量、Top10 数量、邮箱提醒数量、异常来源数量
- 如果缺少模型回填文件，明确指出缺的是哪一个
