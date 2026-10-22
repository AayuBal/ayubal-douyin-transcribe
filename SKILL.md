---
name: ayubal-douyin-transcribe
description: >-
  抖音短视频离线语音转写与逐字稿提炼 Skill。不依赖第三方付费 API 和桌面 GUI 窗口，
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

从抖音分享链接或分享文案中提取口播逐字稿，不依赖第三方付费 API 和桌面端图形软件。
适用于 Antigravity、Claude Code、Codex、Cursor、Qwen Code 等支持 CLI 脚本调用的智能体系统。

---

## 环境依赖

1. **Python 运行环境**：Python 3.10+，已安装 `sherpa-onnx` 与 `playwright`。
2. **离线语音模型**：SenseVoice ONNX，自动识别本地 AppData、用户缓存或 `SENSE_VOICE_MODEL_DIR` 指定路径。
3. **音频转码**：系统 PATH 中的 `ffmpeg`。

---

## 执行流程

当用户提供包含抖音短链接（`v.douyin.com/...`）或分享文案，并要求提取文字稿时，按以下步骤处理：

### 第一步：运行本地 CLI 脚本提取原始文本

在终端运行脚本（支持参数传入或标准输入）：

```bash
python C:\Users\hzy\.gemini\config\skills\ayubal-douyin-transcribe\scripts\douyin_transcribe.py "<抖音链接或分享文案>" --json
```

或者使用相对路径：
```bash
python scripts/douyin_transcribe.py "<抖音链接或分享文案>" --json
```

脚本执行动作：
1. 跟随短链接重定向，拦截抖音官方 Web API 取得原声音频直链；
2. 下载临时音频并调用 FFmpeg 转为 16kHz 单声道 PCM WAV；
3. 加载本地 SenseVoice 模型，以 20 秒滑动窗口切片识别，防止长音频丢失词句；
4. 输出包含作者、标题和时间切片的 JSON 数据。

---

### 第二步：排版与纠错

取得原始识别文本后，按以下规则完成交付：

#### 1. 短句分段
- 不输出未经换行的整块长段落。
- 不添加概括性小标题、多级大纲或编号列表，除非用户明确要求。
- 每 1～2 句话单独成段，段落之间空一行，符合移动端阅读视线。

#### 2. 术语与热词纠错
SenseVoice 处理个别生僻词或网络用语时可能出现同音字偏差，需结合语境校对：
- 编程场景：将 `we coding`、`老外co` 改为 `vibe coding`。
- 流行用语：将 `搏击理论` 改为 `薄肌理论`。
- 职场术语：将 `大成` 改为 `大厂`，将 `海康` 改为 `HC (Headcount)` 等。

---

## 交付格式

```markdown
作者：[视频作者]
标题：[视频标题]

***

[第 1~2 句话]

[第 3~4 句话]

[自然承接的句子]

...

[结尾句子]
```
