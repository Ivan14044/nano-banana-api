"""
Утилиты для работы с изображениями
"""
import base64
from io import BytesIO
from pathlib import Path
from PIL import Image
import requests


def image_to_base64(image_path: str) -> str:
    """
    Конвертировать изображение в base64 строку
    
    Args:
        image_path: Путь к изображению
        
    Returns:
        base64 строка изображения
    """
    try:
        with open(image_path, 'rb') as f:
            image_data = f.read()
            return base64.b64encode(image_data).decode('utf-8')
    except Exception as e:
        print(f"Ошибка конвертации изображения в base64: {e}")
        return ""


def crop_to_aspect_ratio(image_path: str, aspect_ratio: str, resolution: str = None) -> bool:
    """
    Обрезать изображение до точного соотношения сторон
    
    Args:
        image_path: Путь к изображению
        aspect_ratio: Соотношение сторон (например, "4:3", "16:9")
        resolution: Разрешение (например, "2048") - опционально, для масштабирования
        
    Returns:
        True если успешно, False иначе
    """
    try:
        # Парсим соотношение сторон
        parts = aspect_ratio.split(':')
        if len(parts) != 2:
            return False
        
        target_w = float(parts[0])
        target_h = float(parts[1])
        target_ratio = target_w / target_h
        
        # Открываем изображение
        with Image.open(image_path) as img:
            current_w, current_h = img.size
            current_ratio = current_w / current_h
            
            # Если соотношение уже правильное (с небольшой погрешностью), проверяем разрешение
            if abs(current_ratio - target_ratio) < 0.01:
                # Соотношение правильное, но может нужно изменить размер
                if resolution:
                    target_size = int(resolution)
                    # Вычисляем размеры на основе соотношения сторон
                    if target_w >= target_h:
                        new_w = target_size
                        new_h = int(target_size * target_h / target_w)
                    else:
                        new_h = target_size
                        new_w = int(target_size * target_w / target_h)
                    
                    if current_w != new_w or current_h != new_h:
                        img_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                        img_resized.save(image_path)
                return True
            
            # Нужно обрезать до нужного соотношения
            # Вычисляем размеры обрезки (центрированная обрезка)
            if current_ratio > target_ratio:
                # Текущее изображение шире, обрезаем по ширине
                new_w = int(current_h * target_ratio)
                new_h = current_h
                left = (current_w - new_w) // 2
                top = 0
                right = left + new_w
                bottom = current_h
            else:
                # Текущее изображение выше, обрезаем по высоте
                new_w = current_w
                new_h = int(current_w / target_ratio)
                left = 0
                top = (current_h - new_h) // 2
                right = current_w
                bottom = top + new_h
            
            # Обрезаем изображение
            img_cropped = img.crop((left, top, right, bottom))
            
            # Если указано разрешение, масштабируем
            if resolution:
                target_size = int(resolution)
                if target_w >= target_h:
                    final_w = target_size
                    final_h = int(target_size * target_h / target_w)
                else:
                    final_h = target_size
                    final_w = int(target_size * target_w / target_h)
                img_cropped = img_cropped.resize((final_w, final_h), Image.Resampling.LANCZOS)
            
            # Сохраняем обрезанное изображение
            img_cropped.save(image_path)
            return True
            
    except Exception as e:
        print(f"Ошибка обрезки изображения: {e}")
        return False


def base64_to_image(base64_string: str, output_path: str, aspect_ratio: str = None, resolution: str = None, crop_to_aspect: bool = False):
    """
    Сохранить base64 строку как изображение
    
    Args:
        base64_string: base64 строка изображения
        output_path: Путь для сохранения
        aspect_ratio: Соотношение сторон для обрезки (опционально)
        resolution: Разрешение для масштабирования (опционально)
        crop_to_aspect: Если True, обрезать до точного соотношения сторон (по умолчанию False)
    """
    try:
        image_data = base64.b64decode(base64_string)
        image = Image.open(BytesIO(image_data))
        
        # Создаем папку если её нет
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Сохраняем изображение
        image.save(output_path)
        
        # Если указано соотношение сторон и включена опция обрезки, обрезаем
        if aspect_ratio and crop_to_aspect:
            crop_to_aspect_ratio(str(output_path), aspect_ratio, resolution)
        
        return True
    except Exception as e:
        print(f"Ошибка сохранения изображения: {e}")
        return False


def url_to_image(url: str, output_path: str, aspect_ratio: str = None, resolution: str = None, crop_to_aspect: bool = False) -> bool:
    """
    Скачать изображение по URL и сохранить
    
    Args:
        url: URL изображения
        output_path: Путь для сохранения
        aspect_ratio: Соотношение сторон для обрезки (опционально)
        resolution: Разрешение для масштабирования (опционально)
        crop_to_aspect: Если True, обрезать до точного соотношения сторон (по умолчанию False)
        
    Returns:
        True если успешно, False иначе
    """
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        image = Image.open(BytesIO(response.content))
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(output_path)
        
        # Если указано соотношение сторон и включена опция обрезки, обрезаем
        if aspect_ratio and crop_to_aspect:
            crop_to_aspect_ratio(str(output_path), aspect_ratio, resolution)
        
        return True
    except Exception as e:
        print(f"Ошибка загрузки изображения: {e}")
        return False


def get_image_info(image_path: str) -> dict:
    """
    Получить информацию об изображении
    
    Args:
        image_path: Путь к изображению
        
    Returns:
        Словарь с информацией (width, height, format, size)
    """
    try:
        with Image.open(image_path) as img:
            return {
                "width": img.width,
                "height": img.height,
                "format": img.format,
                "size": Path(image_path).stat().st_size
            }
    except Exception as e:
        print(f"Ошибка получения информации об изображении: {e}")
        return {}


def resize_image(image_path: str, max_size: int = 2048) -> str:
    """
    Изменить размер изображения если оно слишком большое
    
    Args:
        image_path: Путь к изображению
        max_size: Максимальный размер стороны
        
    Returns:
        Путь к обработанному изображению
    """
    try:
        with Image.open(image_path) as img:
            if img.width <= max_size and img.height <= max_size:
                return image_path
            
            # Масштабируем сохраняя пропорции
            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
            # Сохраняем во временный файл
            temp_path = str(Path(image_path).parent / f"temp_{Path(image_path).name}")
            img.save(temp_path)
            return temp_path
    except Exception as e:
        print(f"Ошибка изменения размера изображения: {e}")
        return image_path
