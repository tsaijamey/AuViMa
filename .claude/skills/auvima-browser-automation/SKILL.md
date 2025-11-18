---
name: auvima-browser-automation
description: 使用AuViMa CLI自动化浏览器操作。当需要网页数据采集、视频素材收集、UI测试或任何需要与浏览器交互的任务时使用此skill。核心原则：每个操作后必须验证结果，先探索DOM结构，适当等待页面加载。
---

# AuViMa Browser Automation Skill

## Instructions

你是一个AuViMa浏览器自动化专家，精通使用AuViMa CLI进行网页操作、数据采集和UI自动化。

### 核心原则

- ⚠️ **每个操作后必须验证结果** - 通过 `get-title`、`get-content` 或 `exec-js` 检查操作是否成功
- 📋 **先探索DOM结构** - 使用 `exec-js` 获取HTML片段，找到正确的选择器
- 🔄 **适当等待** - 页面加载、JavaScript渲染都需要 `wait` 命令
- 📸 **关键步骤截图** - 便于调试和验证

---

## 场景1: YouTube - 查找特定主题的最新视频

**需求**: 在YouTube上搜索"AI tutorial"，获取前5个视频的标题和链接。

### 实现步骤

```bash
# Step 1: 导航到YouTube
uv run auvima navigate https://youtube.com

# Step 2: 等待页面加载
uv run auvima wait 3

# Step 3: 验证页面加载成功
uv run auvima get-title
# 预期输出: YouTube 或类似标题

# Step 4: 探索搜索框的选择器（首次需要）
uv run auvima exec-js "document.querySelector('input[name=\"search_query\"]') ? 'found' : 'not found'" --return-value
# 预期输出: found

# Step 5: 点击搜索框
uv run auvima click "input[name='search_query']"
uv run auvima wait 0.5

# Step 6: 输入搜索关键词
uv run auvima exec-js "document.querySelector('input[name=\"search_query\"]').value='AI tutorial'"

# Step 7: 验证输入成功
uv run auvima exec-js "document.querySelector('input[name=\"search_query\"]').value" --return-value
# 预期输出: AI tutorial

# Step 8: 点击搜索按钮
uv run auvima click "button#search-icon-legacy"

# Step 9: 等待搜索结果加载
uv run auvima wait 3

# Step 10: 验证进入搜索结果页
uv run auvima get-title
# 预期输出包含: AI tutorial

# Step 11: 检查视频数量
uv run auvima exec-js "document.querySelectorAll('ytd-video-renderer').length" --return-value
# 预期输出: 数字 (如 20)

# Step 12: 提取前5个视频的标题
uv run auvima exec-js "Array.from(document.querySelectorAll('ytd-video-renderer')).slice(0, 5).map((v, i) => ({index: i+1, title: v.querySelector('#video-title')?.textContent?.trim() || 'N/A'})).map(v => v.index + '. ' + v.title).join('\\n')" --return-value

# Step 13: 提取前5个视频的链接
uv run auvima exec-js "Array.from(document.querySelectorAll('ytd-video-renderer')).slice(0, 5).map((v, i) => ({index: i+1, url: v.querySelector('#video-title')?.href || 'N/A'})).map(v => v.index + '. ' + v.url).join('\\n')" --return-value

# Step 14: 截图保存结果
uv run auvima screenshot youtube_ai_tutorial_search.png --full-page
```

### 关键点

1. **每次操作后验证**: 输入后检查value，点击后检查页面变化
2. **适当等待**: 搜索结果需要3秒加载时间
3. **使用复杂JavaScript提取数据**: 结合 `Array.from`、`map`、`slice` 等方法

---

## 场景2: GitHub - 查找某个仓库的最新Issues

**需求**: 访问某个GitHub仓库，获取最新的5个open issues。

### 实现步骤

```bash
# Step 1: 导航到仓库Issues页面
uv run auvima navigate https://github.com/anthropics/claude-code/issues

# Step 2: 等待页面加载
uv run auvima wait 2

# Step 3: 验证页面加载
uv run auvima get-title
# 预期输出包含: Issues

# Step 4: 探索Issues列表的DOM结构
uv run auvima exec-js "document.querySelector('.js-navigation-container') ? 'found container' : 'not found'" --return-value
# 预期输出: found container

# Step 5: 获取Issues数量
uv run auvima exec-js "document.querySelectorAll('.js-navigation-item').length" --return-value

# Step 6: 提取前5个Issues的标题和链接
uv run auvima exec-js "
Array.from(document.querySelectorAll('.js-navigation-item')).slice(0, 5).map((item, i) => {
  const title = item.querySelector('.js-navigation-open')?.textContent?.trim() || 'N/A';
  const url = item.querySelector('.js-navigation-open')?.href || 'N/A';
  const number = item.querySelector('.opened-by')?.textContent?.match(/#\\d+/)?.[0] || 'N/A';
  return (i+1) + '. ' + number + ' - ' + title + '\\n   URL: ' + url;
}).join('\\n\\n')
" --return-value

# Step 7: 检查第一个Issue的状态
uv run auvima exec-js "
document.querySelector('.js-navigation-item .State')?.textContent?.trim() || 'unknown'
" --return-value
# 预期输出: Open

# Step 8: 截图保存
uv run auvima screenshot github_issues.png --full-page
```

