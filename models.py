from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    video_url: str = Field(..., description="视频链接")
    deepseek_api_key: str = Field(default="", description="DeepSeek API Key（可选，留空使用环境变量）")
    output_dir: str = Field(default="", description="输出目录（可选，留空使用默认目录）")


class ProgressEvent(BaseModel):
    event: str = "progress"
    data: dict


class StageResultEvent(BaseModel):
    event: str = "stage_result"
    data: dict


class ErrorEvent(BaseModel):
    event: str = "error"
    data: dict


class CompleteEvent(BaseModel):
    event: str = "complete"
    data: dict
