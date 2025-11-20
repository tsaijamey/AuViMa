---
description: "创建可复用的浏览器操作配方脚本"
---

# /auvima.recipe - 配方创建指令

## 你的任务

引导用户创建一个可复用的JavaScript配方脚本，通过实际执行CDP操作来探索步骤，然后将经验写成代码。

---

## 可用的AuViMa原子操作

```bash
# --- 基础导航 ---
# 导航到URL (可选等待元素出现)
uv run auvima navigate <url> [--wait-for <selector>]
# 获取页面标题
uv run auvima get-title

# --- 交互操作 ---
# 点击元素
uv run auvima click <selector> [--wait-timeout 10]
# 滚动页面 (正数向下，负数向上)
uv run auvima scroll <pixels>
# 等待指定时间
uv run auvima wait <seconds>

# --- 信息提取与调试 ---
# 执行JavaScript (加 --return-value 获取结果)
uv run auvima exec-js <expression> [--return-value]
# 获取文本内容 (默认body)
uv run auvima get-content [selector]
# 截图 (加 --full-page 截全屏)
uv run auvima screenshot <output_file> [--full-page]

# --- 视觉确认 (用于验证选择器) ---
# 高亮元素
uv run auvima highlight <selector>
# 显示鼠标指针
uv run auvima pointer <selector>
```

**选择器类型**：CSS选择器、ARIA标签（`[aria-label="..."]`）、ID（`#id`）、类名（`.class`）

---

## 选择器优先级规则

在生成JavaScript时，按此优先级排序选择器（5最高，1最低）：

| 优先级 | 类型 | 示例 | 稳定性 | 说明 |
|--------|------|------|--------|------|
| **5** | ARIA标签 | `[aria-label="按钮"]` | ✅ 很稳定 | 无障碍属性，极少改变 |
| **5** | data属性 | `[data-testid="submit"]` | ✅ 很稳定 | 专门用于测试 |
| **4** | 稳定ID | `#main-button` | ✅ 稳定 | 语义化ID名称 |
| **3** | 语义化类名 | `.btn-primary` | ⚠️ 中等 | BEM规范类名 |
| **3** | HTML5语义标签 | `button`, `nav` | ⚠️ 中等 | 标准语义标签 |
| **2** | 结构选择器 | `div > button` | ⚠️ 脆弱 | 依赖DOM结构 |
| **1** | 生成的类名 | `.css-abc123` | ❌ 很脆弱 | CSS-in-JS，随时变化 |

**脆弱选择器识别**：
- `.css-*` 或 `._*` 开头的类名
- 纯数字ID：`#12345`
- 过长的ID/类名（>20字符）

---

## 执行流程

### 1. 目标澄清

问清楚：
- 在哪个网站操作？
- 要完成什么任务？
- 前置条件是什么？（如：已打开某页面、已登录）

**文件命名思考**：
根据任务目标，构思一个能自我解释的**短句文件名**。
- 格式：`<平台>_<动词>_<对象>_<补充>.js`
- 目的：让AI仅看文件名就能理解脚本用途
- 示例：
  - `youtube_extract_video_transcript.js` (好：清晰明了)
  - `youtube_transcript.js` (差：是提取？显示？还是隐藏？)
  - `github_star_repository_if_not_starred.js` (好：逻辑完整)

### 2. 逐步探索（带结果验证）

引导用户描述每个步骤，**你实际执行CDP命令并验证结果**：

```
你: 第一步需要做什么？
用户: 点击"作者声明"展开详情
你: [执行] uv run auvima click '[aria-label="作者声明"]'
你: [等待] uv run auvima wait 0.5
你: [验证] uv run auvima screenshot /tmp/step1_result.png
你: [查看截图，确认详情已展开]
    ✓ 成功。记录：ARIA选择器（优先级5）
    ✓ 验证通过：页面出现了详情内容区域
    下一步呢？
```

**关键原则：每步必须验证**

对于每个操作步骤，必须验证其**结果特征**：

1. **导航操作**（navigate/click导致页面跳转）
   - 验证URL是否变化：`uv run auvima exec-js "window.location.href" --return-value`
   - 验证页面标题：`uv run auvima get-title`
   - 验证关键元素出现：`uv run auvima exec-js "document.querySelector('<特征元素>') !== null" --return-value`