---

## 场景3: 电商网站 - 获取产品列表和价格

**需求**: 访问电商网站，获取某个类别的产品名称和价格。

### 实现步骤

```bash
# Step 1: 导航到产品列表页
uv run auvima navigate https://example-shop.com/products/electronics

# Step 2: 等待页面和JavaScript渲染
uv run auvima wait 3

# Step 3: 探索DOM结构
uv run auvima exec-js "document.body.innerHTML.substring(0, 2000)" --return-value

# Step 4: 识别产品卡片选择器（假设为 .product-card）
uv run auvima exec-js "document.querySelectorAll('.product-card').length" --return-value

# Step 5: 高亮第一个产品（调试用）
uv run auvima highlight ".product-card:first-child" --color green --width 3
uv run auvima screenshot first_product_highlighted.png

# Step 6: 提取产品信息
uv run auvima exec-js "
Array.from(document.querySelectorAll('.product-card')).slice(0, 10).map((card, i) => {
  const name = card.querySelector('.product-name')?.textContent?.trim() || 'N/A';
  const price = card.querySelector('.product-price')?.textContent?.trim() || 'N/A';
  const rating = card.querySelector('.product-rating')?.textContent?.trim() || 'N/A';
  return (i+1) + '. ' + name + ' | Price: ' + price + ' | Rating: ' + rating;
}).join('\\n')
" --return-value

# Step 7: 验证提取的数据
uv run auvima exec-js "
document.querySelector('.product-card .product-name')?.textContent?.trim() || 'not found'
" --return-value

# Step 8: 滚动加载更多产品（如果是无限滚动）
uv run auvima scroll 1000
uv run auvima wait 2

# Step 9: 再次检查产品数量
uv run auvima exec-js "document.querySelectorAll('.product-card').length" --return-value
```

---

## 场景4: 新闻网站 - 获取今日头条

**需求**: 访问新闻网站，获取首页头条新闻的标题和摘要。

### 实现步骤

```bash
# Step 1: 导航
uv run auvima navigate https://news.ycombinator.com

# Step 2: 等待加载
uv run auvima wait 2

# Step 3: 验证页面
uv run auvima get-title
# 预期输出: Hacker News

# Step 4: 探索新闻条目结构
uv run auvima exec-js "document.querySelector('.athing') ? 'found' : 'not found'" --return-value

# Step 5: 统计新闻数量
uv run auvima exec-js "document.querySelectorAll('.athing').length" --return-value

# Step 6: 提取前10条新闻
uv run auvima exec-js "
Array.from(document.querySelectorAll('.athing')).slice(0, 10).map((item, i) => {
  const rank = item.querySelector('.rank')?.textContent || (i+1);
  const title = item.querySelector('.titleline > a')?.textContent?.trim() || 'N/A';
  const url = item.querySelector('.titleline > a')?.href || 'N/A';
  return rank + ' ' + title + '\\n   URL: ' + url;
}).join('\\n\\n')
" --return-value

# Step 7: 获取第一条新闻的评论数
uv run auvima exec-js "
document.querySelector('.athing + tr .subtext a:last-child')?.textContent?.trim() || '0 comments'
" --return-value

# Step 8: 截图
uv run auvima screenshot hackernews_frontpage.png
```

---

## 场景5: 表单填写和提交

**需求**: 自动填写网页表单并提交。

### 实现步骤

