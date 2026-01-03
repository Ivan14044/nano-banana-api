"""
Модели данных для API
"""
from dataclasses import dataclass
from typing import Optional, List


@dataclass
class GenerationRequest:
    """Запрос на генерацию изображения"""
    prompt: str
    model: str = "flash"  # flash или pro
    resolution: str = "2048"  # 1024, 2048, 4096
    negative_prompt: Optional[str] = None
    num_images: int = 1
    seed: Optional[int] = None
    aspect_ratio: Optional[str] = None  # Для Pro API: "1:1", "16:9", "9:16", etc.
    reference_images: Optional[List[str]] = None  # Пути к референсным изображениям (до 8, только для Pro)


@dataclass
class EditRequest:
    """Запрос на редактирование изображения"""
    image_path: str
    prompt: str
    model: str = "flash"
    resolution: Optional[str] = None  # Если None, использует размер исходного изображения
    negative_prompt: Optional[str] = None
    aspect_ratio: Optional[str] = None  # Соотношение сторон: "1:1", "16:9", "9:16", etc.


@dataclass
class CombineRequest:
    """Запрос на комбинирование изображений"""
    image_paths: List[str]  # До 8 изображений
    prompt: str
    model: str = "pro"  # Обычно комбинирование требует Pro модель
    resolution: str = "2048"
    negative_prompt: Optional[str] = None
    aspect_ratio: Optional[str] = None  # Соотношение сторон: "1:1", "16:9", "9:16", etc.


@dataclass
class APIResponse:
    """Ответ от API"""
    success: bool
    image_url: Optional[str] = None
    image_base64: Optional[str] = None
    error_message: Optional[str] = None
    credits_used: Optional[float] = None