2. **UI交互操作**（点击按钮/菜单）
   - 截图对比：`uv run auvima screenshot /tmp/stepN.png`
   - 验证目标元素出现/消失
   - 检查文本内容变化

3. **表单/输入操作**
   - 验证输入值已填充
   - 验证错误提示/成功提示

**记录每步的执行信息**：
- 使用的选择器（及其优先级）
- 执行的操作
- **等待时间**（根据页面响应速度调整）
- **验证方法**（如何确认步骤成功）
- **预期的页面特征变化**（用于生成验证代码）

**验证失败时的处理**：
如果某步验证失败（点击无效、元素未出现等）：
1. 尝试其他选择器
2. 增加等待时间
3. 检查是否需要滚动到元素位置
4. 记录哪些选择器失败了（避免写入配方）

### 3. 生成配方文件

对话结束后，**使用Write工具**创建两个文件。**注意：Markdown文档必须与JS脚本完全同名！**

#### 文件1: `src/auvima/recipes/<自解释文件名>.js`

JavaScript配方脚本：

```javascript
/**
 * Recipe: <自解释文件名>
 * Platform: <平台名>
 * Description: <功能描述>
 * Created: <YYYY-MM-DD>
 * Version: 1
 */

(async () => {
  // 辅助函数：按优先级尝试多个选择器
  function findElement(selectors, description) {
    for (const sel of selectors) {
      const elem = document.querySelector(sel.selector);
      if (elem) return elem;
    }
    throw new Error(`无法找到${description}`);
  }

  // 辅助函数：等待并验证元素出现
  async function waitForElement(selector, description, timeout = 5000) {
    const startTime = Date.now();
    while (Date.now() - startTime < timeout) {
      const elem = document.querySelector(selector);
      if (elem) return elem;
      await new Promise(r => setTimeout(r, 100));
    }
    throw new Error(`等待超时：${description} (${selector})`);
  }

  // 步骤1: <用户描述>
  const elem1 = findElement([
    { selector: '<ARIA或data属性>', priority: 5 },  // 最稳定
    { selector: '<稳定ID>', priority: 4 },           // 降级
    { selector: '<语义类名>', priority: 3 }          // 再降级
  ], '<元素描述>');
  elem1.click();

  // 验证步骤1成功：等待<预期特征>出现
  await waitForElement('<验证选择器>', '<预期特征描述>');
  await new Promise(r => setTimeout(r, 500));

  // 步骤2: <用户描述>
  const elem2 = findElement([
    { selector: '<选择器1>', priority: 5 }
  ], '<元素描述>');
  elem2.click();

  // 验证步骤2成功：检查<预期特征>
  await waitForElement('<验证选择器>', '<预期特征描述>');
  await new Promise(r => setTimeout(r, 500));

  // 步骤3: 提取数据
  const result = document.querySelector('.target').innerText;

  return result;
})();
```

**编写规则**：
- 使用箭头函数IIFE：`(async () => {...})()`（CDP才能正确等待Promise）
- 优先使用高优先级选择器（ARIA/data > ID > class）
- 每个元素提供2-3个降级选择器（如果探索中使用了多个）
- **每步操作后必须验证**：使用 `waitForElement()` 等待预期特征出现
- 操作后等待：点击/输入后500ms，导航后2000ms
- 清晰的错误消息（包含选择器信息）
- **验证选择器的选择**：选择步骤执行成功后"必然出现"的唯一元素

#### 文件2: `src/auvima/recipes/<自解释文件名>.md`

**关键要求**：必须与JS文件同名（仅后缀不同），作为该配方的配套说明书。AI在使用配方前会检索并阅读此文件。

知识文档，**必须包含6个标准章节**：

