"""
Управление конфигурацией приложения
"""
import json
import os
from pathlib import Path
from utils.path_utils import get_images_path, ensure_images_dir


class Config:
    """Класс для управления настройками приложения"""
    
    def __init__(self):
        self.config_dir = Path.home() / ".nanobanana_pro"
        self.config_file = self.config_dir / "config.json"
        self.config_dir.mkdir(exist_ok=True)
        
        # Получаем путь к папке изображений через утилиту
        default_images_dir = str(get_images_path())
        
        # Значения по умолчанию
        self.default_config = {
            "api_key": "",
            "default_model": "flash",  # flash или pro
            "default_resolution": "2048",  # 1024, 2048, 4096
            "save_images": True,
            "images_dir": default_images_dir,
            "theme": "dark"
        }
        
        self.load()
    
    def load(self):
        """Загрузка конфигурации из файла"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # Объединяем с дефолтными значениями
                    for key, value in self.default_config.items():
                        if key not in config:
                            config[key] = value
                    self.__dict__.update(config)
            except Exception as e:
                print(f"Ошибка загрузки конфигурации: {e}")
                self.__dict__.update(self.default_config)
        else:
            self.__dict__.update(self.default_config)
            self.save()
    
    def save(self):
        """Сохранение конфигурации в файл"""
        try:
            config_data = {key: value for key, value in self.__dict__.items() 
                          if key in self.default_config}
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Ошибка сохранения конфигурации: {e}")
    
    def get(self, key, default=None):
        """Получить значение настройки"""
        return getattr(self, key, default)
    
    def set(self, key, value):
        """Установить значение настройки"""
        if key in self.default_config:
            setattr(self, key, value)
            self.save()
    
    def ensure_images_dir(self):
        """Создать папку для изображений если её нет"""
        # Используем утилиту для получения правильного пути
        images_path = ensure_images_dir()
        # Обновляем конфигурацию если путь изменился
        if str(images_path) != self.get("images_dir"):
            self.set("images_dir", str(images_path))
        return images_path