```bash
# Step 1: 导航到表单页面
uv run auvima navigate https://example.com/contact

# Step 2: 等待加载
uv run auvima wait 2

# Step 3: 探索表单字段
uv run auvima exec-js "
Array.from(document.querySelectorAll('input, textarea')).map(el => ({
  name: el.name || el.id,
  type: el.type,
  placeholder: el.placeholder
}))
" --return-value

# Step 4: 填写姓名字段
uv run auvima exec-js "document.querySelector('input[name=\"name\"]').value='John Doe'"

# Step 5: 验证姓名已填写
uv run auvima exec-js "document.querySelector('input[name=\"name\"]').value" --return-value
# 预期输出: John Doe

# Step 6: 填写邮箱
uv run auvima exec-js "document.querySelector('input[name=\"email\"]').value='john@example.com'"

# Step 7: 验证邮箱
uv run auvima exec-js "document.querySelector('input[name=\"email\"]').value" --return-value
# 预期输出: john@example.com

# Step 8: 填写消息
uv run auvima exec-js "document.querySelector('textarea[name=\"message\"]').value='This is a test message'"

# Step 9: 验证消息
uv run auvima exec-js "document.querySelector('textarea[name=\"message\"]').value" --return-value

# Step 10: 高亮提交按钮（确认找对了）
uv run auvima highlight "button[type='submit']" --color red --width 5
uv run auvima screenshot form_ready_to_submit.png

# Step 11: 点击提交（如果需要）
# uv run auvima click "button[type='submit']"

# Step 12: 等待提交处理
# uv run auvima wait 2

# Step 13: 验证提交成功（检查成功消息）
# uv run auvima exec-js "document.querySelector('.success-message')?.textContent?.trim() || 'no message'" --return-value
```

---

## 场景6: 视频平台 - 批量收集视频元数据

**需求**: 访问YouTube频道，获取所有视频的发布时间和观看次数。

### 实现步骤

```bash
# Step 1: 导航到频道视频页面
uv run auvima navigate https://www.youtube.com/@channelname/videos

# Step 2: 等待加载
uv run auvima wait 3

# Step 3: 验证页面
uv run auvima get-title

# Step 4: 滚动加载更多视频
uv run auvima scroll 1000
uv run auvima wait 2
uv run auvima scroll 1000
uv run auvima wait 2

# Step 5: 检查视频数量
uv run auvima exec-js "document.querySelectorAll('ytd-grid-video-renderer').length" --return-value

# Step 6: 提取视频元数据
uv run auvima exec-js "
Array.from(document.querySelectorAll('ytd-grid-video-renderer')).map((video, i) => {
  const title = video.querySelector('#video-title')?.textContent?.trim() || 'N/A';
  const views = video.querySelector('#metadata-line span:first-child')?.textContent?.trim() || 'N/A';
  const date = video.querySelector('#metadata-line span:last-child')?.textContent?.trim() || 'N/A';
  const duration = video.querySelector('.ytd-thumbnail-overlay-time-status-renderer')?.textContent?.trim() || 'N/A';
  return (i+1) + '. ' + title + '\\n   Views: ' + views + ' | Date: ' + date + ' | Duration: ' + duration;
}).join('\\n\\n')
" --return-value

# Step 7: 筛选最新视频（发布在1周内）
uv run auvima exec-js "
Array.from(document.querySelectorAll('ytd-grid-video-renderer')).filter(video => {
  const date = video.querySelector('#metadata-line span:last-child')?.textContent?.trim() || '';
  return date.includes('day') || date.includes('hour') || date.includes('minute');
}).map(video => video.querySelector('#video-title')?.textContent?.trim()).join('\\n')
" --return-value

# Step 8: 截图
uv run auvima screenshot youtube_channel_videos.png --full-page
```

---

## 场景7: 动态内容 - 等待AJAX加载完成

**需求**: 处理单页应用(SPA)中的动态内容加载。

### 实现步骤

```bash
# Step 1: 导航到SPA页面
uv run auvima navigate https://example-spa.com/dashboard

# Step 2: 等待初始加载
uv run auvima wait 2

# Step 3: 检查加载指示器
uv run auvima exec-js "document.querySelector('.loading-spinner') ? 'loading' : 'loaded'" --return-value

# Step 4: 循环等待直到内容加载（使用更智能的检查）
uv run auvima exec-js "
(function checkLoading() {
  const spinner = document.querySelector('.loading-spinner');
  const content = document.querySelector('.content-loaded');
  return spinner ? 'still loading' : (content ? 'loaded' : 'unknown state');
})()
" --return-value

# Step 5: 等待特定元素出现
uv run auvima wait 3

# Step 6: 再次验证
uv run auvima exec-js "document.querySelector('.data-table') ? 'table found' : 'table not found'" --return-value

# Step 7: 提取数据
uv run auvima exec-js "
Array.from(document.querySelectorAll('.data-table tbody tr')).map((row, i) => {
  const cells = Array.from(row.querySelectorAll('td')).map(td => td.textContent.trim());
  return (i+1) + '. ' + cells.join(' | ');
}).join('\\n')
" --return-value
```

---

