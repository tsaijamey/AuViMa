# ones_create_epic_in_scrum_project

## 功能描述

在ONES项目管理系统（ones.chagee.com）的Scrum项目中自动化Epic工作项创建的准备流程。该配方从工作台首页开始，自动导航到指定的Scrum项目，打开Epic创建对话框，并提取所有必填和可选字段的完整信息，帮助用户理解创建Epic所需的数据结构和默认值。

适用场景：
- 研究ONES系统中Epic的字段结构和验证规则
- 批量创建Epic前的准备工作
- 理解Epic创建流程和必填字段
- 自动化项目管理工作流的前置步骤

## 使用方法

**配方执行器说明**：生成的配方本质上是JavaScript代码，通过CDP的Runtime.evaluate接口注入到浏览器中执行。因此，执行配方的标准方式是使用 `uv run auvima exec-js` 命令。

1. 确保已登录ONES系统（ones.chagee.com）
2. 打开浏览器，确保Chrome CDP已连接（端口9222）
3. 执行配方：
   ```bash
   # 将配方JS文件内容作为脚本注入浏览器执行
   uv run auvima exec-js src/auvima/recipes/ones_create_epic_in_scrum_project.js --return-value
   ```
4. 配方将自动完成以下操作：
   - 确保在工作台首页（如不在则自动跳转）
   - 点击"【Scrum】D端-算法/AI应用"项目卡片
   - 切换到Epic标签页
   - 点击"+Epic"按钮打开创建对话框
   - 分析并返回所有表单字段的详细信息

**注意**：AI调试时请记住，你生成的 `.js` 文件不是在 Node.js 环境中运行，而是在浏览器的上下文中运行（类似 Chrome Console）。因此：
- 不能使用 `require()` 或 `import`
- 可以直接使用 `document`, `window` 等浏览器 API
- `console.log` 的输出通常需要查看 `--return-value` 或浏览器控制台

## 前置条件

- 已登录 ONES 系统（ones.chagee.com）
- 有权限访问"【Scrum】D端-算法/AI应用"项目
- 有权限创建Epic工作项
- Chrome CDP已连接（ws://127.0.0.1:9222）
- 浏览器已打开ONES系统页面（配方会自动导航到首页）

## 预期输出

配方成功执行后，将打开Epic创建对话框，并返回JSON格式的详细字段信息：

```json
{
  "success": true,
  "message": "Epic创建对话框已打开，表单字段分析完成",
  "url": "https://ones.chagee.com/project/#/team/xxx/epic",
  "requiredFieldsCount": 6,
  "optionalFieldsCount": 4,
  "fields": {
    "required": {
      "title": {
        "type": "input",
        "description": "Epic标题",
        "example": "完全基于AI的自动化工作流生成(AI能力基建)"
      },
      "project": {
        "type": "select",
        "description": "所属项目",
        "defaultValue": "【Scrum】D端-算法/AI应用"
      },
      "workItemType": {
        "type": "select",
        "description": "工作项类型",
        "defaultValue": "Epic"
      },
      "owner": {
        "type": "select",
        "description": "负责人",
        "defaultValue": "蔡佳"
      },
      "projectLevel": {
        "type": "select",
        "description": "项目等级",
        "defaultValue": "B级",
        "options": ["A级", "B级", "C级", "D级"]
      },
      "businessCenter": {
        "type": "select",
        "description": "业务中心",
        "defaultValue": "未设置",
        "note": "必填！需要根据实际情况选择"
      }
    },
    "optional": {
      "description": {
        "type": "richtext",
        "description": "Epic描述"
      },
      "priority": {
        "type": "select",
        "description": "优先级",
        "defaultValue": "P2",
        "options": ["P0", "P1", "P2", "P3", "P4"]
      },
      "iteration": {
        "type": "select",
        "description": "所属迭代",
        "defaultValue": "未设置"
      }
    }
  },
  "next_steps": [
    "1. 填写标题（必填）- 输入Epic名称",
    "2. 确认所属项目（必填）- 通常已默认正确",
    "3. 选择负责人（必填）- 默认为蔡佳，可修改",
    "4. 选择项目等级（必填）- 根据Epic重要性选择A/B/C/D级",
    "5. 选择业务中心（必填）- 需要手动选择",
    "6. 填写描述和其他可选字段",
    "7. 点击"确定"按钮提交"
  ],
  "warnings": [
    "业务中心是必填字段，默认为"未设置"，提交前必须选择一个具体的业务中心",
    "由于ONES系统使用React/Vue框架，自动填写输入框可能不会触发框架的状态更新",
    "建议使用此配方打开对话框后，手动填写表单字段"
  ]
}
```

## 注意事项

- **选择器稳定性**：使用了3个高稳定性选择器（class选择器），1个中等稳定性选择器（文本匹配）
  - `.home-card-base`（优先级4）- 首页项目卡片
  - `.ones-tabs-item`（优先级4）- Epic标签页
  - `[role="dialog"]`（优先级5）- 对话框
- **项目特定性**：配方硬编码了"【Scrum】D端-算法/AI应用"项目名称，如果需要支持其他项目，需要修改第38-40行的项目选择逻辑
- **框架限制**：ONES系统使用React/Vue等现代前端框架，直接通过JavaScript设置input.value不会触发框架的状态更新，因此配方不包含自动填写功能，仅负责打开对话框和提取字段信息
- **必填字段警告**：
  - "业务中心"字段默认为"未设置"，提交前必须手动选择一个具体的业务中心
  - 如果不选择，点击"确定"按钮将会失败
- **等待时间**：各步骤间设置了1000ms-2000ms的等待时间，根据网络状况和系统响应速度，可能需要调整
- 如ONES系统改版导致脚本失效，使用 `/auvima.recipe update ones_create_epic_in_scrum_project` 更新
- 当前配方仅打开对话框并提取字段信息，不执行实际的表单填写和提交操作

## 更新历史

| 日期 | 版本 | 变更说明 |
|------|------|----------|
| 2025-11-20 | v5 | 修复按钮查找逻辑：改为只匹配文本为"Epic"的按钮（"+"是SVG图标，不在textContent中），配方现已能成功打开对话框并返回完整字段信息 |
| 2025-11-20 | v4 | 重构导航流程：从首页直接点击项目卡片（而非项目管理菜单），使用更稳定的选择器（.home-card-base），更详细的字段信息和警告提示 |
| 2025-11-20 | v3 | 修复异步语法：使用箭头函数IIFE `(async () => {...})()`，CDP能正确等待Promise |
| 2025-11-20 | v2 | 尝试移除IIFE（失败：顶层return在CDP中不合法） |
| 2025-11-20 | v1 | 初始版本：实现从首页导航到Epic创建对话框，提取所有字段信息 |
