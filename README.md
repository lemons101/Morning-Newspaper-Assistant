# Morning Newspaper Assistant

这是一个面向中文 AI 早报生产流程的助手项目。

它的目标不是在旧项目里继续打补丁，而是把“从候选采集、正文抓取、标题粗筛、成稿、精排，到页面展示”这一整条链路单独整理成一个更清晰、更稳定的助手。这个项目关注的是把早报做出来、做干净、做成可用页面，而不是维持一个带有实验味道的 `v2` 分支命名。

## 这个助手解决什么问题

之前的早报链路并不缺数据，问题主要出在成稿和展示层：

- 抓到了正文，但摘要可能退回英文片段或网页噪音。
- 模型步骤失败时，容易让规则 fallback 伪装成正式成稿。
- 页面展示时，推荐理由、主要内容、原始网页碎片容易混在一起。
- 候选条目进入 Top10 后，缺少清晰的人工回填边界和中间产物边界。

Morning Newspaper Assistant 的思路是把每一步都拆成可检查、可回填、可重跑的产物，让问题停在它出现的地方，而不是一路流到页面。

## 核心原则

- 原始材料和发布成稿分离。
- 先保留中间产物，再生成最终页面。
- 宁可少写，也不把脏文本、网页导航、乱码、长英文碎片直接放进早报。
- 标题粗筛、正文成稿、Top10 精排都允许人工或模型回填，但必须留下明确输入输出文件。
- 页面只读取最终发布层，不直接拼接中间临时结果。

## 项目目录

```text
Morning-Newspaper-Assistant/
  README.md
  config/
  docs/
  references/
  runtime/
  scripts/
  skills/
  src/
  dashboard_app.py
  run_dashboard.cmd
```

## 当前可用入口

目前已经提供一套可串联执行的助手 skill 入口：

```text
skills/morning-newspaper-assistant-skill/
  SKILL.md
  scripts/run_morning_report_v2.py
```

它会按顺序串联：

1. 候选采集
2. 正文抓取
3. 标题粗筛输入准备
4. 标题粗筛结果应用
5. 正文成稿输入准备
6. 成稿结果应用
7. Top10 精排输入准备
8. 对粗筛后的候选做最终排序，并取前 10 条
9. 静态页面生成

如果中间需要模型或人工回填结果文件，skill 会保留 prompt 与输入文件，并在返回结果里明确指出缺的是哪一步。

其中：

- 标题粗筛不是强行凑满 15 条，而是先保留一小批最值得继续读正文的候选，通常不超过 15 条。
- 正常情况下，标题粗筛应尽量保留 10 到 15 条，给后续成稿和精排留下足够候选。
- Top10 精排不是重新做一轮粗选，而是对粗筛并成稿后的候选做最终排序，然后取前 10 条进入页面。

## 页面查看方式

这个项目目前提供两种页面查看方式：

1. 静态页面：
   - `runtime/dashboard.html`
2. 本地动态看板：
   - `dashboard_app.py`
   - `run_dashboard.cmd`
   - 默认地址：`http://127.0.0.1:8502`
3. 对外固定分享页（8510）：
   - 启动脚本：`scripts/serve_dashboard_8510.sh`
   - 固定只服务 `Morning-Newspaper-Assistant/runtime/dashboard.html`

如果只想快速检查结果，直接打开静态页面即可；如果希望像旧项目一样起一个本地网页服务，就运行 `run_dashboard.cmd`。

## 正式运行入口（Assistant Only）

正式产物现在应只通过 Assistant 项目生成，不再通过 Manager 项目脚本间接产出。

推荐入口：

```bash
bash scripts/run_assistant_only.sh
```

它会调用：

```bash
python scripts/run_daily_pipeline.py
```

约束：
- 正式页面、正式 runtime、8510 分享页都以 `Morning-Newspaper-Assistant` 为唯一来源。
- `Morning-Newspaper-Manager` 仅保留为历史参考或实验链，不应再作为正式页面生成入口。

## 邮箱提醒链路

这个项目现在除了公开早报主链，还带了一条独立的助手侧提醒链路：

`163邮箱 -> mail_event_queue.json -> executive_mailbox.json -> 页面右侧提醒`

它的定位不是参与 Top10 排序，而是帮助你每天顺手看“今天有没有要忙的事”。

### 需要的配置

在项目根目录放一个 `.env` 文件，至少包含：

```text
IMAP_USER=你的163邮箱地址
IMAP_PASS=你的163邮箱客户端授权码
```

也可以直接复制 `.env.example` 再改成自己的值。

注意：`IMAP_PASS` 用的是 163 邮箱后台生成的客户端授权码，不是网页登录密码。

163 邮箱默认连接配置已经写在 `config/sources.yaml` 里：

- `imap.163.com:993`
- `pop.163.com:995`

### 会生成的文件

- `runtime/mail_event_queue.json`
  - 保存从邮件里识别出的未来会议、截止、提醒事项队列
- `runtime/executive_mailbox.json`
  - 保存今天页面右侧直接展示的提醒卡片
- `runtime/mailbox_collect_report.json`
  - 保存本次邮箱采集状态，方便排查

### 单独测试邮箱链路

```bash
python scripts/collect_mailbox.py
```

如果只想临时关闭邮箱提醒，把 `config/sources.yaml` 里的 `assistant_mailbox.enabled` 改成 `false` 即可。

## 当前定位

Morning Newspaper Assistant 已经具备一个完整早报助手应有的主链路：

- 能采集和抓正文
- 能准备标题粗筛和成稿输入
- 能接住人工/模型回填结果
- 能生成 Top10 发布层
- 能输出静态页面和本地网页入口

接下来更重要的是持续优化内容质量和来源覆盖，而不是继续沿用 `v2` 这种“实验项目”口吻。