## 场景8: 分页浏览和数据聚合

**需求**: 浏览多页内容，聚合所有页面的数据。

### 实现步骤

```bash
# Step 1: 导航到第一页
uv run auvima navigate https://example.com/products?page=1

# Step 2: 等待加载
uv run auvima wait 2

# Step 3: 提取第一页数据
uv run auvima exec-js "
Array.from(document.querySelectorAll('.product-item')).map(item =>
  item.querySelector('.product-name')?.textContent?.trim()
).join('\\n')
" --return-value

# Step 4: 检查是否有下一页按钮
uv run auvima exec-js "document.querySelector('.next-page') ? 'has next' : 'no next'" --return-value

# Step 5: 点击下一页
uv run auvima click ".next-page"

# Step 6: 等待第二页加载
uv run auvima wait 2

# Step 7: 验证页面切换（检查URL变化）
uv run auvima exec-js "window.location.href" --return-value
# 预期输出包含: page=2

# Step 8: 提取第二页数据
uv run auvima exec-js "
Array.from(document.querySelectorAll('.product-item')).map(item =>
  item.querySelector('.product-name')?.textContent?.trim()
).join('\\n')
" --return-value

# 重复Step 4-8直到没有下一页
```

---

## 通用调试技巧

### 1. 探索DOM结构

```bash
# 获取页面HTML片段
uv run auvima exec-js "document.body.innerHTML.substring(0, 3000)" --return-value

# 查找包含特定文本的元素
uv run auvima exec-js "
Array.from(document.querySelectorAll('*')).filter(el =>
  el.textContent.includes('搜索')
).map(el => el.tagName + '.' + el.className).slice(0, 10).join('\\n')
" --return-value

# 获取所有链接
uv run auvima exec-js "
Array.from(document.querySelectorAll('a')).map(a => a.href).slice(0, 20).join('\\n')
" --return-value
```

### 2. 验证选择器

```bash
# 测试选择器是否有效
uv run auvima exec-js "document.querySelector('YOUR_SELECTOR') ? 'found' : 'not found'" --return-value

# 统计匹配元素数量
uv run auvima exec-js "document.querySelectorAll('YOUR_SELECTOR').length" --return-value

# 获取元素的所有属性
uv run auvima exec-js "
const el = document.querySelector('YOUR_SELECTOR');
el ? {
  tag: el.tagName,
  id: el.id,
  class: el.className,
  text: el.textContent.substring(0, 100)
} : null
" --return-value
```

### 3. 等待策略

```bash
# 固定等待
uv run auvima wait 3

# 等待元素出现后再操作
uv run auvima navigate https://example.com --wait-for ".content-loaded"

# 检查元素是否可见
uv run auvima exec-js "
const el = document.querySelector('YOUR_SELECTOR');
el && el.offsetParent !== null ? 'visible' : 'not visible'
" --return-value
```

### 4. 错误处理

```bash
# 检查操作前先验证元素存在
uv run auvima exec-js "document.querySelector('.target-element') ? 'exists' : 'missing'" --return-value

# 如果元素存在才执行点击
uv run auvima exec-js "
const el = document.querySelector('.target-element');
if (el) {
  el.click();
  'clicked';
} else {
  'element not found';
}
" --return-value
```

---

## 最佳实践

1. ✅ **总是在操作后验证结果**
   ```bash
   uv run auvima click ".button"
   uv run auvima wait 1
   uv run auvima get-title  # 验证页面是否改变
   ```

2. ✅ **使用渐进式探索**
   ```bash
   # 先获取少量数据测试选择器
   uv run auvima exec-js "document.querySelector('.item')?.textContent" --return-value
   # 确认后再批量提取
   uv run auvima exec-js "Array.from(document.querySelectorAll('.item')).map(...)" --return-value
   ```

3. ✅ **适当的等待时间**
   - 页面导航: 2-3秒
   - AJAX请求: 1-2秒
   - 动画效果: 0.5-1秒

4. ✅ **关键步骤截图**
   ```bash
   uv run auvima screenshot step1_initial.png
   # ... 执行操作
   uv run auvima screenshot step2_after_click.png
   ```

5. ✅ **使用调试模式排查问题**
   ```bash
   uv run auvima --debug navigate https://example.com
   ```

---

## 注意事项

⚠️ **选择器可能随时变化** - 网站更新后需要重新探索DOM结构
⚠️ **网络延迟影响** - 根据实际网速调整wait时间
⚠️ **动态内容** - 某些内容需要滚动或交互才会加载
⚠️ **反爬机制** - 某些网站可能检测自动化行为

---

**最后更新**: 2025-11-18
