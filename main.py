#!/usr/bin/env python3
"""
视频文案分析工具 - 主入口脚本
用法: python main.py <视频URL或文件路径> [输出目录]
"""

import os
import sys
import subprocess
import re
from pathlib import Path

def get_script_dir():
    """获取脚本所在目录"""
    return Path(__file__).parent.resolve()

def get_venv_python():
    """获取虚拟环境中的 Python 路径"""
    venv_python = get_script_dir() / "venv" / "bin" / "python"
    if venv_python.exists():
        return str(venv_python)
    return sys.executable

def get_venv_ytdlp():
    """获取虚拟环境中的 yt-dlp 路径"""
    venv_ytdlp = get_script_dir() / "venv" / "bin" / "yt-dlp"
    if venv_ytdlp.exists():
        return str(venv_ytdlp)
    return "yt-dlp"

def is_url(path):
    """判断是否为 URL"""
    return path.startswith("http://") or path.startswith("https://")

def extract_video_id(url):
    """从 URL 提取视频 ID"""
    # B站
    bilibili_match = re.search(r'(BV[\w]+|av\d+)', url)
    if bilibili_match:
        return bilibili_match.group(1)
    
    # YouTube
    youtube_match = re.search(r'(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})', url)
    if youtube_match:
        return youtube_match.group(1)
    
    # 默认使用 URL 的哈希
    return hex(hash(url) & 0xFFFFFFFF)[2:]

def download_video(url, output_dir):
    """下载视频"""
    video_id = extract_video_id(url)
    output_template = str(output_dir / f"{video_id}.%(ext)s")
    
    cmd = [
        get_venv_ytdlp(),
        "-f", "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
        "--merge-output-format", "mp4",
        "-o", output_template,
        url
    ]
    
    print(f"📥 正在下载视频: {url}")
    print(f"   输出路径: {output_dir}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ 下载失败: {result.stderr}")
        return None
    
    # 查找下载的文件
    for ext in ["mp4", "mkv", "webm"]:
        video_file = output_dir / f"{video_id}.{ext}"
        if video_file.exists():
            print(f"✅ 视频下载成功: {video_file}")
            return video_file
    
    print("❌ 未找到下载的视频文件")
    return None

def transcribe_video(video_path, output_dir, model="medium", language="auto"):
    """使用 Whisper 转录视频"""
    video_path = Path(video_path)
    video_id = video_path.stem
    srt_path = output_dir / f"{video_id}.srt"
    
    script_path = get_script_dir() / "scripts" / "transcribe_audio.py"
    
    cmd = [
        get_venv_python(),
        str(script_path),
        str(video_path),
        str(srt_path),
        model,
        language,
        "cpu"  # 默认使用 CPU，MacOS 上更稳定
    ]
    
    print(f"🎤 正在转录视频: {video_path}")
    print(f"   使用模型: {model}, 语言: {language}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ 转录失败: {result.stderr}")
        if result.stdout:
            print(f"   输出: {result.stdout}")
        return None
    
    if srt_path.exists():
        print(f"✅ 转录成功: {srt_path}")
        return srt_path
    
    print("❌ 未找到生成的字幕文件")
    return None

def read_srt_as_text(srt_path):
    """读取 SRT 字幕并提取纯文本"""
    with open(srt_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 移除时间戳和序号，只保留文本
    lines = []
    for line in content.split("\n"):
        line = line.strip()
        # 跳过空行、序号和时间戳
        if not line:
            continue
        if line.isdigit():
            continue
        if "-->" in line:
            continue
        lines.append(line)
    
    return " ".join(lines)

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ["-h", "--help"]:
        print("用法: python main.py <视频URL或文件路径> [输出目录] [whisper模型] [语言]")
        print()
        print("参数:")
        print("  视频URL或文件路径  - B站/YouTube URL 或本地视频文件路径")
        print("  输出目录          - 可选，默认为 ~/video-analysis/")
        print("  whisper模型       - 可选，tiny/base/small/medium/large，默认 medium")
        print("  语言              - 可选，zh/en/auto，默认 auto")
        print()
        print("示例:")
        print("  python main.py https://www.bilibili.com/video/BVxxxx")
        print("  python main.py ./my_video.mp4 ./output medium zh")
        sys.exit(0 if len(sys.argv) > 1 else 1)
    
    input_path = sys.argv[1]
    output_dir = Path(sys.argv[2] if len(sys.argv) > 2 else os.path.expanduser("~/video-analysis"))
    model = sys.argv[3] if len(sys.argv) > 3 else "medium"
    language = sys.argv[4] if len(sys.argv) > 4 else "auto"
    
    # 创建输出目录
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("🎬 视频文案分析工具")
    print("=" * 60)
    
    # 阶段 1: 获取视频
    if is_url(input_path):
        video_path = download_video(input_path, output_dir)
        if not video_path:
            sys.exit(1)
    else:
        video_path = Path(input_path)
        if not video_path.exists():
            print(f"❌ 视频文件不存在: {video_path}")
            sys.exit(1)
        print(f"📁 使用本地视频: {video_path}")
    
    # 阶段 2: Whisper 转录
    srt_path = transcribe_video(video_path, output_dir, model, language)
    if not srt_path:
        sys.exit(1)
    
    # 阶段 3: 提取文本
    text_content = read_srt_as_text(srt_path)
    transcript_path = output_dir / f"{video_path.stem}_文字稿.md"
    
    with open(transcript_path, "w", encoding="utf-8") as f:
        f.write(f"# 视频语音转录文字稿\n\n")
        f.write(f"**视频来源**: {input_path}\n")
        f.write(f"**视频文件**: {video_path}\n")
        f.write(f"**转录模型**: Whisper {model}\n\n")
        f.write("---\n\n")
        f.write("## 完整文字稿\n\n")
        f.write(text_content)
        f.write("\n")
    
    print(f"✅ 文字稿已保存: {transcript_path}")
    
    # 完成报告
    print()
    print("=" * 60)
    print("✅ 视频文案分析完成！")
    print("=" * 60)
    print()
    print(f"📁 输出目录: {output_dir}")
    print()
    print("📄 生成文件:")
    print(f"   - {video_path.name} (视频)")
    print(f"   - {srt_path.name} (字幕)")
    print(f"   - {transcript_path.name} (文字稿)")
    print()
    print("💡 提示: 文字稿已准备好，可以进行三维度分析了！")

if __name__ == "__main__":
    main()
