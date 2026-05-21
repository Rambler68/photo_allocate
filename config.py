"""
config.py — Централизованные настройки проекта photo_allocate
"""
import os
from pathlib import Path

# ── Пути ─────────────────────────────────────────────────────────────────────
BEGIN_OF_PATHES = r"\\webdav.cloud.mail.ru@SSL\DavWWWRoot"

# Папка-источник (Camera Uploads) — откуда берём новые файлы
PATH_TO_SOURCE: str = os.environ.get(
    "PHOTO_SOURCE",
    BEGIN_OF_PATHES + r"\Camera Uploads",
)

# Папка-архив — куда раскладываем по годам/датам
PATH_TO_ARCHIVE: str = os.environ.get(
    "PHOTO_ARCHIVE",
    BEGIN_OF_PATHES + r"\Foto (Фото)",
)

# ── Распознавание имён файлов ─────────────────────────────────────────────────
FILE_NAME_BEGIN_LIST: list[str] = [
    "IMG_", "VID_", "video_", "PANO_", "Screenshot_", "Screenrecorder-",
]

SUPPORTED_EXTENSIONS: set[str] = {
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".heic",
    ".mp4", ".mov", ".avi", ".mkv", ".3gp",
}

# ── AI (Google Gemini Vision) ─────────────────────────────────────────────────
GEMINI_API_KEY: str = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL: str = "gemini-1.5-flash"

# Максимальное число фото, которые отправляем в Gemini для одной папки
MAX_PHOTOS_PER_FOLDER: int = 5

# Лимит обучающих (few-shot) примеров, добавляемых в промпт
MAX_FEW_SHOT_EXAMPLES: int = 5

# ── Кэш ──────────────────────────────────────────────────────────────────────
CACHE_FILE: Path = Path(__file__).parent / "ai_label_cache.json"

# ── Логирование ───────────────────────────────────────────────────────────────
LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")   # DEBUG | INFO | WARNING
LOG_FILE: Path = Path(__file__).parent / "photo_allocate.log"

# ── Режим сухого прогона ──────────────────────────────────────────────────────
# True  — только вывод в лог, без реального перемещения / переименования
# False — реальное выполнение операций
DRY_RUN: bool = os.environ.get("DRY_RUN", "0") == "1"
