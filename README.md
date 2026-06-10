# Video Copy Analyzer

[中文文档](README.zh-CN.md) | English

<div align="center">

**🤖 Claude Skill** | AI-Powered Video Analysis

[![Claude 4.5 Opus](https://img.shields.io/badge/Tested%20on-Claude%204.5%20Opus-blue)](https://claude.ai)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

</div>

> 🎬 One-stop video content extraction and copywriting analysis tool. Download videos, smart subtitle extraction (embedded/burned/audio), and analyze scripts using three AI frameworks.

## ✨ Features

| Stage | Function | Description |
|-------|----------|-------------|
| 1️⃣ | **Video Download** | Download from Bilibili/YouTube/Douyin (yt-dlp + custom downloader) |
| 2️⃣ | **Smart Subtitle Extraction** | Three-tier priority: Embedded → OCR (RapidOCR) → ASR (FunASR/Whisper) |
| 3️⃣ | **Smart Correction** | Context-based auto-correction of transcription errors |
| 4️⃣ | **Three-Dimensional Analysis** | TextContent + Viral + Brainstorming |

## 🚀 Quick Start

### Prerequisites

```bash
# 1. yt-dlp (video downloader)
pip install yt-dlp

# 2. FFmpeg (must be installed and in PATH)
ffmpeg -version

# 3. Python dependencies
pip install pysrt python-dotenv

# 4. FunASR (Recommended for Chinese, lightweight & accurate)
pip install funasr modelscope

# 5. RapidOCR (ONNX lightweight, for burned subtitle detection)
pip install rapidocr-onnxruntime

# 6. Whisper (Alternative for English/multilingual)
pip install openai-whisper

# 7. requests (for Douyin download)
pip install requests
```

### Usage

This is a **Claude Skill** designed for AI agents. Install it in your `.agent/skills/` directory:

```bash
git clone https://github.com/ALBEDO-TABAI/video-copy-analyzer.git .agent/skills/video-copy-analyzer
```

Then use it with Claude:

> "Analyze this video: https://www.bilibili.com/video/BV1xxxxx"

## 🎯 Smart Subtitle Extraction (3-Tier Priority)

The skill automatically selects the best extraction method:

```
Video Input
    ↓
[1️⃣ Embedded Subtitle] ──→ Detected ──→ Direct Extract (Highest Accuracy)
    ↓ Not detected
[2️⃣ Burned Subtitle OCR] ──→ RapidOCR Frame Sampling ──→ Detected ──→ Full Video OCR
    ↓ Not detected
[3️⃣ Audio Transcription] ──→ FunASR (Chinese optimized) / Whisper (Multilingual)
    ↓
Output SRT Subtitles
```

### Extraction Methods Comparison

| Tier | Method | Use Case | Accuracy | Speed |
|------|--------|----------|----------|-------|
| **L1** | Embedded Extract | Video has subtitle stream | ⭐⭐⭐⭐⭐ | ⚡ Fastest |
| **L2** | RapidOCR | Subtitles burned into video | ⭐⭐⭐⭐ | 🚀 Fast |
| **L3** | FunASR Nano | Chinese audio transcription | ⭐⭐⭐⭐ | � Medium |
| **L3** | Whisper | English/multilingual audio | ⭐⭐⭐ | 🐢 Medium |

### Tech Stack

- **RapidOCR (ONNX)**: Lightweight OCR for burned subtitle detection
  - 🚀 Lightweight: ONNX Runtime, no GPU required
  - 🎯 Cross-platform: Windows/Linux/Mac
  - 📦 Easy deploy: Single pip install
  - ✨ High accuracy: Based on PaddleOCR

- **FunASR Nano**: Alibaba open-source Chinese ASR model
  - 🚀 Lightweight: ~100MB vs Whisper Large ~1.5GB
  - 🎯 Chinese optimized: Better than Whisper for Chinese
  - ⏱️ Timestamp: Word-level timestamps
  - 💨 Fast: Runs well on CPU

## �📊 Three-Dimensional Analysis Framework

### 1. TextContent Analysis
- Narrative structure breakdown
- Rhetorical device identification
- Keyword extraction

### 2. Viral-Abstract-Script Framework
- **Viral-5D Diagnosis**: Hook / Emotion / Peaks / CTA / Social Currency
- Style positioning
- Optimization suggestions

### 3. Brainstorming Framework
- Core value decomposition
- 2-3 creative direction exploration
- Incremental verification points

## 📁 Project Structure

```
video-copy-analyzer/
├── SKILL.md                          # Core skill instructions
├── scripts/
│   ├── download_douyin.py            # Douyin video downloader (watermark-free)
│   ├── extract_subtitle_funasr.py    # Smart subtitle extraction (FunASR + RapidOCR)
│   ├── extract_subtitle.py           # Whisper-based extraction
│   ├── transcribe_audio.py           # Audio transcription script
│   └── check_environment.py          # Environment verification
└── references/
    └── analysis-frameworks.md        # Analysis framework details
```

## 🔧 Configuration

On first use, the skill will prompt you to set a default output directory:

- **Option A**: Use default `~/video-analysis/`
- **Option B**: Specify each time
- **Option C**: Set a fixed custom directory

## 📄 Output Files

After analysis, you'll receive:

| File | Content |
|------|---------|
| `{video_id}.mp4` | Original video |
| `{video_id}.srt` | Raw subtitles |
| `{video_id}_transcript.md` / `{video_id}_文字稿.md` | Corrected transcript |
| `{video_id}_analysis.md` / `{video_id}_分析报告.md` | Three-dimensional analysis report |

## 🎯 Supported Environments

This is a **Claude Skill** that works with AI coding assistants:

| Environment | Model | Status |
|-------------|-------|--------|
| **Antigravity** | Gemini 3 Pro | ✅ Supported |
| **Cursor** | Claude 4.5 Opus | ✅ **Tested & Recommended** |
| **Claude Code** | Claude 4.5 Opus | ✅ Supported |
| **Windsurf** | Any Claude model | ✅ Supported |
| **Trae** | Claude 3.5/4 | ✅ Supported |

> 💡 **Best Performance**: Tested with **Claude 4.5 Opus**, achieving optimal results in transcription correction and three-dimensional analysis.

## 📝 License

MIT License
