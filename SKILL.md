---
name: ayubal-douyin-transcribe
description: >-
  抖音短视频离线语音转写与逐字稿提炼 Skill。完全脱离第三方付费 API 和桌面 GUI 窗口，
  纯本地通过 Playwright + FFmpeg + SenseVoice 离线大模型完成原声音频抓取与 20s 滑动窗口高精度语音识别。
  交付小红书/社交媒体风格的短句自然呼吸感分段文字稿，并自动纠正网络热梗与技术黑话。
metadata:
  triggers:
    - 抖音转文字
    - 抖音转写
    - 抖音文字稿
    - 提取抖音文案
    - 提取台词
    - 视频转写
    - 抖音视频文案
---

# 抖音本地离线语音转写 (ayubal-douyin-transcribe)

本 Skill 专为从抖音分享链接/文案中提取高清口播逐字稿而设计。
核心特色：**彻底脱离任何外部桌面端 GUI 软件、完全免费、零 Token/API 消耗、纯本地离线转写**。同时适用于 **Antigravity、Claude Code、Codex、Cursor、Qwen Code** 等所有兼容通用 Skill 的智能体系统。

---

## 🛠️ 底层环境与依赖

1. **Python 运行环境**：系统 Python 3.10+（需安装 `sherpa-onnx`、`playwright`）。
2. **离线语音大模型**：SenseVoice ONNX（支持自动从本地 AppData、用户缓存或 `SENSE_VOICE_MODEL_DIR` 读取）。
3. **音频转码**：系统配置的 `ffmpeg`。

---

## 🚀 执行流程 (Standard Operating Procedure)

当用户输入包含抖音短链接（`v.douyin.com/...`）或分享文案，并要求提取文字稿/排版时，按以下步骤执行：

### 第一步：调用本地 CLI 脚本提取原始逐字稿

运行本地脚本（支持直接传入链接或通过标准输入）：

```bash
python C:\Users\hzy\.gemini\config\skills\ayubal-douyin-transcribe\scripts\douyin_transcribe.py "<抖音链接或分享文案>" --json
```

或者使用相对路径（在 Skill 目录下）：
```bash
python scripts/douyin_transcribe.py "<抖音链接或分享文案>" --json
```

脚本将自动执行以下操作：
1. 自动跟随短链重定向，拦截抖音官方 Web API 取得原声最高码率音频直链；
2. 自动下载临时音频并用 FFmpeg 转换成标准的 16kHz 单声道 PCM WAV；
3. 加载本地 SenseVoice 模型，以 20 秒滑动窗口无缝切片识别，防止长音频丢字断句；
4. 输出包含视频元数据（作者、标题）和各时间段切片的 JSON。

---

### 第二步：智能体语义精修与排版交付（关键铁律）

拿到原始识别文本后，**任何智能体（Gemini、Claude、GPT 等）必须严格按照以下排版铁律进行交付**：

#### 1. 严格遵循“短句呼吸感”分段
* ❌ **严禁输出一整块密密麻麻的万字长段**。
* ❌ **严禁过度加工成带加粗的小标题、多级大纲摘要（如“一、背景 二、拆解”）或编号列表（1. 2. 3.）**，除非用户有明确要求。
* ✅ **必须采用适合手机移动端阅读的呼吸节奏**：每 1～2 句话独立成段，段落之间空一行，忠实保留口播原貌。

#### 2. 网络热梗与专业黑话智能纠错
SenseVoice 为通用语音大模型，对最新的网络梗、英文缩写或行业术语可能会存在同音别字，智能体需结合语境主动纠偏：
* 编程/AI 场景：将 `we coding`、`老外co` 纠正为 `vibe coding` 等；
* 健身/流行梗：将 `搏击理论` 纠正为 `薄肌理论` 等；
* 职场/商业场景：将 `大成` 纠正为 `大厂`，将 `海康` 纠正为 `HC (Headcount)` 等。

---

## 📋 交付模板范例

交付给用户时的标准格式：

```markdown
作者：[视频作者]
标题：[视频标题]

***

[第 1~2 句话]

[第 3~4 句话]

[自然承接的句子]

...

[结尾 Punchline 句子]
```
