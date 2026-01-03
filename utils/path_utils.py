"""
Утилиты для работы с путями в режиме разработки и в исполняемом файле
"""
import sys
import os
from pathlib import Path


def get_base_path() -> Path:
    """
    Получить базовый путь к приложению
    
    Returns:
        Path: Базовый путь (папка с exe или папка проекта)
    """
    if getattr(sys, 'frozen', False):
        # Если запущено из exe (PyInstaller)
        # sys.executable - путь к exe файлу
        return Path(sys.executable).parent
    else:
        # Если запущено из исходников
        # Возвращаем папку проекта (на уровень выше utils)
        return Path(__file__).parent.parent


def get_resource_path(relative_path: str) -> Path:
    """
    Получить путь к ресурсу в зависимости от режима (dev или exe)
    
    Args:
        relative_path: Относительный путь к ресурсу (например, "data/images")
        
    Returns:
        Path: Абсолютный путь к ресурсу
    """
    base_path = get_base_path()
    return base_path / relative_path


def get_data_path() -> Path:
    """
    Получить путь к папке data
    
    Returns:
        Path: Путь к папке data
    """
    return get_resource_path("data")


def get_images_path() -> Path:
    """
    Получить путь к папке с изображениями
    
    Returns:
        Path: Путь к папке data/images
    """
    return get_resource_path("data/images")


def get_db_path() -> Path:
    """
    Получить путь к файлу базы данных
    
    Returns:
        Path: Путь к data/history.db
    """
    return get_resource_path("data/history.db")


def ensure_data_dir() -> Path:
    """
    Создать папку data если её нет
    
    Returns:
        Path: Путь к папке data
    """
    data_path = get_data_path()
    data_path.mkdir(parents=True, exist_ok=True)
    return data_path


def ensure_images_dir() -> Path:
    """
    Создать папку data/images если её нет
    
    Returns:
        Path: Путь к папке data/images
    """
    images_path = get_images_path()
    images_path.mkdir(parents=True, exist_ok=True)
    return images_path





