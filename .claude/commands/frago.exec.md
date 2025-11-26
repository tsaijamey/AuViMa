---
description: "执行一次性的复杂任务（使用完整的frago工具集）"
---

# /frago.exec - 执行复杂任务

## 你的任务

作为任务执行者，你需要优先使用完整的 **frago 工具集**、**已有的配方**和**已有的project工作记录**(通过rg搜索)，完成用户指定的一次性复杂任务。与 `/frago.run`（专注于调研）不同，本命令专注于**任务完成**。

## 核心定位

- **目标**：完成用户指定的具体任务（如"在Upwork申请5个Python职位"）
- **成功标准**：任务目标达成 + 结果可验证
- **工作空间**：使用 `projects/` 目录（与 `/frago.run` 共享基础设施）

### 🔒 工作空间隔离原则（必须遵守）

**所有产出物必须放在 Project 工作空间内**：

```
projects/<project_id>/       # Project 工作空间根目录
├── project.json             # 元数据
├── logs/
│   └── execution.jsonl      # 执行日志
├── scripts/                 # 执行脚本
├── screenshots/             # 截图
├── outputs/                 # 任务产出物（数据、报告、视频等）
│   ├── video_script.json    # 生成的脚本实例
│   ├── final_video.mp4      # 视频产出
│   └── analysis.json        # 分析结果
└── temp/                    # 临时文件（任务完成后清理）
```

**禁止的行为**：
- ❌ 在桌面、/tmp、下载目录等外部位置创建文件
- ❌ 配方执行时不指定 output_dir，使用配方默认位置
- ❌ 产出物散落在工作空间外的目录

**正确做法**：
- ✅ 所有文件使用 `projects/<project_id>/` 下的路径
- ✅ 调用配方时明确指定 `output_dir` 为工作空间内的目录
- ✅ 临时文件放在 `temp/`，任务完成后清理

```bash
# 正确：所有输出都在工作空间内
uv run frago recipe run video_produce_from_script \
  --params '{
    "script_file": "projects/<project_id>/outputs/video_script.json",
    "output_dir": "projects/<project_id>/outputs/video"
  }'

# 错误：使用外部目录
uv run frago recipe run video_produce_from_script \
  --params '{"script_file": "~/Desktop/script.json"}'  # ❌ 禁止
```

### 🔐 单一运行互斥（Single Run Mutex）

**系统仅允许一个活跃的 Project 上下文**。这是设计约束，确保工作聚焦。

**互斥规则**：
- 当 `set-context` 时，若已有其他活跃的 project，命令会失败并提示先释放
- 同一 project 可以重复 `set-context`（恢复工作）
- 任务完成后**必须**释放上下文

**释放命令**：

```bash
# 释放当前上下文
uv run frago run release
```

**典型工作流**：

```bash
# 1. 开始任务
uv run frago run init "upwork python job apply"
uv run frago run set-context upwork-python-job-apply

# 2. 执行任务...

# 3. 任务完成，释放上下文（必须！）
uv run frago run release

# 4. 开始新任务
uv run frago run init "another task"
uv run frago run set-context another-task
```

**如果忘记释放**：

```bash
# 尝试设置新上下文时会看到错误
Error: Another run 'upwork-python-job-apply' is currently active.
Run 'uv run frago run release' to release it first,
or 'uv run frago run set-context upwork-python-job-apply' to continue it.
```

## 工具优先级（必须遵守）

执行任务时，按以下优先级选择工具：

```
1. 已有配方 (Recipe)     ← 最优先：经过验证、可复用
2. frago 命令            ← 次优先：跨 agent 通用
3. Claude Code 内置工具  ← 最后：仅限 Claude Code 环境
```

### 为什么这个优先级很重要？

- **配方**：已封装的可靠自动化流程，直接调用最高效
- **frago 命令**：基于 CDP 的通用能力，任何 agent CLI 都能调用
- **Claude Code 工具**：如 WebSearch、WebFetch 仅限 Claude Code 环境

### 具体场景示例

| 需求 | ❌ 不要 | ✅ 应该 |
|------|--------|--------|
| 搜索信息 | `WebSearch` | `uv run frago navigate "https://google.com/search?q=..."` + 提取结果 |
| 查看网页 | `WebFetch` | `uv run frago navigate <url>` + `uv run frago get-content` |
| 提取数据 | 手写 JS | 先查 `uv run frago recipe list` 是否有现成配方 |
| 截图 | 无 | `uv run frago screenshot` 或 `uv run frago run screenshot` |

