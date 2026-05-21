"""
sorter.py — Модуль сортировки медиафайлов по структуре год/мм.дд

Логика перенесена из order_rename.py и расширена:
  - поддержка dry_run (без реального перемещения)
  - структурированное логирование
  - возврат статистики для вызывающего кода
"""
import logging
from pathlib import Path

import config

logger = logging.getLogger(__name__)


def _extract_date_prefix(filename: str) -> str:
    """
    Убирает служебные префиксы (IMG_, VID_, …) и дефисы,
    возвращает строку вида 'YYYYMMDD…'.
    """
    name = filename
    for prefix in config.FILE_NAME_BEGIN_LIST:
        if prefix in name:
            name = name.replace(prefix, "")
    name = name.replace("-", "")
    return name


def _build_target_folder(archive_root: Path, clean_name: str) -> Path:
    """
    Строит путь к целевой подпапке: <archive_root>/<YYYY>/<MM>.<DD>
    Ожидает clean_name начинающееся с 'YYYYMMDD'.
    """
    year   = clean_name[0:4]   # 2025
    month  = clean_name[4:6]   # 04
    day    = clean_name[6:8]   # 25
    return archive_root / year / f"{month}.{day}"


def sort_files(
    source: Path | None = None,
    archive: Path | None = None,
    dry_run: bool | None = None,
) -> dict:
    """
    Основная функция сортировки.

    Параметры
    ---------
    source  : папка-источник (по умолчанию из config)
    archive : папка-архив    (по умолчанию из config)
    dry_run : если True — только логирует, не перемещает файлы

    Возвращает словарь:
        {
            "moved":   int,   # успешно перемещённых файлов
            "skipped": int,   # пропущенных (нет нужного префикса / расширение)
            "errors":  int,   # ошибок
        }
    """
    source  = Path(source)  if source  is not None else Path(config.PATH_TO_SOURCE)
    archive = Path(archive) if archive is not None else Path(config.PATH_TO_ARCHIVE)
    dry_run = dry_run if dry_run is not None else config.DRY_RUN

    stats = {"moved": 0, "skipped": 0, "errors": 0}

    if not source.exists():
        logger.error("Папка-источник не найдена: %s", source)
        return stats

    logger.info("Источник : %s", source)
    logger.info("Архив    : %s", archive)
    logger.info("Dry-run  : %s", dry_run)

    for myfile in sorted(source.glob("*.*")):
        if not myfile.is_file():
            continue

        ext = myfile.suffix.lower()
        if ext not in config.SUPPORTED_EXTENSIONS:
            logger.debug("Пропуск (расширение не поддерживается): %s", myfile.name)
            stats["skipped"] += 1
            continue

        original_name = myfile.name
        clean_name = _extract_date_prefix(original_name)

        if len(clean_name) < 8 or not clean_name[:8].isdigit():
            logger.warning("Не удалось извлечь дату из имени: %s", original_name)
            stats["skipped"] += 1
            continue

        try:
            target_folder = _build_target_folder(archive, clean_name)
            target_path   = target_folder / original_name

            if dry_run:
                logger.info("[DRY-RUN] %s  →  %s", myfile, target_path)
            else:
                target_folder.mkdir(parents=True, exist_ok=True)
                myfile.rename(target_path)
                logger.info("Перемещён: %s  →  %s", original_name, target_folder)

            stats["moved"] += 1

        except Exception as exc:
            logger.error("Ошибка при обработке %s: %s", original_name, exc)
            stats["errors"] += 1

    logger.info(
        "Готово. Перемещено: %(moved)d  Пропущено: %(skipped)d  Ошибок: %(errors)d",
        stats,
    )
    return stats
