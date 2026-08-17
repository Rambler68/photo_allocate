"""
ai_providers.py — Abstraction layer for AI image analysis providers
"""
import base64
import logging
from pathlib import Path
from typing import Optional

import config

logger = logging.getLogger(__name__)


class AIProvider:
    """Base class for AI providers"""
    def analyze_images(self, images: list[Path], prompt: str) -> Optional[str]:
        raise NotImplementedError


class YandexVisionProvider(AIProvider):
    """Yandex Cloud Vision API implementation"""
    def __init__(self):
        if not config.YANDEX_VISION_API_KEY or not config.YANDEX_VISION_FOLDER_ID:
            raise ValueError("Yandex Vision credentials not configured")

    def _encode_image(self, image_path: Path) -> Optional[str]:
        try:
            return base64.b64encode(image_path.read_bytes()).decode()
        except Exception as exc:
            logger.warning("Failed to read image %s: %s", image_path, exc)
            return None

    def analyze_images(self, images: list[Path], prompt: str) -> Optional[str]:
        """Analyze images using Yandex Vision API"""
        try:
            from yandex.cloud.ai.vision.v1 import vision_service_pb2, vision_service_pb2_grpc
            from yandex.cloud.ai.vision.v1 import vision_pb2
            import grpc

            # Create channel and stub
            channel = grpc.ssl_channel_credentials()
            stub = vision_service_pb2_grpc.VisionServiceStub(channel)

            # Prepare request
            request = vision_service_pb2.BatchAnalyzeRequest(
                folder_id=config.YANDEX_VISION_FOLDER_ID,
                analyze_specs=[]
            )

            # Add images to request
            for img_path in images:
                encoded = self._encode_image(img_path)
                if not encoded:
                    continue

                spec = vision_pb2.AnalyzeSpec(
                    content=encoded,
                    features=[
                        vision_pb2.Feature(
                            type=vision_pb2.Feature.TEXT_DETECTION,
                            text_detection_config=vision_pb2.TextDetectionConfig(
                                language_codes=["ru"],
                                model="page"
                            )
                        )
                    ]
                )
                request.analyze_specs.append(spec)

            # Send request
            response = stub.BatchAnalyze(request)

            # Process results
            descriptions = []
            for result in response.results:
                for res in result.results:
                    if res.text_detection:
                        descriptions.append(res.text_detection.text)

            return " ".join(descriptions)[:100]  # Truncate for folder name

        except ImportError:
            logger.error("yandex-cloud-vision package not installed. Run: pip install yandex-cloud-vision")
            return None
        except Exception as exc:
            logger.error("Yandex Vision API error: %s", exc)
            return None


class RouterAIProvider(AIProvider):
    """Провайдер RouterAI (routerai.ru) — OpenAI-совместимый chat/completions API.

    Отправляет изображения как base64 data-URI в поле image_url,
    как показано в руководстве разработчика RouterAI (раздел «Мультимодальность»).
    """
    def __init__(self):
        if not config.ROUTERAI_API_KEY:
            raise ValueError("ROUTERAI_API_KEY не настроен")

    def _encode_image(self, image_path: Path) -> Optional[str]:
        try:
            return base64.b64encode(image_path.read_bytes()).decode()
        except Exception as exc:
            logger.warning("Не удалось прочитать изображение %s: %s", image_path, exc)
            return None

    @staticmethod
    def _mime_type(image_path: Path) -> Optional[str]:
        """Возвращает MIME-тип изображения по расширению файла.

        Возвращает None для неподдерживаемых форматов (например, .heic),
        которые не следует отправлять в RouterAI.
        """
        return {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".bmp": "image/bmp",
            ".webp": "image/webp",
        }.get(image_path.suffix.lower())

    def analyze_images(self, images: list[Path], prompt: str) -> Optional[str]:
        """Отправляет изображения в RouterAI и возвращает текстовое описание."""
        try:
            import requests
        except ImportError:
            logger.error("requests не установлен. Выполните: pip install requests")
            return None

        # Содержимое сообщения: сначала текстовый промпт, затем изображения
        content: list[dict] = [{"type": "text", "text": prompt}]
        for img_path in images[:config.MAX_PHOTOS_PER_FOLDER]:
            mime = self._mime_type(img_path)
            if not mime:
                logger.warning("Пропускаю файл с неподдерживаемым форматом: %s", img_path.name)
                continue
            encoded = self._encode_image(img_path)
            if not encoded:
                continue
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:{mime};base64,{encoded}",
                },
            })

        if len(content) == 1:
            logger.warning("Нет изображений для отправки в RouterAI")
            return None

        url = f"{config.ROUTERAI_BASE_URL}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config.ROUTERAI_API_KEY}",
        }
        payload = {
            "model": config.ROUTERAI_MODEL,
            "messages": [{"role": "user", "content": content}],
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=120)
            response.raise_for_status()
            data = response.json()
            description = data["choices"][0]["message"]["content"]
            return description.strip() if description else None
        except requests.RequestException as exc:
            logger.error("RouterAI API error: %s", exc)
            return None
        except (KeyError, IndexError) as exc:
            logger.error("Неожиданный формат ответа RouterAI: %s", exc)
            return None


class GeminiProvider(AIProvider):
    """Google Gemini implementation (existing functionality)"""
    def analyze_images(self, images: list[Path], prompt: str) -> Optional[str]:
        """Existing Gemini implementation from stage2_label.py"""
        try:
            import google.generativeai as genai
        except ImportError:
            logger.error("google-generativeai not installed. Run: pip install google-generativeai")
            return None

        if not config.GEMINI_API_KEY:
            logger.error("GEMINI_API_KEY not configured")
            return None

        genai.configure(api_key=config.GEMINI_API_KEY)
        model = genai.GenerativeModel(config.GEMINI_MODEL)

        parts = [prompt]
        for img_path in images:
            encoded = self._encode_image(img_path)
            if encoded:
                mime = "image/jpeg" if img_path.suffix.lower() in {".jpg", ".jpeg"} else "image/png"
                parts.append({"inline_data": {"mime_type": mime, "data": encoded}})

        try:
            response = model.generate_content(parts)
            return response.text.strip()
        except Exception as exc:
            logger.error("Gemini API error: %s", exc)
            return None

    def _encode_image(self, image_path: Path) -> Optional[str]:
        try:
            return base64.b64encode(image_path.read_bytes()).decode()
        except Exception as exc:
            logger.warning("Failed to read image %s: %s", image_path, exc)
            return None
