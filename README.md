# AuViMa - Automated Video Maker

基于Claude Code的自动化视频制作pipeline，通过AI驱动实现从主题到成品视频的全流程自动化。

## 项目概述

AuViMa是一个自动化视频生产系统，专注于生成4类特定内容的视频：

### 支持的内容类型

1. **资讯深度分析** - 基于核心观点的论证型内容
   - 示例：`"AI将如何改变教育行业 - 观点：个性化学习是核心"`

2. **GitHub项目解析** - 开源项目的深度介绍
   - 示例：`"分析 https://github.com/langchain-ai/langchain"`

3. **产品介绍** - 软件产品的功能演示
   - 示例：`"介绍 Notion 的核心功能"`

4. **MVP开发演示** - 从想法到产品的开发过程
   - 示例：`"用React开发一个番茄钟应用"`

系统能够自动完成：
1. 根据主题类型定向收集信息
2. 规划分镜头脚本
3. 录制视频片段
4. 生成配音音频
5. 合成最终视频

## 系统架构

### 核心工作流程

```
Pipeline主控 → Chrome启动 → 信息收集 → 分镜规划 → [循环生成] → 素材评估 → 视频合成 → 完成
```

### Pipeline主控流程

```python
python pipeline_master.py "<主题>" <项目名>
```

Pipeline将依次执行以下阶段：

#### 阶段0: 环境准备
- **执行者**：Pipeline
- **任务**：启动Chrome CDP (端口9222)
- **输出**：Chrome进程持久运行

#### 阶段1: 信息收集 (`/auvima.start`)
- **执行者**：Claude Code CLI
- **输入**：视频主题
- **信息源**：Chrome CDP、Git、本地文件
- **输出**：
  - `research/report.json` - 信息报告
  - `research/screenshots/` - 截图素材
  - `start.done` - 完成标记

#### 阶段2: 分镜规划 (`/auvima.storyboard`)
- **执行者**：Claude Code CLI
- **输入**：`research/report.json`
- **输出**：
  - `shots/shot_xxx.json` - 分镜序列
  - `storyboard.done` - 完成标记

#### 阶段3: 视频生成循环 (`/auvima.generate`)
**Pipeline控制的循环流程**：

```
for each shot_xxx.json:
    ├── 录制视频
    │   └── 生成 shot_xxx.mp4
    ├── 生成音频
    │   └── 生成 shot_xxx_audio.mp3
    ├── 验证同步
    │   └── 确保 video_duration ≥ audio_duration
    └── 创建标记
        └── 生成 shot_xxx.done
```

- **执行者**：Claude Code CLI (循环调用)
- **完成标记**：`generate.done`

#### 阶段4: 素材评估 (`/auvima.evaluate`)
- **执行者**：Claude Code CLI
- **任务**：
  - 检查所有clips完整性
  - **重点验证音视频时长匹配**
  - 识别需要修复的问题
- **输出**：
  - `evaluation_report.json` - 评估报告
  - `evaluate.done` - 完成标记

#### 阶段5: 视频合成 (`/auvima.merge`)
- **执行者**：Claude Code CLI
- **任务**：
  - 按编号顺序合并视频
  - 合成音频轨道
  - 生成最终视频
- **输出**：
  - `outputs/final_output.mp4` - 最终视频
  - `merge.done` - 完成标记

#### 阶段6: 清理环境
- **执行者**：Pipeline
- **任务**：关闭Chrome，清理临时文件

## 目录结构

```
AuViMa/
├── README.md                   # 项目说明
├── .claude/
│   └── commands/              # Claude Code命令配置
│       ├── auvima_start.md    # 信息收集命令
│       ├── auvima_storyboard.md # 分镜规划命令
│       ├── auvima_generate.md # 视频生成命令
│       ├── auvima_evaluate.md # 素材评估命令
│       └── auvima_merge.md    # 视频合成命令
├── src/                        # 核心Python脚本
│   ├── chrome_cdp_launcher_v2.py  # Chrome CDP启动器
│   ├── pipeline_master.py     # Pipeline主控制器
│   └── .venv/                     # Python虚拟环境
├── scripts/                    # Shell脚本工具
│   ├── cdp_*.sh               # Chrome CDP操作脚本
│   └── start_chrome_cdp.sh    # Chrome启动脚本（已废弃）
├── projects/                   # 项目工作目录
│   └── <project_name>/
│       ├── research/          # 信息收集
│       │   ├── report.json
│       │   └── screenshots/
│       ├── shots/            # 分镜脚本
│       │   └── shot_xxx.json
│       ├── clips/            # 视频片段
│       └── logs/             # 执行日志
├── outputs/                    # 最终输出
├── templates/                  # 模板文件
└── chrome_profile/            # Chrome用户配置
```

## 技术栈

- **浏览器控制**：Chrome DevTools Protocol (CDP)
- **视频录制**：ffmpeg + AVFoundation (macOS)
- **脚本语言**：Python 3.12 + Shell
- **音频生成**：火山引擎声音克隆API（待集成）
- **AI助手**：Claude Code

