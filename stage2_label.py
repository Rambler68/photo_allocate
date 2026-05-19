"""
stage2_label.py — Этап 2: AI-анализ папок и добавление описания к имени подпапки.

Алгоритм:
1. Обходит папки архива за текущий год (или указанный), у которых нет описания.
2. Собирает few-shot примеры из archive_scanner (папки с уже готовыми описаниями).
3. Для каждой безымянной папки отправляет запрос в Google Gemini Vision.
4. Результат кэширует (ai_cache.py).
5. Переименовывает папку, добавляя описание: "мм.дд" → "мм.дд - Описание".

Использование:
    python stage2_label.py [--dry-run] [--year 2025] [--archive PATH] [--clear-cache]
"""
import argparse
import base64
import logging
import re
import sys
from pathlib import Path

import config
from ai_cache import LabelCache
from archive_scanner import get_few_shot_examples

logger = logging.getLogger(__name__)

IMAGE_EXTENSIONS: set[str] = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".heic"}


# ── Вспомогательные функции ───────────────────────────────────────────────────

def _is_unlabeled(folder_name: str) -> bool:
    """Папка не имеет описания, если имя состоит только из 'мм.дд'."""
    return bool(re.fullmatch(r"\d{2}\.\d{2}", folder_name.strip()))


def _get_sample_images(folder: Path, max_count: int = config.MAX_PHOTOS_PER_FOLDER) -> list[Path]:
    images = [
        f for f in folder.iterdir()
        if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS
    ]
    return sorted(images)[:max_count]


def _encode_image(image_path: Path) -> str | None:
    """Кодирует изображение в base64 для передачи в Gemini API."""
    try:
        return base64.b64encode(image_path.read_bytes()).decode()
    except Exception as exc:
        logger.warning("Не удалось прочитать изображение %s: %s", image_path, exc)
        return None


def _build_prompt(few_shot: list[dict]) -> str:
    """Строит системный промпт с few-shot примерами."""
    lines = [
        "Ты — помощник, который кратко описывает событие по фотографиям из семейного альбома.",
        "Описание должно быть на русском языке, 2-5 слов, подходить для имени папки.",
        "Не используй даты, цифры, спецсимволы (кроме пробела и дефиса).",
        "",
        "Примеры:",
    ]
    for ex in few_shot:
        lines.append(f'  Описание: "{ex["description"]}"')
    lines += [
        "",
        "Посмотри на приложенные фотографии и дай ОДНО короткое описание события.",
        "Ответь только описанием, без кавычек и пояснений.",
    ]
    return "\n".join(lines)


# ── Gemini Vision ─────────────────────────────────────────────────────────────

def _call_gemini(images: list[Path], prompt: str) -> str | None:
    """
    Отправляет изображения и промпт в Google Gemini Vision.
    Возвращает строку-описание или None при ошибке.
    """
    try:
        import google.generativeai as genai  # pip install google-generativeai
    except ImportError:
        logger.error("Пакет google-generativeai не установлен. Выполните: pip install google-generativeai")
        return None

    if not config.GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY не задан в config.py или переменных окружения")
        return None

    genai.configure(api_key=config.GEMINI_API_KEY)
    model = genai.GenerativeModel(config.GEMINI_MODEL)

    # Формируем части запроса: промпт + изображения
    parts: list = [prompt]
    for img_path in images:
        encoded = _encode_image(img_path)
        if encoded:
            mime = "image/jpeg" if img_path.suffix.lower() in {".jpg", ".jpeg"} else "image/png"
            parts.append({"inline_data": {"mime_type": mime, "data": encoded}})

    try:
        response = model.generate_content(parts)
        description = response.text.strip()
        logger.debug("Gemini ответил: %r", description)
        return description
    except Exception as exc:
        logger.error("Ошибка Gemini API: %s", exc)
        return None


# ── Основной процесс ──────────────────────────────────────────────────────────

