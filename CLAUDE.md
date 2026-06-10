# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

视频文案提取分析网页工具 — 输入视频链接（B站/YouTube/抖音），自动完成下载→字幕提取→AI分析→结构化，实时渲染结果。

## 启动服务

```bash
cd webapp
uvicorn app:app --host 0.0.0.0 --port 8000
# 浏览器打开 http://localhost:8000
```

Python 依赖安装（优先清华镜像）：
```bash
pip install -r webapp/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

系统依赖：`ffmpeg` 必须在 PATH 中。本机路径 `D:\ffmpeg-8.1.1-full_build\bin`，`config.py` 会在启动时自动添加到 PATH。

## 架构

```
webapp/                          # Web 应用
├── app.py                       # FastAPI 入口，SSE 流媒体端点
├── config.py                    # 配置 + FFmpeg PATH 检测
├── pipeline.py                  # 5 阶段异步生成器，产出 SSE 事件
├── prompts.py                   # DeepSeek API 提示词 + call_deepseek()
├── utils.py                     # SRT 解析、SSE 格式化、URL 识别
├── models.py                    # Pydantic 请求/响应模型
├── static/index.html            # 单文件前端 (Tailwind CDN + marked.js)
├── requirements.txt
└── .env.example

video-copy-analyzer/             # 原有 skill 脚本（只读复用，不修改）
├── SKILL.md                     # 5 阶段流程定义
├── scripts/
│   ├── download_douyin.py       # download_douyin_video(url, output_path) -> bool
│   └── extract_subtitle_funasr.py  # extract_with_funasr(video_path, srt_path) -> bool
└── references/
    └── analysis-frameworks.md   # 三维度分析框架详解

output/                          # 分析结果输出目录
```

## 5 阶段流水线

| 阶段 | 执行方式 | 说明 |
|------|---------|------|
| 1 下载 | `download_douyin_video()` 或 `subprocess: yt-dlp` | 抖音专用下载器，其他平台 yt-dlp |
| 2 字幕 | `extract_with_funasr()` 直接调用 | FunASR (Paraformer) 中文语音转录，输出 SRT |
| 3 校正 | DeepSeek API (temperature=0.3) | 修正 ASR 同音字错误，口语风格 |
| 4 分析 | DeepSeek API (temperature=0.7) | TextContent + Viral-5D + Brainstorming 三维度 |
| 5 结构化 | DeepSeek API (temperature=0.5) | 按叙事逻辑分段 + 小标题 + 金句加粗 |

前端通过 `fetch()` + `ReadableStream` 接收 SSE 流，阶段完成即渲染对应标签页。

## 关键注意事项

- **Windows GBK 问题**：所有 `subprocess.run()` 必须加 `encoding="utf-8", errors="replace"`，否则 emoji 字符会导致 GBK 编码崩溃。
- **FunASR 导入**：直接 `from extract_subtitle_funasr import extract_with_funasr` 调用函数，不要运行该脚本的 `main()`（它会调 B站 API 并因 cookies 卡住）。
- **DeepSeek API**：兼容 OpenAI SDK，`base_url="https://api.deepseek.com/v1"`，建议模型 `deepseek-chat`。API Key 可通过环境变量 `DEEPSEEK_API_KEY` 或网页输入框提供。
- **FunASR 首次运行**：自动下载 2-3GB 模型文件，需等待 1-5 分钟，后续秒级加载。
- **输出文件**：`{video_id}.mp4`、`{video_id}.srt`、`{video_id}_文字稿.md`、`{video_id}_分析报告.md`、`{video_id}_结构化文字稿.md`，全部写入 `output/`。
