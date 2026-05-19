"""
archive_scanner.py — Сканирование архива фотографий для сбора few-shot примеров.

Обходит структуру <archive_root>/<год>/<дата - описание>/
и возвращает список пар (описание_папки, [пути_к_фото]).

Используется в stage2_label.py для формирования обучающих примеров (few-shot prompting).
"""
import logging
import random
from pathlib import Path

import config

logger = logging.getLogger(__name__)

IMAGE_EXTENSIONS: set[str] = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".heic"}


def _has_description(folder_name: str) -> bool:
    """Папка содержит описание, если после 'мм.дд' есть ещё текст."""
    parts = folder_name.split(" ", 1)
    return len(parts) == 2 and parts[1].strip() != ""


def _extract_description(folder_name: str) -> str:
    """Возвращает текстовое описание из имени папки вида 'мм.дд - Описание'."""
    parts = folder_name.split(" ", 1)
    if len(parts) == 2:
        return parts[1].strip(" -–—").strip()
    return ""


def _get_images(folder: Path, max_count: int = config.MAX_PHOTOS_PER_FOLDER) -> list[Path]:
    """Возвращает до max_count изображений из папки."""
    images = [
        f for f in folder.iterdir()
        if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS
    ]
    return images[:max_count]


def scan_archive(
    archive_root: Path | None = None,
    year_from: int = 2010,
    year_to: int = 2024,
    max_examples: int = 200,
) -> list[dict]:
    """
    Сканирует архив и собирает обучающие примеры.

    Возвращает список словарей:
    [
        {
            "folder_name": "10.25 - Праздник в школе",
            "description": "Праздник в школе",
            "images": [Path(...), Path(...)],
        },
        ...
    ]
    """
    archive_root = Path(archive_root) if archive_root else Path(config.PATH_TO_ARCHIVE)
    examples: list[dict] = []

    if not archive_root.exists():
        logger.error("Архив не найден: %s", archive_root)
        return examples

    for year_dir in sorted(archive_root.iterdir()):
        if not year_dir.is_dir():
            continue
        try:
            year = int(year_dir.name)
        except ValueError:
            continue
        if not (year_from <= year <= year_to):
            continue

        for date_dir in sorted(year_dir.iterdir()):
            if not date_dir.is_dir():
                continue
            if not _has_description(date_dir.name):
                continue

            description = _extract_description(date_dir.name)
            images = _get_images(date_dir)

            if not images:
                logger.debug("Нет изображений в %s, пропуск", date_dir)
                continue

            examples.append({
                "folder_name": date_dir.name,
                "description": description,
                "images": images,
            })

            if len(examples) >= max_examples:
                logger.info("Достигнут лимит примеров: %d", max_examples)
                return examples

    logger.info("Собрано обучающих примеров: %d", len(examples))
    return examples


def get_few_shot_examples(
    archive_root: Path | None = None,
    n: int = config.MAX_FEW_SHOT_EXAMPLES,
    seed: int = 42,
) -> list[dict]:
    """
    Возвращает n случайных обучающих примеров из архива.
    Примеры перемешиваются с фиксированным seed для воспроизводимости.
    """
    all_examples = scan_archive(archive_root)
    rng = random.Random(seed)
    rng.shuffle(all_examples)
    return all_examples[:n]