### 搜索和浏览的正确方式

```bash
# 搜索（使用 CDP 而非 WebSearch）
uv run frago navigate "https://www.google.com/search?q=python+tutorial"
uv run frago exec-js "Array.from(document.querySelectorAll('.g')).map(e => ({title: e.querySelector('h3')?.textContent, url: e.querySelector('a')?.href})).filter(e => e.url)" --return-value

# 查看网页（使用 CDP 而非 WebFetch）
uv run frago navigate "https://example.com"
uv run frago get-content  # 获取页面文本
# 或
uv run frago exec-js "document.body.innerText" --return-value
```

## 可用工具

### 🔍 资源发现

**开始任务前，先搜索已有资源**：

```bash
# 查找可复用的配方
uv run frago recipe list --format json

# 搜索相关的历史项目记录
rg -l "关键词" projects/

# 查看某个项目的执行日志
cat projects/<project_id>/logs/execution.jsonl
```

**命令用法查询**：

```bash
uv run frago --help              # 所有命令
uv run frago <command> --help    # 具体用法
```

### 📝 核心命令（必须掌握）

#### 1. Run 命令系统（任务管理）

**初始化和上下文**：
```bash
uv run frago run init "task-description"
uv run frago run set-context <project_id>
```

**记录日志**（最重要）：
```bash
uv run frago run log \
  --step "步骤描述" \
  --status "success|error|warning" \
  --action-type "<9种有效值之一>" \
  --execution-method "<6种有效值之一>" \
  --data '{"key": "value"}'
```

**9种有效 action-type 值**：
1. `navigation` - 页面导航
2. `extraction` - 数据提取
3. `interaction` - 页面交互
4. `screenshot` - 截图
5. `recipe_execution` - Recipe执行
6. `data_processing` - 数据处理
7. `analysis` - AI分析
8. `user_interaction` - 用户交互
9. `other` - 其他

**6种有效 execution-method 值**：
1. `command` - CLI命令
2. `recipe` - Recipe调用
3. `file` - 脚本文件
4. `manual` - 手动操作
5. `analysis` - AI推理
6. `tool` - AI工具

**常见错误**：
- ❌ `web_search` → ✅ `data_processing`
- ❌ `browsing` → ✅ `navigation`
- ❌ `scraping` → ✅ `extraction`

#### 2. Recipe 系统

```bash
# 发现 Recipe
uv run frago recipe list --format json
uv run frago recipe info <name> --format json

# 执行 Recipe
uv run frago recipe run <name> --params '{...}' --output-file result.json
```

#### 3. 其他常用命令

**浏览器操作**：参考 `uv run frago --help`，包括：
- `navigate` - 导航
- `click` - 点击
- `exec-js` - 执行 JavaScript
- `screenshot` - 截图

**提示**：需要其他命令时，使用 `--help` 查询

## 执行流程

### 1. 明确任务目标和输出物

在开始前，**必须明确任务的输出物要求**：

#### Step 1: 分析用户的输出物需求

检查用户的任务描述是否明确了输出格式：

**✅ 输出物明确的情况**（直接执行）：
- "生成一份 JSON 格式的投资分析数据"
- "输出 Markdown 格式的研究报告"
- "保存 CSV 格式的职位列表"
- "导出 HTML 格式的可视化报告"

**⚠️ 输出物模糊的情况**（需要询问用户）：
- "分析伯克希尔投资 Google 的逻辑" → 没说要什么格式
- "帮我研究一下 API 使用方法" → 没说要文档还是数据
- "在 Upwork 申请职位" → 没说要什么记录

#### Step 2: 如果输出物模糊，使用 AskUserQuestion 明确

**重要**：如果用户没有明确输出格式，**必须**使用 **AskUserQuestion** 工具询问：

```markdown
问题：你希望任务的最终输出是什么格式？
选项：
- 📊 结构化数据（JSON/CSV）- 适合后续处理和分析
- 📝 文档报告（Markdown/HTML）- 适合阅读和分享
- 💾 仅执行日志 - 最小化输出，只保存执行记录
- 🖼️ 截图集合 - 可视化记录关键步骤
```

**记录用户选择**：
```bash
uv run frago run log \
  --step "明确任务输出物格式" \
  --status "success" \
  --action-type "user_interaction" \
  --execution-method "tool" \
  --data '{"tool": "AskUserQuestion", "question": "输出格式确认", "answer": "结构化数据文件（JSON）", "reasoning": "用户选择 JSON 格式用于后续分析"}'
```

#### Step 3: 确定最终输出规格

