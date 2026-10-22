#!/usr/bin/env python3
"""
ayubal-douyin-transcribe: 抖音短视频离线语音转写 CLI 工具
作者: ayubal (https://github.com/AayuBal)
基于 Playwright + FFmpeg + sherpa-onnx (SenseVoice) 离线大模型，实现无付费 API、纯本地高精度语音转写。
"""

import sys
import os
import re
import json
import argparse
import tempfile
import urllib.request
import subprocess
import wave
import struct
from pathlib import Path

def find_sense_voice_model() -> tuple[str, str]:
    """寻找本地 SenseVoice 模型路径 (model.onnx, tokens.txt)"""
    candidate_dirs = []
    
    if os.environ.get("SENSE_VOICE_MODEL_DIR"):
        candidate_dirs.append(Path(os.environ["SENSE_VOICE_MODEL_DIR"]))
        
    candidate_dirs.extend([
        Path(os.environ.get("APPDATA", "")) / "DouyinCreatorToolkit" / "models" / "asr" / "sense-voice",
        Path.home() / ".cache" / "sherpa-onnx" / "sense-voice",
        Path.home() / ".local" / "share" / "DouyinCreatorToolkit" / "models" / "asr" / "sense-voice",
        Path(__file__).resolve().parent.parent / "models" / "sense-voice"
    ])
    
    for c_dir in candidate_dirs:
        model_file = c_dir / "model.onnx"
        tokens_file = c_dir / "tokens.txt"
        if model_file.exists() and tokens_file.exists():
            return str(model_file), str(tokens_file)
            
    raise FileNotFoundError(
        "未在本地找到 SenseVoice 模型文件 (model.onnx 与 tokens.txt)。\n"
        "请确保模型位于 AppData/DouyinCreatorToolkit/models/asr/sense-voice 或通过 SENSE_VOICE_MODEL_DIR 指定路径。"
    )

def extract_share_url(text: str) -> str:
    """从分享文本中提取有效链接"""
    urls = re.findall(r'https?://[^\s]+', text)
    if not urls:
        raise ValueError("输入内容中未检测到有效的 HTTP/HTTPS 链接！")
    return urls[0]

def capture_douyin_video_info(url: str, headless: bool = True) -> dict:
    """使用 Playwright 拦截抖音 Web Detail API 获取真实视频和音频地址"""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise ImportError("未检测到 playwright 依赖，请运行: pip install playwright")
        
    aweme_details = []

    def handle_response(response):
        if 'aweme/v1/web/aweme/detail' in response.url:
            try:
                body = response.text()
                data = json.loads(body)
                if data.get("aweme_detail"):
                    aweme_details.append(data["aweme_detail"])
            except Exception:
                pass

    with sync_playwright() as p:
        browser = None
        # 优先尝试 Edge，其次通用 Chromium
        try:
            browser = p.chromium.launch(channel="msedge", headless=headless)
        except Exception:
            try:
                browser = p.chromium.launch(headless=headless)
            except Exception as e:
                raise RuntimeError(f"Playwright 浏览器启动失败: {e}")

        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        page = context.new_page()
        page.on("response", handle_response)

        try:
            page.goto(url, wait_until="domcontentloaded", timeout=20000)
        except Exception:
            pass

        # 等待数据包返回
        page.wait_for_timeout(5000)
        browser.close()

    if not aweme_details:
        raise RuntimeError("未能从抖音页面拦截到视频详情数据 (aweme_detail)，请检查网络或链接是否有效。")

    detail = aweme_details[0]
    author = detail.get("author", {}).get("nickname", "未知作者")
    desc = detail.get("desc", "").strip()
    aweme_id = detail.get("aweme_id", "")

    # 获取音频直链（优先原声 MP3，无则回退到视频播放源）
    music_urls = detail.get("music", {}).get("play_url", {}).get("url_list", [])
    video_urls = detail.get("video", {}).get("play_addr", {}).get("url_list", [])

    audio_url = music_urls[0] if music_urls else (video_urls[0] if video_urls else "")
    if not audio_url:
        raise RuntimeError("未能获取到视频/音频的有效播放直链。")

    return {
        "aweme_id": aweme_id,
        "author": author,
        "title": desc,
        "audio_url": audio_url,
        "video_url": video_urls[0] if video_urls else ""
    }

