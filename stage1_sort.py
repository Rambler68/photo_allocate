"""
stage1_sort.py — Этап 1: сортировка медиафайлов из Camera Uploads по структуре год/мм.дд.

Использование:
    python stage1_sort.py [--dry-run] [--source PATH] [--archive PATH]
"""
import argparse
import logging
import sys
from pathlib import Path

import config
from sorter import sort_files


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
    parser = argparse.ArgumentParser(description="Этап 1: сортировка медиафайлов по папкам год/мм.дд")
    parser.add_argument("--dry-run", action="store_true", default=config.DRY_RUN,
                        help="Только вывод — без реального перемещения файлов")
    parser.add_argument("--source", type=Path, default=None,
                        help="Папка-источник (Camera Uploads)")
    parser.add_argument("--archive", type=Path, default=None,
                        help="Папка-архив (Foto)")
    parser.add_argument("--log-level", default=config.LOG_LEVEL,
                        choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    setup_logging(args.log_level)

    logger = logging.getLogger("stage1")
    logger.info("=== Этап 1: сортировка файлов ===")

    stats = sort_files(
        source=args.source,
        archive=args.archive,
        dry_run=args.dry_run,
    )

    logger.info("Результат: %s", stats)
    return 0 if stats["errors"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