基于用户的明确要求或选择，定义输出规格：

```markdown
## 任务目标
- **任务描述**：[用户原始需求]
- **成功标准**：[可验证的完成条件]
- **输出格式**：[用户明确的格式或通过交互确认的格式]
- **输出位置**：projects/<project_id>/outputs/
- **文件命名**：[描述性名称，反映内容]

示例 1（结构化数据 - JSON）：
- 任务描述：在Upwork上申请5个Python职位
- 成功标准：成功提交5个申请 + 保存职位详情
- 输出格式：JSON（包含职位列表、申请状态、时间戳）
- 输出文件：`outputs/applied_jobs.json`

示例 2（文档报告 - Markdown）：
- 任务描述：分析伯克希尔投资 Google 的逻辑
- 成功标准：完整的投资分析 + 数据支撑
- 输出格式：Markdown 报告（包含时间线、分析、数据）
- 输出文件：`outputs/investment_analysis.md`

示例 3（结构化数据 - CSV）：
- 任务描述：提取Upwork上Python职位列表
- 成功标准：提取至少20个职位的详细信息
- 输出格式：CSV 表格（便于Excel打开）
- 输出文件：`outputs/python_jobs.csv`

示例 4（HTML报告）：
- 任务描述：生成网页数据分析报告
- 成功标准：包含图表和表格的可视化报告
- 输出格式：HTML（可在浏览器中打开）
- 输出文件：`outputs/analysis_report.html`
```

### 2. 生成任务 ID

**重要**：project_id 必须是简洁、可读的英文短句（3-5 个词）

```python
# 示例
用户任务："在Upwork上申请5个Python职位"
任务短句："upwork python job apply"

用户任务："批量下载YouTube视频字幕"
任务短句："youtube batch download subtitles"
```

### 3. 初始化工作空间

```bash
# 创建 project
uv run frago run init "upwork python job apply"

# 设置上下文（假设返回的 project_id 是 upwork-python-job-apply）
uv run frago run set-context upwork-python-job-apply
```

### 4. 执行任务并记录日志

每完成一个关键步骤后记录日志：

```bash
# 示例：导航到Upwork
uv run frago navigate https://upwork.com/jobs

uv run frago run log \
  --step "导航到Upwork职位搜索页" \
  --status "success" \
  --action-type "navigation" \
  --execution-method "command" \
  --data '{"url": "https://upwork.com/jobs"}'

# 示例：提取职位列表
uv run frago exec-js "Array.from(document.querySelectorAll('.job-tile')).map(el => ({title: el.querySelector('.title').textContent, url: el.querySelector('a').href}))"

uv run frago run log \
  --step "提取到15个Python职位" \
  --status "success" \
  --action-type "extraction" \
  --execution-method "command" \
  --data '{"jobs": [...], "total": 15}'
```

### 5. 使用 Recipe 加速重复操作

如果发现重复操作（如批量申请），优先使用 Recipe：

```bash
# 发现现有 Recipe
uv run frago recipe list --format json | grep "upwork"

# 如果有现成的 Recipe
uv run frago recipe run upwork_apply_job \
  --params '{"job_url": "https://...", "cover_letter": "..."}' \
  --output-file result.json

# 记录日志
uv run frago run log \
  --step "使用Recipe申请职位" \
  --status "success" \
  --action-type "recipe_execution" \
  --execution-method "recipe" \
  --data '{"recipe": "upwork_apply_job", "result": {...}}'
```

### 6. 保存任务结果

```bash
# 保存关键截图
uv run frago run screenshot "申请成功页面"

# 将结果保存到 outputs/
echo '{"applied_jobs": [...]}' > projects/<project_id>/outputs/result.json

# 记录最终结果
uv run frago run log \
  --step "完成任务：成功申请5个职位" \
  --status "success" \
  --action-type "user_interaction" \
  --execution_method "analysis" \
  --data '{"total_applied": 5, "result_file": "outputs/result.json", "task_completed": true}'
```

## 任务成功标准

### ✅ 完成条件

任务完成需满足以下条件：

1. **用户目标达成**：
   - 任务描述中的具体目标已实现
   - 可通过日志或文件验证

2. **结果已保存**：
   - 任务结果保存到 `outputs/` 或日志
   - 关键步骤有截图记录

3. **最后一条日志标记**：
   ```json
   {
     "action_type": "analysis",
     "execution_method": "analysis",
     "step": "完成任务：[简要描述]",
     "data": {
       "task_completed": true,
       "summary": "完成情况摘要",
       "result_file": "outputs/result.json"  // 可选
     }
   }
   ```

