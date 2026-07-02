# photo_allocate

Проект для автоматической сортировки и AI-подписи семейного фотоархива.

## Структура проекта

```
photo_allocate/
├── config.py            # Все настройки: пути, API-ключи, флаги
├── sorter.py            # Логика перемещения файлов по папкам год/мм.дд
├── archive_scanner.py   # Сбор few-shot примеров из архива 2010-2024
├── ai_cache.py          # Кэш результатов AI (JSON-файл)
├── ai_providers.py      # Провайдеры AI (Yandex Vision и Google Gemini)
├── stage2_label.py      # CLI-скрипт: только AI-подпись папок
├── main.py              # Единый pipeline (этап 1 + этап 2)
├── requirements.txt     # Зависимости проекта
└── README.md
```

## Принцип работы

### Этап 1 — Сортировка

Читает файлы из папки **Camera Uploads** (облачное хранилище) и раскладывает их по подпапкам:

```
Foto (Фото)/
└── 2025/
    └── 04.25/
        └── IMG_20250425_120000.jpg
```

Имена файлов, начинающиеся с `IMG_`, `VID_`, `video_`, `PANO_`, `Screenshot_`, `Screenrecorder-`, обрабатываются автоматически: из них извлекается дата в формате `YYYYMMDD`.

### Этап 2 — AI-подпись

1. Находит подпапки без описания (имя вида `мм.дд`).
2. Загружает few-shot примеры из уже подписанных папок архива (2010–2024).
3. Отправляет до 5 фотографий из папки в AI-провайдеры:
   - Сначала используется **Yandex Vision** (распознавание текста на фото).
   - В случае ошибки или отсутствия настроек происходит автоматический переход (fallback) на **Google Gemini Vision** (описание происходящего на фото).
4. Получает краткое описание события (2–5 слов на русском).
5. Переименовывает папку: `04.25` → `04.25 - Праздник в школе`.
6. Кэширует результат в `ai_label_cache.json`.

## Установка

Установите зависимости проекта:

```bash
pip install -r requirements.txt
```

## Настройка

Задайте переменные окружения (или измените `config.py`):

| Переменная                | Описание                                | Пример                     |
|-----------------|---------------------------------------------------|-----------------------------|
| `GEMINI_API_KEY`| Ключ Google Gemini API                            | `AIzaSy...`                 |
| `YANDEX_VISION_API_KEY` | Ключ Yandex Cloud Vision API              | `AQVN...`                   |
| `YANDEX_VISION_FOLDER_ID` | ID каталога Yandex Cloud                | `b1g...`                    |
| `PHOTO_SOURCE`  | Путь к папке Camera Uploads                       | `D:\\Camera Uploads`         |
| `PHOTO_ARCHIVE` | Путь к папке-архиву                               | `D:\\Foto`                   |
| `DRY_RUN`       | `1` — сухой прогон, `0` — реальные изменения      | `1`                         |
| `LOG_LEVEL`     | Уровень логирования (`DEBUG`/`INFO`/`WARNING`)    | `INFO`                      |

### Получение ключей API

#### Google Gemini API
1. Откройте [Google AI Studio](https://aistudio.google.com/app/apikey).
2. Создайте API-ключ.
3. Установите переменную: `set GEMINI_API_KEY=ваш_ключ` (Windows) или `export GEMINI_API_KEY=ваш_ключ` (Linux/macOS).

#### Yandex Vision API
1. Настройте аккаунт в Yandex Cloud и получите API-ключ (или IAM-токен) и ID каталога.
2. Установите переменные: `YANDEX_VISION_API_KEY` и `YANDEX_VISION_FOLDER_ID`.

## Запуск

### Оба этапа сразу

```bash
python main.py
```

### Только сортировка (этап 1)

```bash
python main.py --stage 1
```

### Только AI-подпись (этап 2)

```bash
python main.py --stage 2 --year 2025
```

### Сухой прогон (без реальных изменений)

```bash
python main.py --dry-run
```

### Очистить AI-кэш

```bash
python main.py --stage 2 --clear-cache
```

### Все доступные параметры

```
--stage {1,2}      Запустить только этап 1 или 2. По умолчанию — оба.
--dry-run          Режим просмотра без изменений файловой системы.
--source PATH      Переопределить путь к Camera Uploads.
--archive PATH     Переопределить путь к архиву.
--year YEAR        Обрабатывать только указанный год (только для этапа 2).
--clear-cache      Очистить кэш AI перед запуском.
--log-level LEVEL  Уровень логирования: DEBUG | INFO | WARNING | ERROR.
```

## Логирование

Лог пишется одновременно в консоль и в файл `photo_allocate.log`.

## Кэш AI

Результаты работы AI сохраняются в `ai_label_cache.json`. При повторном запуске папки, уже имеющиеся в кэше, не тратят запросы к API.

## Облачное хранилище (mail.ru WebDAV)

По умолчанию пути настроены для подключённого WebDAV-диска:

```
\\webdav.cloud.mail.ru@SSL\DavWWWRoot\Camera Uploads
\\webdav.cloud.mail.ru@SSL\DavWWWRoot\Foto (Фото)
```

Для локальной папки достаточно передать `--source` и `--archive` или задать переменные окружения.