```markdown
# <自解释文件名>

## 功能描述
<详细说明这个配方的用途、适用场景和价值>

## 使用方法

**配方执行器说明**：生成的配方本质上是JavaScript代码，通过CDP的Runtime.evaluate接口注入到浏览器中执行。因此，执行配方的标准方式是使用 `uv run auvima exec-js` 命令。

1. <前置条件步骤>
2. 执行配方：
   ```bash
   # 将配方JS文件内容作为脚本注入浏览器执行
   uv run auvima exec-js recipes/<自解释文件名>.js
   ```
3. <查看结果的方法>

**注意**：AI调试时请记住，你生成的 `.js` 文件不是在 Node.js 环境中运行，而是在浏览器的上下文中运行（类似 Chrome Console）。因此：
- 不能使用 `require()` 或 `import`
- 可以直接使用 `document`, `window` 等浏览器 API
- `console.log` 的输出通常需要查看 `--return-value` 或浏览器控制台

## 前置条件
- <条件1：如"已打开YouTube视频页面">
- <条件2：如"视频字幕已开启">
- Chrome CDP已连接

## 预期输出
<说明脚本成功后返回什么数据，格式是什么>

## 注意事项
- **选择器稳定性**：使用了<N>个ARIA选择器，<M>个class选择器
- **脆弱选择器**（如有）：`<选择器>`（<原因>，可能随网站改版失效）
- 如<网站名>改版导致脚本失效，使用 `/auvima.recipe update <配方名>` 更新
- <其他注意事项>

## 更新历史
| 日期 | 版本 | 变更说明 |
|------|------|----------|
| <YYYY-MM-DD> | v1 | 初始版本 |
```

---

## 更新模式

如果用户执行 `/auvima.recipe update <配方名> "原因"`：

1. **读取现有配方**：
   ```bash
   # 使用Read工具读取
   src/auvima/recipes/<配方名>.js
   src/auvima/recipes/<配方名>.md
   ```

2. **显示当前信息**：
   - 当前版本号（从.md的更新历史提取）
   - 当前选择器（从.js头部注释或代码提取）
   - 上次更新原因

3. **重新探索**：按照"逐步探索"流程，引导用户重新描述步骤

4. **覆盖写入**：
   - `.js` 文件：完全覆盖，版本号+1
   - `.md` 文件：覆盖全文，在"更新历史"表格**追加新行**（不是替换）

**更新历史示例**：
```markdown
| 日期 | 版本 | 变更说明 |
|------|------|----------|
| 2025-11-20 | v2 | YouTube改版，更新字幕按钮选择器 |
| 2025-11-19 | v1 | 初始版本 |
```

---

## 列出模式

如果用户执行 `/auvima.recipe list`：

1. **扫描目录**：读取 `src/auvima/recipes/*.js` 所有文件

2. **提取元数据**：从每个.js文件头部注释读取：
   ```javascript
   /**
    * Recipe: youtube_extract_video_transcript
    * Platform: youtube
    * Description: 提取视频字幕内容
    * Version: 2
    */
   ```

3. **按平台分组显示**：
   ```
   配方库（src/auvima/recipes/）：

   【YouTube】
   1. youtube_extract_video_transcript.js - 提取视频字幕内容 (v2)
   2. youtube_download_video_as_mp4.js - 下载视频 (v1)

   【GitHub】  
   3. github_get_repository_clone_url.js - 获取仓库克隆信息 (v1)

   总计：3个配方
   ```

---

## 重要提醒

1. **验证是核心**：每步操作后必须验证结果，否则配方会因步骤失败而返回错误结果
2. **你会写代码**：直接用Write工具写.js和.md，不要调用任何Python函数
3. **你经历过整个过程**：你执行了CDP命令并验证了结果，所以你知道：
   - 哪些选择器有效
   - 每步成功后出现了什么特征
   - 需要等待多久
4. **文件命名规范**：`<平台>_<动词>_<对象>_<补充>.js`（全小写，短句式），必须有同名`.md`文件
5. **6章节完整性**：知识文档必须包含全部6个章节
6. **选择器降级**：按优先级从高到低排列，提供2-3个备选
7. **异步语法**：使用 `(async () => {...})()` 而非 `(async function(){...})()` 或顶层await+return

---

## 开始执行

根据用户输入判断模式：
- 如果是 `/auvima.recipe update <配方名> "原因"`：进入**更新模式**
- 如果是 `/auvima.recipe list`：进入**列出模式**
- 否则：进入**创建模式**（从目标澄清开始）
