"""FastAPI 入口 —— 视频文案分析 Web 服务"""

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from config import HOST, PORT, DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEFAULT_OUTPUT_DIR
from models import AnalyzeRequest
from pipeline import run_pipeline
from utils import format_sse, extract_video_id
from history import create as history_create, update_stage as history_update_stage, get_list, get_detail, delete as history_delete

app = FastAPI(title="视频文案提取分析工具")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """提供前端页面"""
    index_path = static_dir / "index.html"
    if index_path.exists():
        return index_path.read_text(encoding="utf-8")
    return HTMLResponse("<h1>前端页面未找到</h1>", status_code=404)


@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "service": "视频文案提取分析工具"}


# ============================================================
# 历史记录 API
# ============================================================

@app.get("/api/history")
async def list_history():
    """获取历史记录列表"""
    return get_list()


@app.get("/api/history/{record_id}")
async def detail_history(record_id: str):
    """获取单条历史记录详情"""
    record = get_detail(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="记录未找到")
    return record


@app.delete("/api/history/{record_id}")
async def delete_history(record_id: str):
    """删除一条历史记录"""
    ok = history_delete(record_id)
    if not ok:
        raise HTTPException(status_code=404, detail="记录未找到")
    return {"status": "ok"}


# ============================================================
# 分析 API
# ============================================================

@app.post("/api/analyze")
async def analyze(request: AnalyzeRequest):
    """
    启动视频文案分析，返回 SSE 流。
    客户端通过 text/event-stream 接收实时进度和结果。
    """
    api_key = request.deepseek_api_key or DEEPSEEK_API_KEY
    if not api_key:
        raise HTTPException(
            status_code=400,
            detail="请提供 DeepSeek API Key（在请求中或设置 DEEPSEEK_API_KEY 环境变量）",
        )

    output_dir = request.output_dir or str(DEFAULT_OUTPUT_DIR)
    video_id = extract_video_id(request.video_url)
    record_id = history_create(request.video_url, video_id)

    async def event_generator():
        # 首先发送 record_id 给前端
        yield format_sse({"event": "record_created", "data": {"record_id": record_id, "video_id": video_id}})

        async for event in run_pipeline(
            video_url=request.video_url,
            api_key=api_key,
            output_dir_str=output_dir,
            base_url=DEEPSEEK_BASE_URL,
        ):
            # 拦截阶段结果，保存到历史记录
            if event.get("type") == "stage_result":
                stage = event.get("stage")
                content = event.get("content", "")
                try:
                    history_update_stage(record_id, stage, content)
                except Exception:
                    pass  # 历史记录保存失败不影响主流程

            yield format_sse(event)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)
