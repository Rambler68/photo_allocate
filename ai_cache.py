"""
ai_cache.py — Кэш результатов AI-анализа папок.

Хранит результаты в JSON-файле.
Ключ кэша — нормализованный абсолютный путь к папке.

Пример записи:
{
    "\\\\webdav...\\Foto\\2025\\04.25": {
        "description": "Праздник в школе",
        "labeled_name": "04.25 - Праздник в школе",
        "timestamp": "2025-04-26T10:00:00"
    }
}
"""
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import config

logger = logging.getLogger(__name__)


def _load(cache_file: Path) -> dict:
    if cache_file.exists():
        try:
            return json.loads(cache_file.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.warning("Не удалось прочитать кэш %s: %s", cache_file, exc)
    return {}


def _save(data: dict, cache_file: Path) -> None:
    try:
        cache_file.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception as exc:
        logger.error("Не удалось сохранить кэш %s: %s", cache_file, exc)


def _key(folder: Path) -> str:
    return str(folder.resolve())


class LabelCache:
    """Простой JSON-кэш описаний папок."""

    def __init__(self, cache_file: Path | None = None):
        self._file = cache_file or config.CACHE_FILE
        self._data: dict = _load(self._file)

    # ── Публичный API ────────────────────────────────────────────────────────

    def get(self, folder: Path) -> dict | None:
        """Возвращает кэшированную запись или None."""
        return self._data.get(_key(folder))

    def set(self, folder: Path, description: str, labeled_name: str) -> None:
        """Сохраняет результат в кэш (в памяти и на диск)."""
        self._data[_key(folder)] = {
            "description": description,
            "labeled_name": labeled_name,
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        }
        _save(self._data, self._file)
        logger.debug("Кэш обновлён для %s", folder)

    def has(self, folder: Path) -> bool:
        return _key(folder) in self._data

    def clear(self) -> None:
        self._data = {}
        _save(self._data, self._file)
        logger.info("Кэш очищен")

    def stats(self) -> dict:
        return {"entries": len(self._data), "file": str(self._file)}
