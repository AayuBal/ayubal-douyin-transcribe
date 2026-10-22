# ayubal-douyin-transcribe

抖音短视频本地离线语音转写工具与 Agent Skill。

输入抖音分享链接或文本，工具通过 Playwright 抓取原声音频直链，利用本地 SenseVoice 模型进行 20 秒切片语音识别，输出按自然口播停顿分段的文字稿。

无需购买第三方数据接口，无需启动桌面端程序，可在终端直接执行，也可作为 Skill 配置给 Antigravity、Claude Code、Codex 等 Agent 调用。

---

## 工作流程

```mermaid
flowchart LR
    A[抖音分享链接 / 文案] --> B[Playwright 拦截音频地址]
    B --> C[下载原声 MP3]
    C --> D[FFmpeg 转为 16kHz WAV]
    D --> E[SenseVoice 20s 切片识别]
    E --> F[原始转写文本 / JSON]
    F --> G[Agent 语义校正与短句分段]
```

---

## 功能特点

- **完全本地运行**：语音识别由本地的 SenseVoice ONNX 模型完成，不依赖外部付费转写 API，无 Token 费用。
- **长音频 20 秒切片**：针对长视频按 20 秒滑动窗口分块推理，避免长音频单次解码导致的丢句漏字。
- **无 GUI 窗口**：全流程由 Python 脚本在后台无头运行，适合直接嵌入各类命令行 Agent 的自动化链路。
- **短句分段排版**：输出格式遵循移动端阅读习惯，每 1～2 句话独立成段，段落间空行，不增加概括性大纲与列表编号。
- **术语纠错指引**：在 Agent 规范中内置了针对网络热词与英文术语（如 `vibe coding`、`薄肌理论` 等）的语义校正要求。

---

## 环境准备

### 1. 安装基础依赖

需要 Python 3.10 及以上版本，以及系统 PATH 中可用的 `ffmpeg`。

```bash
# 安装 Python 库
pip install sherpa-onnx playwright

# 安装 Playwright 浏览器内核
playwright install msedge   # 或 playwright install chromium
```

### 2. 配置 SenseVoice 模型

脚本会自动在以下路径寻找模型文件（`model.onnx` 与 `tokens.txt`）：

1. 环境变量 `SENSE_VOICE_MODEL_DIR` 所指目录
2. `AppData/DouyinCreatorToolkit/models/asr/sense-voice`（若安装过相关工具箱）
3. `~/.cache/sherpa-onnx/sense-voice`
4. 本项目根目录下的 `models/sense-voice`

如本地未下载模型，可从 [sherpa-onnx 官方发布页](https://github.com/k2-fsa/sherpa-onnx/releases) 下载 SenseVoice-Small ONNX 格式模型解压至上述任意目录。

---

## 使用方法

### 命令行运行

```bash
# 1. 直接传入短链接或分享文本
python scripts/douyin_transcribe.py "https://v.douyin.com/xxxx/"

# 2. 从标准输入读取（适合管道传递）
echo "https://v.douyin.com/xxxx/" | python scripts/douyin_transcribe.py --stdin

# 3. 输出结构化 JSON（包含分段详情与作者、标题元数据）
python scripts/douyin_transcribe.py "https://v.douyin.com/xxxx/" --json
```

---

## 接入 Agent

本项目可作为技能供支持 Skill 架构的 Agent 调用：

### 1. Google Antigravity
将本项目放置或链接在 `~/.gemini/config/skills/ayubal-douyin-transcribe`。
对话中输入视频链接或直接要求“转写这个抖音视频”，Agent 会按 `SKILL.md` 规则执行转写并完成自然分段。

### 2. Claude Code
将项目引入后，Claude 会在处理抖音链接时调用 `scripts/douyin_transcribe.py --json` 提取文本，并按预设格式交付。

### 3. OpenAI Codex / Cursor
作为终端工具放入工作区或全局 Skill 目录即可随时通过 CLI 唤起。

---

## 输出排版样式

文字稿交付采用短句呼吸感排版，示例：

```text
什么薄肌理论、大学理论都不如我的摆摊理论。

但凡你还在上大学，毕业想找份双休不加班还能月薪过万的好工作，就一定要遵循我的摆摊理论。

不管是摆摊卖烧烤、卖炒饭，还是手抓饼、烤冷面、淀粉肠、酱香饼都可以。

要我说你就去摆摊，别光搞什么大创赛，或者整什么 vibe coding、拿 AI 做个软件做个网页，那些在摆摊面前都不够看的。

你想想你去参加那大创赛，那不就是 PPT 大赛嘛，能有几个有真实的产品、真实的实操、有真实的盈利啊？
```

---

## 许可证

本项目采用 [MIT License](./LICENSE) 授权。