def label_folders(
    archive: Path | None = None,
    year: int | None = None,
    dry_run: bool | None = None,
    cache: LabelCache | None = None,
) -> dict:
    """
    Находит безымянные папки и добавляет к ним AI-описание.

    Возвращает статистику:
        {"labeled": int, "skipped": int, "cached": int, "errors": int}
    """
    archive = Path(archive) if archive else Path(config.PATH_TO_ARCHIVE)
    dry_run = dry_run if dry_run is not None else config.DRY_RUN
    cache   = cache or LabelCache()

    stats = {"labeled": 0, "skipped": 0, "cached": 0, "errors": 0}

    if not archive.exists():
        logger.error("Архив не найден: %s", archive)
        return stats

    # Получаем few-shot примеры из архива (2010-2024)
    few_shot = get_few_shot_examples(archive)
    prompt   = _build_prompt(few_shot)
    logger.info("Few-shot примеров загружено: %d", len(few_shot))

    # Определяем папки для обработки
    year_dirs = []
    if year:
        candidate = archive / str(year)
        if candidate.is_dir():
            year_dirs = [candidate]
        else:
            logger.warning("Папка года не найдена: %s", candidate)
    else:
        year_dirs = [d for d in sorted(archive.iterdir()) if d.is_dir()]

    for year_dir in year_dirs:
        for date_dir in sorted(year_dir.iterdir()):
            if not date_dir.is_dir():
                continue
            if not _is_unlabeled(date_dir.name):
                logger.debug("Уже подписана, пропуск: %s", date_dir.name)
                stats["skipped"] += 1
                continue

            # Проверяем кэш
            if cache.has(date_dir):
                cached = cache.get(date_dir)
                logger.info("Из кэша: %s → %s", date_dir.name, cached["labeled_name"])
                if not dry_run:
                    _rename_folder(date_dir, cached["labeled_name"])
                stats["cached"] += 1
                continue

            images = _get_sample_images(date_dir)
            if not images:
                logger.warning("Нет изображений в %s, пропуск", date_dir)
                stats["skipped"] += 1
                continue

            logger.info("Анализируем: %s (%d фото)", date_dir, len(images))
            description = _call_gemini(images, prompt)

            if not description:
                logger.error("Не получено описание для %s", date_dir)
                stats["errors"] += 1
                continue

            # Очищаем описание от недопустимых символов для имени папки
            safe_desc = re.sub(r'[\\/:*?"<>|]', "", description).strip()
            labeled_name = f"{date_dir.name} - {safe_desc}"

            cache.set(date_dir, safe_desc, labeled_name)

            if dry_run:
                logger.info("[DRY-RUN] %s  →  %s", date_dir.name, labeled_name)
            else:
                error = _rename_folder(date_dir, labeled_name)
                if error:
                    stats["errors"] += 1
                    continue

            stats["labeled"] += 1

    logger.info(
        "Этап 2 завершён. Подписано: %(labeled)d  Из кэша: %(cached)d  "
        "Пропущено: %(skipped)d  Ошибок: %(errors)d",
        stats,
    )
    return stats


def _rename_folder(folder: Path, new_name: str) -> Exception | None:
    """Переименовывает папку. Возвращает исключение при ошибке."""
    new_path = folder.parent / new_name
    if new_path.exists():
        logger.warning("Целевая папка уже существует: %s", new_path)
        return ValueError(f"Already exists: {new_path}")
    try:
        folder.rename(new_path)
        logger.info("Переименована: %s  →  %s", folder.name, new_name)
        return None
    except Exception as exc:
        logger.error("Ошибка переименования %s: %s", folder, exc)
        return exc


# ── CLI ───────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Этап 2: AI-подпись папок по содержимому фото")
    parser.add_argument("--dry-run", action="store_true", default=config.DRY_RUN)
    parser.add_argument("--year", type=int, default=None, help="Обрабатывать только указанный год")
    parser.add_argument("--archive", type=Path, default=None)
    parser.add_argument("--clear-cache", action="store_true", help="Очистить кэш AI перед запуском")
    parser.add_argument("--log-level", default=config.LOG_LEVEL,
                        choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    return parser.parse_args()


def setup_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(config.LOG_FILE, encoding="utf-8"),
        ],
    )


def main() -> int:
    args = parse_args()
    setup_logging(args.log_level)

    logger.info("=== Этап 2: AI-подпись папок ===")

    cache = LabelCache()
    if args.clear_cache:
        cache.clear()
        logger.info("Кэш очищен")

    stats = label_folders(
        archive=args.archive,
        year=args.year,
        dry_run=args.dry_run,
        cache=cache,
    )
    return 0 if stats["errors"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
