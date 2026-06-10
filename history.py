"""历史记录管理 —— JSON 文件存储"""

import json
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path

HISTORY_FILE = Path(__file__).parent.parent / "output" / ".history.json"

TZ = timezone(timedelta(hours=8))


def _load_all() -> list[dict]:
    if not HISTORY_FILE.exists():
        return []
    try:
        data = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def _save_all(records: list[dict]) -> None:
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_FILE.write_text(
        json.dumps(records, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def create(video_url: str, video_id: str) -> str:
    """创建一条新的历史记录，返回记录 ID"""
    record_id = uuid.uuid4().hex[:12]
    record = {
        "id": record_id,
        "video_id": video_id,
        "video_url": video_url,
        "title": video_id,
        "created_at": datetime.now(TZ).isoformat(),
        "stages": {},
    }
    records = _load_all()
    records.insert(0, record)
    _save_all(records)
    return record_id


def update_stage(record_id: str, stage: int, content: str) -> None:
    """更新指定记录某个阶段的结果"""
    records = _load_all()
    stage_key = {3: "text", 4: "analysis", 5: "structured"}[stage]
    for r in records:
        if r["id"] == record_id:
            r["stages"][stage_key] = content
            # 从阶段5结果中提取标题
            if stage == 5 and content:
                title = _extract_title(content)
                if title:
                    r["title"] = title
            break
    _save_all(records)


def update_title(record_id: str, title: str) -> None:
    """更新历史记录标题"""
    records = _load_all()
    for r in records:
        if r["id"] == record_id:
            r["title"] = title
            break
    _save_all(records)


def _extract_title(markdown: str) -> str:
    """从结构化文字稿中提取标题"""
    for line in markdown.split("\n"):
        line = line.strip()
        if line.startswith("# ") and not line.startswith("## "):
            title = line[2:].strip()
            # 去掉 "结构化文字稿" 后缀
            title = title.replace(" 结构化文字稿", "").replace("结构化文字稿", "")
            return title
    return ""


def get_list() -> list[dict]:
    """获取历史记录列表（不含完整内容，仅摘要）"""
    records = _load_all()
    summaries = []
    for r in records:
        item = {
            "id": r["id"],
            "video_id": r.get("video_id", ""),
            "video_url": r.get("video_url", ""),
            "title": r.get("title", r.get("video_id", "")),
            "created_at": r.get("created_at", ""),
            "has_text": "text" in r.get("stages", {}),
            "has_analysis": "analysis" in r.get("stages", {}),
            "has_structured": "structured" in r.get("stages", {}),
        }
        summaries.append(item)
    return summaries


def get_detail(record_id: str) -> dict | None:
    """获取单条历史记录详情（含完整内容）"""
    records = _load_all()
    for r in records:
        if r["id"] == record_id:
            return r
    return None


def delete(record_id: str) -> bool:
    """删除一条历史记录"""
    records = _load_all()
    new_records = [r for r in records if r["id"] != record_id]
    if len(new_records) == len(records):
        return False
    _save_all(new_records)
    return True
