import re
import json
from pathlib import Path


def is_douyin_url(url: str) -> bool:
    patterns = [
        r"v\.douyin\.com",
        r"www\.douyin\.com",
        r"m\.douyin\.com",
        r"douyin\.com/video/",
        r"douyin\.com/jingxuan",
    ]
    return any(re.search(p, url) for p in patterns)


def extract_video_id(url: str) -> str:
    # B站 BV 号
    m = re.search(r"(BV[\w]+|av\d+)", url)
    if m:
        return m.group(1)
    # YouTube
    m = re.search(r"(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})", url)
    if m:
        return m.group(1)
    # 抖音: 从 URL 提取数字 ID
    m = re.search(r"/video/(\d+)", url)
    if m:
        return m.group(1)
    # 抖音短链接: 用 URL 哈希
    return hex(hash(url) & 0xFFFFFFFF)[2:]


def get_output_path(output_dir: Path, video_id: str, suffix: str) -> Path:
    return output_dir / suffix


def read_srt_as_text(srt_path: str) -> str:
    """读取 SRT 字幕文件，提取纯文本"""
    with open(srt_path, "r", encoding="utf-8") as f:
        content = f.read()

    lines = []
    for line in content.split("\n"):
        line = line.strip()
        if not line or line.isdigit() or "-->" in line:
            continue
        lines.append(line)

    return " ".join(lines)


def format_sse(event: dict) -> str:
    """将字典格式化为 SSE 文本"""
    event_type = event.get("event", "message")
    data = json.dumps(event.get("data", {}), ensure_ascii=False)
    return f"event: {event_type}\ndata: {data}\n\n"


def make_progress_event(stage: int, stage_name: str, status: str, progress_pct: int, message: str) -> dict:
    return {
        "event": "progress",
        "data": {
            "stage": stage,
            "stage_name": stage_name,
            "status": status,
            "progress_pct": progress_pct,
            "message": message,
        },
    }


def make_stage_result_event(stage: int, stage_name: str, output_file: str, content: str) -> dict:
    return {
        "event": "stage_result",
        "data": {
            "stage": stage,
            "stage_name": stage_name,
            "output_file": output_file,
            "content": content,
        },
    }


def make_error_event(stage: int, message: str) -> dict:
    return {
        "event": "error",
        "data": {"stage": stage, "message": message},
    }


def make_complete_event(job_id: str, outputs: dict) -> dict:
    return {
        "event": "complete",
        "data": {"job_id": job_id, "outputs": outputs},
    }