## 已完成功能 ✅

### 基础设施
- [x] Chrome CDP启动器（1280x960窗口，位置20,20）
- [x] Chrome profile管理
- [x] Python虚拟环境配置（uv管理）
- [x] ffmpeg录制测试

### Chrome CDP脚本集
- [x] 基础操作脚本（navigate, get_content, screenshot等）
- [x] 页面交互脚本（click, scroll, wait等）
- [x] 视觉效果脚本（highlight, spotlight, annotate等）
- [x] 清理脚本（clear_effects）

### 命令系统
- [x] `/auvima.start` 命令配置（信息收集）
- [x] `/auvima.storyboard` 命令配置（分镜规划）
- [x] `/auvima.generate` 命令配置（视频生成）
- [x] `/auvima.evaluate` 命令配置（素材评估）
- [x] `/auvima.merge` 命令配置（视频合成）

### 自动化框架
- [x] Pipeline控制器设计
- [x] 分镜JSON模板
- [x] 项目目录结构

## 待完成功能 📝

### 核心功能
- [ ] `/auvima.start` 实际实现脚本
- [ ] `/auvima.storyboard` 实际实现脚本
- [ ] `/auvima.generate` 实际实现脚本
- [ ] `/auvima.evaluate` 实际实现脚本
- [ ] `/auvima.merge` 实际实现脚本
- [ ] Pipeline主控制器集成
- [ ] Claude Code CLI集成
- [ ] 视频录制功能集成
- [ ] 音频生成接口（火山引擎API）
- [ ] 音视频同步验证

### 增强功能
- [ ] 代码展示录制
- [ ] 本地静态页面生成
- [ ] 多音频片段支持（shot_001_1.mp3, shot_001_2.mp3）
- [ ] 进度监控和报告
- [ ] 错误恢复机制

## 使用流程

### 一键启动Pipeline

```bash
cd /Users/chagee/Repos/AuViMa/src
source .venv/bin/activate

# 启动完整pipeline
python pipeline_master.py "<主题>" <项目名>
```

### 示例命令

```bash
# 类型1：资讯深度分析
python pipeline_master.py "AI教育革命 - 观点：个性化学习将取代传统课堂" ai_education

# 类型2：GitHub项目解析  
python pipeline_master.py "https://github.com/openai/whisper" whisper_intro

# 类型3：产品介绍
python pipeline_master.py "Notion产品功能介绍" notion_demo

# 类型4：MVP开发演示
python pipeline_master.py "React开发待办事项应用MVP" todo_mvp
```

### Pipeline执行流程

1. **自动启动Chrome CDP**（端口9222）
2. **信息收集**（/auvima.start）→ start.done
3. **分镜规划**（/auvima.storyboard）→ storyboard.done
4. **循环生成视频**（/auvima.generate × N）→ generate.done
5. **素材评估**（/auvima.evaluate）→ evaluate.done
6. **视频合成**（/auvima.merge）→ merge.done
7. **环境清理**，输出最终视频

整个流程完全自动化，通过.done文件进行阶段同步。

## 分镜JSON示例

```json
{
  "shot_id": "shot_001",
  "duration": 10,
  "type": "browser_recording",
  "description": "展示GitHub首页",
  "actions": [
    {
      "action": "navigate",
      "url": "https://github.com",
      "wait": 3
    },
    {
      "action": "scroll",
      "direction": "down",
      "pixels": 500,
      "wait": 2
    }
  ],
  "narration": "GitHub是全球最大的代码托管平台...",
  "audio_config": {
    "voice": "default",
    "speed": 1.0
  },
  "source_reference": "https://github.com/about"
}
```

## 环境要求

- macOS（用于AVFoundation录制）
- Chrome浏览器
- Python 3.12+
- ffmpeg 8.0+
- uv包管理器
- 屏幕录制权限（系统设置 > 隐私与安全性 > 屏幕录制）

## 依赖安装

```bash
# Python依赖
cd src
source .venv/bin/activate
uv pip install -r requirements.txt

# 系统依赖（如未安装）
brew install ffmpeg
brew install uv
```

## 开发规范

1. **脚本位置**：
   - 命令实现脚本放在 `scripts/`
   - Python核心脚本放在 `src/`

2. **文件命名**：
   - 视频片段：`shot_xxx.mp4`（基于时间戳）
   - 音频片段：`shot_xxx_audio.mp3` 或 `shot_xxx_1.mp3`
   - 截图文件：必须使用绝对路径保存

3. **Chrome CDP使用**：
   - prepare阶段：仅用于信息收集
   - generate阶段：加入视觉引导效果

## 注意事项

1. Chrome必须通过CDP启动器运行，保持9222端口可用
2. 录制前需要授权屏幕录制权限
3. 所有截图必须使用绝对路径
4. 视频长度必须大于等于音频总长度
5. 每个分镜完成后必须创建`.completed`标记文件

## 项目状态

🚧 **开发中** - 基础架构已完成，核心功能实现中

---

Created by Claude Code with Human
2024-11