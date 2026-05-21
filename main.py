"""
main.py — Единый pipeline: Этап 1 (сортировка) → Этап 2 (AI-подпись).

Использование:
    python main.py                        # оба этапа, реальный режим
    python main.py --dry-run              # оба этапа, без реальных изменений
    python main.py --stage 1              # только сортировка
    python main.py --stage 2              # только AI-подпись
    python main.py --stage 2 --year 2025  # подписать только 2025 год
    python main.py --clear-cache          # очистить AI-кэш перед запуском
"""
import argparse
import logging
import sys
from pathlib import Path

import config
from ai_cache import LabelCache


def setup_logging(level: str = config.LOG_LEVEL) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(config.LOG_FILE, encoding="utf-8"),
        ],
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="photo_allocate — сортировка и AI-подпись фотоархива",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--stage", type=int, choices=[1, 2], default=None,
        help="Запустить только указанный этап (1 или 2). По умолчанию — оба.",
    )
    parser.add_argument(
        "--dry-run", action="store_true", default=config.DRY_RUN,
        help="Режим сухого прогона — без реальных изменений файловой системы.",
    )
    parser.add_argument("--source",  type=Path, default=None, help="Папка-источник (Camera Uploads)")
    parser.add_argument("--archive", type=Path, default=None, help="Папка-архив (Foto)")
    parser.add_argument("--year",    type=int,  default=None, help="Год для этапа 2")
    parser.add_argument(
        "--clear-cache", action="store_true",
        help="Очистить кэш AI перед запуском этапа 2",
    )
    parser.add_argument(
        "--log-level", default=config.LOG_LEVEL,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )
    return parser.parse_args()


def run_stage1(args: argparse.Namespace) -> int:
    from sorter import sort_files
    logger = logging.getLogger("stage1")
    logger.info("=== Этап 1: сортировка файлов ===")
    stats = sort_files(source=args.source, archive=args.archive, dry_run=args.dry_run)
    logger.info("Результат этапа 1: %s", stats)
    return 0 if stats["errors"] == 0 else 1


def run_stage2(args: argparse.Namespace) -> int:
    from stage2_label import label_folders
    logger = logging.getLogger("stage2")
    logger.info("=== Этап 2: AI-подпись папок ===")

    cache = LabelCache()
    if args.clear_cache:
        cache.clear()
        logger.info("Кэш AI очищен")

    stats = label_folders(
        archive=args.archive,
        year=args.year,
        dry_run=args.dry_run,
        cache=cache,
    )
    logger.info("Результат этапа 2: %s", stats)
    return 0 if stats["errors"] == 0 else 1


def main() -> int:
    args = parse_args()
    setup_logging(args.log_level)

    logger = logging.getLogger("main")
    logger.info("photo_allocate pipeline запущен  |  dry-run=%s  |  stage=%s",
                args.dry_run, args.stage or "1+2")

    exit_code = 0

    if args.stage in (None, 1):
        exit_code |= run_stage1(args)

    if args.stage in (None, 2):
        exit_code |= run_stage2(args)

    logger.info("Pipeline завершён. Код выхода: %d", exit_code)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
