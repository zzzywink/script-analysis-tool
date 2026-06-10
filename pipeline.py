"""5 阶段视频文案分析流水线 —— 异步生成器，产出 SSE 事件"""

import sys
import subprocess
import re
from pathlib import Path
from typing import AsyncGenerator

# Windows 下强制 UTF-8 输出，避免 emoji 等字符 GBK 编码崩溃
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from config import SKILL_SCRIPTS_DIR, DEFAULT_OUTPUT_DIR, DEEPSEEK_MODEL
from utils import (
    is_douyin_url,
    extract_video_id,
    get_output_path,
    read_srt_as_text,
    make_progress_event,
    make_stage_result_event,
    make_error_event,
    make_complete_event,
)
from prompts import (
    TEXT_CORRECTION_SYSTEM,
    get_correction_user_prompt,
    ANALYSIS_SYSTEM,
    get_analysis_user_prompt,
    STRUCTURED_SYSTEM,
    get_structured_user_prompt,
    call_deepseek,
)

# 将 skill scripts 加入 sys.path，以便直接 import
sys.path.insert(0, str(SKILL_SCRIPTS_DIR))


async def run_pipeline(
    video_url: str,
    api_key: str,
    output_dir_str: str = "",
    base_url: str = "https://api.deepseek.com/v1",
) -> AsyncGenerator[dict, None]:
    """
    执行完整的 5 阶段流水线，产出 SSE 事件字典。

    Args:
        video_url: 视频链接
        api_key: DeepSeek API Key
        output_dir_str: 输出目录（留空使用默认）
        base_url: API 地址
    """
    output_dir = Path(output_dir_str) if output_dir_str else DEFAULT_OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    video_id = extract_video_id(video_url)

    # 同一次分析的文件放在同一个子文件夹里
    output_dir = output_dir / video_id
    output_dir.mkdir(parents=True, exist_ok=True)

    video_path = None
    srt_path = None
    text_content = ""
    analysis_content = ""

    # ================================================================
    # 阶段 1: 下载视频 (0-20%)
    # ================================================================
    yield make_progress_event(1, "下载视频", "running", 5, "正在连接视频源...")

    try:
        if is_douyin_url(video_url):
            video_path = output_dir / f"{video_id}.mp4"
            yield make_progress_event(1, "下载视频", "running", 10, "识别为抖音链接，使用专用下载器...")

            from download_douyin import download_douyin_video
            success = download_douyin_video(video_url, str(video_path))
            if not success or not video_path.exists() or video_path.stat().st_size == 0:
                yield make_error_event(1, "抖音视频下载失败，请检查链接是否有效")
                return
        else:
            video_path = output_dir / f"{video_id}.mp4"
            yield make_progress_event(1, "下载视频", "running", 10, f"使用 yt-dlp 下载 (B站/YouTube)...")

            cmd = [
                "yt-dlp",
                "--merge-output-format", "mp4",
                "-o", str(video_path),
                "--no-playlist",
                video_url,
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)

            if result.returncode != 0:
                yield make_error_event(1, f"视频下载失败: {result.stderr[:300] if result.stderr else '未知错误'}")
                return

        if not video_path or not video_path.exists():
            yield make_error_event(1, "视频下载失败：未找到下载文件")
            return

        file_size_mb = video_path.stat().st_size / (1024 * 1024)
        yield make_progress_event(1, "下载视频", "done", 20, f"视频下载完成 ({file_size_mb:.1f} MB)")

    except subprocess.TimeoutExpired:
        yield make_error_event(1, "视频下载超时")
        return
    except Exception as e:
        yield make_error_event(1, f"视频下载异常: {str(e)}")
        return

    # ================================================================
    # 阶段 2: 字幕提取 (20-40%)
    # ================================================================
    srt_path = output_dir / f"{video_id}.srt"
    yield make_progress_event(2, "字幕提取", "running", 22, "正在使用 FunASR 进行语音转录...（首次运行需下载约 2-3GB 模型）")

    try:
        from extract_subtitle_funasr import extract_with_funasr

        yield make_progress_event(2, "字幕提取", "running", 30, "FunASR 转录中，请耐心等待...")

        success = extract_with_funasr(str(video_path.resolve()), str(srt_path.resolve()))

        if not success or not srt_path.exists() or srt_path.stat().st_size == 0:
            yield make_error_event(2, "字幕提取失败：FunASR 转录未产生有效输出")
            return

        srt_size_kb = srt_path.stat().st_size / 1024
        yield make_progress_event(2, "字幕提取", "done", 40, f"字幕提取完成 ({srt_size_kb:.1f} KB)")

    except ImportError as e:
        yield make_error_event(2, f"FunASR 未安装或导入失败: {str(e)}")
        return
    except Exception as e:
        yield make_error_event(2, f"字幕提取异常: {str(e)}")
        return

    # ================================================================
    # 阶段 3: 文稿校正 (40-60%) — DeepSeek API
    # ================================================================
    yield make_progress_event(3, "文稿校正", "running", 42, "正在读取字幕文件...")

    try:
        raw_text = read_srt_as_text(str(srt_path))
        if not raw_text.strip():
            yield make_error_event(3, "字幕内容为空，无法进行文稿校正")
            return

        yield make_progress_event(3, "文稿校正", "running", 48, "正在调用 AI 进行文稿校正...")

        corrected = await call_deepseek(
            system_prompt=TEXT_CORRECTION_SYSTEM,
            user_message=get_correction_user_prompt(raw_text, video_id),
            api_key=api_key,
            temperature=0.3,
            base_url=base_url,
            model=DEEPSEEK_MODEL,
        )

        text_content = corrected or ""
        text_path = get_output_path(output_dir, video_id, "文字稿.md")
        text_path.write_text(text_content, encoding="utf-8")

        yield make_progress_event(3, "文稿校正", "done", 60, "文稿校正完成")
        yield make_stage_result_event(3, "文稿校正", str(text_path), text_content)

    except Exception as e:
        yield make_error_event(3, f"文稿校正失败: {str(e)}")
        return

    # ================================================================
    # 阶段 4: 三维度分析 (60-85%) — DeepSeek API
    # ================================================================
    yield make_progress_event(4, "三维度分析", "running", 62, "正在调用 AI 进行三维度综合分析...")

    try:
        analysis = await call_deepseek(
            system_prompt=ANALYSIS_SYSTEM,
            user_message=get_analysis_user_prompt(text_content, video_id),
            api_key=api_key,
            temperature=0.7,
            base_url=base_url,
            model=DEEPSEEK_MODEL,
        )

        analysis_content = analysis or ""
        analysis_path = get_output_path(output_dir, video_id, "分析报告.md")
        analysis_path.write_text(analysis_content, encoding="utf-8")

        yield make_progress_event(4, "三维度分析", "done", 85, "三维度分析完成")
        yield make_stage_result_event(4, "三维度分析", str(analysis_path), analysis_content)

    except Exception as e:
        yield make_error_event(4, f"三维度分析失败: {str(e)}")
        return

    # ================================================================
    # 阶段 5: 结构化文字稿 (85-100%) — DeepSeek API
    # ================================================================
    yield make_progress_event(5, "结构化文字稿", "running", 87, "正在调用 AI 生成结构化文字稿...")

    try:
        # 提取分析报告中的叙事结构部分（减少 token 消耗）
        narrative_section = _extract_narrative_section(analysis_content)

        structured = await call_deepseek(
            system_prompt=STRUCTURED_SYSTEM,
            user_message=get_structured_user_prompt(text_content, narrative_section, video_id),
            api_key=api_key,
            temperature=0.5,
            base_url=base_url,
            model=DEEPSEEK_MODEL,
        )

        structured_content = structured or ""
        structured_path = get_output_path(output_dir, video_id, "结构化文字稿.md")
        structured_path.write_text(structured_content, encoding="utf-8")

        yield make_progress_event(5, "结构化文字稿", "done", 100, "全部完成！")
        yield make_stage_result_event(5, "结构化文字稿", str(structured_path), structured_content)

    except Exception as e:
        yield make_error_event(5, f"结构化文字稿生成失败: {str(e)}")
        return

    # ================================================================
    # 完成
    # ================================================================
    yield make_complete_event(video_id, {
        "video_path": str(video_path) if video_path else "",
        "srt_path": str(srt_path),
        "text_path": str(get_output_path(output_dir, video_id, "文字稿.md")),
        "analysis_path": str(get_output_path(output_dir, video_id, "分析报告.md")),
        "structured_path": str(get_output_path(output_dir, video_id, "结构化文字稿.md")),
    })


def _extract_narrative_section(analysis_text: str) -> str:
    """从分析报告中提取叙事结构相关部分，减少传给阶段5的上下文长度"""
    lines = analysis_text.split("\n")
    in_narrative = False
    result = []

    for line in lines:
        if "叙事结构" in line or "叙事声音" in line:
            in_narrative = True
        if in_narrative:
            # 遇到下一个大章节则停止
            if line.startswith("## 二") or line.startswith("## ") and "Viral" in line:
                break
            result.append(line)

    if not result:
        # 如果没找到专门章节，返回前 80 行
        result = lines[:80]

    return "\n".join(result)