def download_file(url: str, dest_path: str):
    """下载音频文件"""
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    )
    with urllib.request.urlopen(req, timeout=30) as resp, open(dest_path, "wb") as f:
        f.write(resp.read())

def convert_to_wav(input_path: str, output_wav: str):
    """通过 ffmpeg 将音频转换为 16kHz 单声道 PCM 16-bit WAV"""
    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le",
        output_wav
    ]
    res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"FFmpeg 转码失败: {res.stderr}")

def transcribe_wav(wav_path: str, model_path: str, tokens_path: str, chunk_duration_s: float = 20.0) -> list[dict]:
    """使用 sherpa-onnx SenseVoice 模型分块切片转写"""
    try:
        import sherpa_onnx
    except ImportError:
        raise ImportError("未检测到 sherpa_onnx 依赖，请运行: pip install sherpa-onnx")

    with wave.open(wav_path, "rb") as wav:
        sample_rate = wav.getframerate()
        n_frames = wav.getnframes()
        raw_data = wav.readframes(n_frames)

    samples_raw = struct.unpack(f"<{n_frames}h", raw_data)
    all_samples = [float(s) / 32768.0 for s in samples_raw]
    total_duration = n_frames / sample_rate

    recognizer = sherpa_onnx.OfflineRecognizer.from_sense_voice(
        model=model_path,
        tokens=tokens_path,
        num_threads=4,
        provider="cpu",
        language="auto",
        use_itn=True,
        debug=False,
    )

    t = 0.0
    segments = []

    while t < total_duration:
        t_end = min(t + chunk_duration_s, total_duration)
        idx_start = int(t * sample_rate)
        idx_end = int(t_end * sample_rate)
        chunk = all_samples[idx_start:idx_end]

        stream = recognizer.create_stream()
        stream.accept_waveform(sample_rate, chunk)
        recognizer.decode_stream(stream)
        text = stream.result.text.strip()

        if text:
            segments.append({
                "start": round(t, 2),
                "end": round(t_end, 2),
                "text": text
            })

        t += chunk_duration_s

    return segments

def main():
    parser = argparse.ArgumentParser(description="ayubal-douyin-transcribe: 抖音视频本地离线语音转写 CLI 工具")
    parser.add_argument("input", nargs="?", help="抖音分享链接或完整分享文案")
    parser.add_argument("--stdin", action="store_true", help="从标准输入读取分享内容")
    parser.add_argument("--json", action="store_true", help="以 JSON 格式输出结果")
    parser.add_argument("--keep-audio", action="store_true", help="保留下载的音频文件不删除")

    args = parser.parse_args()

    # 获取输入文案
    raw_text = ""
    if args.stdin:
        raw_text = sys.stdin.read().strip()
    elif args.input:
        raw_text = args.input.strip()
    else:
        parser.print_help()
        sys.exit(1)

    if not raw_text:
        print("错误：未提供任何抖音链接或输入内容！", file=sys.stderr)
        sys.exit(1)

    url = extract_share_url(raw_text)

    # 1. 查找 SenseVoice 模型
    model_path, tokens_path = find_sense_voice_model()

    # 2. 抓取视频信息与音频直链
    info = capture_douyin_video_info(url)

    # 3. 下载与音频预处理
    with tempfile.TemporaryDirectory() as tmp_dir:
        download_ext = ".mp3" if ".mp3" in info["audio_url"] else ".mp4"
        raw_audio_file = os.path.join(tmp_dir, f"source{download_ext}")
        wav_file = os.path.join(tmp_dir, "audio_16k.wav")

        download_file(info["audio_url"], raw_audio_file)
        convert_to_wav(raw_audio_file, wav_file)

        # 4. SenseVoice 切片转写
        segments = transcribe_wav(wav_file, model_path, tokens_path, chunk_duration_s=20.0)

        full_raw_text = "".join(seg["text"] for seg in segments)

        if args.json:
            result = {
                "status": "success",
                "author": info["author"],
                "title": info["title"],
                "aweme_id": info["aweme_id"],
                "audio_url": info["audio_url"],
                "segments": segments,
                "full_raw_text": full_raw_text
            }
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"作者: {info['author']}")
            print(f"标题: {info['title']}")
            print("-" * 50)
            print("【原始转写文本】:")
            print(full_raw_text)

if __name__ == "__main__":
    main()
