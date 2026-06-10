import os
from pathlib import Path

from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv(Path(__file__).parent / ".env")

# 自动检测并添加 FFmpeg 到 PATH
_FFMPEG_CANDIDATES = [
    r"D:\ffmpeg-8.1.1-full_build\bin",
    r"C:\ffmpeg\bin",
    os.path.expanduser(r"~\ffmpeg\bin"),
]
for _fp in _FFMPEG_CANDIDATES:
    if os.path.isdir(_fp) and _fp not in os.environ.get("PATH", ""):
        os.environ["PATH"] = _fp + os.pathsep + os.environ.get("PATH", "")

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.resolve()

# Skill 脚本目录
SKILL_SCRIPTS_DIR = PROJECT_ROOT / "video-copy-analyzer" / "scripts"

# 默认输出目录
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "output"

# DeepSeek API 配置
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

# 服务器配置
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# 输出目录确保存在
DEFAULT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