### 🛑 停止条件

满足以下任一条件立即停止：
- 用户目标达成 + 最后一条日志标记 `task_completed: true`
- 任务执行失败，原因已记录
- 用户明确指示停止

## 输出约束

### ✅ 允许的输出

**根据用户选择的输出格式，创建相应的文件**：

#### 1. **必需输出**
- `execution.jsonl`（执行日志，记录所有操作步骤）

#### 2. **用户指定的结果文件**（根据 Step 1 确认的格式）

**📊 结构化数据文件**（Agent 可直接生成）：
- `outputs/*.json` - JSON 格式数据
- `outputs/*.csv` - CSV 表格（简单的逗号分隔）

**📝 文档报告**（Agent 可直接生成）：
- `outputs/*.md` - Markdown 格式报告
- `outputs/*.html` - HTML 格式报告
- `outputs/*.txt` - 纯文本文件

**🖼️ 多媒体文件**（通过工具生成）：
- `screenshots/*.png` - 截图（使用 `uv run frago screenshot`）
- `outputs/*.srt` - 字幕文件（如果任务涉及）

**⚠️ 复杂格式**（需要额外库，一般不推荐）：
- ~~`outputs/*.pdf`~~ - 需要 PDF 库，复杂度高
- ~~`outputs/*.xlsx`~~ - 需要 Excel 库，建议用 CSV 代替

#### 3. **辅助文件**（可选）
- `scripts/*.{py,js,sh}` - 执行过程中生成的脚本
- `outputs/metadata.json` - 输出文件的元数据说明

### ❌ 禁止的行为

- **违背用户选择**：用户选择 JSON，不要输出 Markdown
- **创建未经确认的文档**：如果用户没选"文档报告"，不要创建 `.md` 或 `.html`
- **生成复杂格式**：不要尝试生成 PDF、XLSX 等需要额外库的格式
- **重复记录相似的日志**：避免冗余
- **过度输出**：每个关键步骤记录一次即可

### 📋 输出文件命名规范

- **描述性命名**：`investment_analysis.json` 而非 `result.json`
- **日期标记**（如需要）：`jobs_2025-11-23.csv`
- **版本区分**（如有多个）：`report_v1.md`, `report_v2.md`

## 进度展示

每完成 5 个关键步骤，输出进度摘要：

```markdown
✅ 已完成 5 步：
1. 导航到Upwork搜索页（navigation/command）
2. 搜索Python职位（interaction/command）
3. 提取15个职位列表（extraction/command）
4. 筛选合适职位（data_processing/analysis）
5. 申请第1个职位（user_interaction/recipe）

📊 当前进度：已申请 1/5 个职位
📁 输出文件：outputs/applied_jobs.json
```

## 最佳实践

### ✅ 推荐做法

1. **优先使用 Recipe**：避免重复手动操作
2. **结构化输出**：任务结果保存为 JSON 格式
3. **关键步骤截图**：保留任务完成的证据
4. **每5步输出进度**：让用户了解任务进展
5. **失败及时记录**：错误信息记录在日志中

### ❌ 禁止做法

1. **跳过上下文设置**：必须先 `set-context`
2. **忽略错误**：任务失败需记录原因
3. **过度日志**：只记录关键步骤
4. **创建冗余文档**：不要创建总结 Markdown

## 任务完成后

生成执行摘要：

```markdown
✅ 任务完成！

**Project**: upwork-python-job-apply
**执行时间**: 2025-11-23 14:00 - 14:30 (30分钟)

**完成情况**：
- 成功申请 5 个 Python 职位
- 保存职位详情到 outputs/applied_jobs.json
- 保存申请截图到 screenshots/

**关键步骤**：
1. 导航到Upwork并搜索
2. 提取15个候选职位
3. 筛选出5个合适职位
4. 批量申请（使用Recipe加速）
5. 验证申请成功

**输出文件**：
- outputs/applied_jobs.json（5个职位详情）
- screenshots/001_search-results.png
- screenshots/002_application-success.png

**详细日志**: projects/upwork-python-job-apply/logs/execution.jsonl（共12条记录）
```

## 注意事项

- **工作目录管理**：始终在项目根目录执行命令，使用相对路径访问文件
- **禁止使用 `cd`**：会导致 `uv run frago` 命令失效
- **上下文优先级**：环境变量 `FRAGO_CURRENT_RUN` > 配置文件 `.frago/current_project`
- **并发安全**：同一时间只在一个 project 中工作
