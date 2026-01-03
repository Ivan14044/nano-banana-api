"""
Утилита для загрузки изображений на публичные URL
Необходимо для работы с NanoBanana API (редактирование и комбинирование)
"""
import requests
import subprocess
import tempfile
import os
from pathlib import Path
from typing import Optional


def upload_to_imgur(image_path: str, client_id: str = None) -> Optional[str]:
    """
    Загрузить изображение на Imgur (требует API ключ)
    
    Args:
        image_path: Путь к изображению
        client_id: Imgur Client ID (опционально, можно получить бесплатно)
        
    Returns:
        URL изображения или None
    """
    # Для работы нужен Imgur Client ID
    # Можно получить бесплатно на https://api.imgur.com/oauth2/addclient
    if not client_id:
        return None
    
    try:
        headers = {"Authorization": f"Client-ID {client_id}"}
        with open(image_path, 'rb') as f:
            files = {'image': f}
            response = requests.post(
                "https://api.imgur.com/3/image",
                headers=headers,
                files=files,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    return result.get("data", {}).get("link")
    except Exception as e:
        print(f"Ошибка загрузки на Imgur: {e}")
    
    return None


def upload_to_tmpfiles(image_path: str) -> Optional[str]:
    """
    Загрузить изображение на tmpfiles.org (временный хостинг)
    
    Args:
        image_path: Путь к изображению
        
    Returns:
        URL изображения или None
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        with open(image_path, 'rb') as f:
            file_data = f.read()
            files = {'file': (Path(image_path).name, file_data, 'image/png')}
            
            # Пробуем новый API формат
            response = requests.post(
                "https://tmpfiles.org/api/v1/upload",
                files=files,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                # Пробуем распарсить как JSON
                try:
                    result = response.json()
                    # Проверяем разные форматы ответа
                    if result.get("status") == "success":
                        data = result.get("data", {})
                        file_url = data.get("url") or data.get("link")
                        if file_url:
                            # Преобразуем URL в прямой доступ
                            if file_url.startswith("/dl/"):
                                return f"https://tmpfiles.org{file_url}"
                            elif file_url.startswith("http"):
                                return file_url
                            else:
                                return f"https://tmpfiles.org/dl/{file_url}"
                    # Альтернативный формат ответа
                    elif "url" in result:
                        url = result["url"]
                        if url.startswith("/dl/"):
                            return f"https://tmpfiles.org{url}"
                        return url
                except ValueError:
                    # Если не JSON, пробуем как текст
                    text = response.text.strip()
                    if text and text.startswith("http"):
                        return text
    except Exception as e:
        print(f"Ошибка загрузки на tmpfiles: {e}")
    
    return None


def upload_to_0x0(image_path: str) -> Optional[str]:
    """
    Загрузить изображение на 0x0.st (основной хостинг)
    Использует curl через subprocess для обхода ограничений User-Agent
    
    Args:
        image_path: Путь к изображению
        
    Returns:
        URL изображения или None
    """
    # Сначала пробуем через curl (как в примере C#)
    try:
        # Создаем временный файл для результата
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.txt') as temp_file:
            temp_result = temp_file.name
        
        # Команда curl (как в примере C#)
        # Используем абсолютный путь к файлу
        abs_path = os.path.abspath(image_path)
        cmd = f'curl -F "file=@{abs_path}" https://0x0.st'
        
        # Запускаем curl через subprocess
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            url = result.stdout.strip()
            # Убираем возможные пробелы и переносы строк
            url = url.replace('\n', '').replace('\r', '').strip()
            if url and (url.startswith("http://") or url.startswith("https://")):
                # Удаляем временный файл
                try:
                    os.unlink(temp_result)
                except:
                    pass
                return url
        
        # Если curl не сработал, пробуем через requests с минимальным User-Agent
        print(f"curl не сработал, пробуем через requests...")
    except Exception as e:
        print(f"Ошибка при использовании curl: {e}")
    
    # Резервный метод через requests с минимальным User-Agent
    try:
        # Пробуем с curl User-Agent или вообще без него
        headers = {
            'User-Agent': 'curl/7.68.0'  # User-Agent от curl
        }
        
        with open(image_path, 'rb') as f:
            # 0x0.st принимает файл через multipart/form-data
            files = {'file': (Path(image_path).name, f, 'application/octet-stream')}
            response = requests.post(
                "https://0x0.st",
                files=files,
                headers=headers,
                timeout=60
            )
            
            # 0x0.st возвращает просто текстовый URL, а не JSON
            if response.status_code == 200:
                url = response.text.strip()
                url = url.replace('\n', '').replace('\r', '').strip()
                if url and (url.startswith("http://") or url.startswith("https://")):
                    return url
            else:
                print(f"0x0.st вернул статус {response.status_code}: {response.text[:200]}")
    except Exception as e:
        print(f"Ошибка загрузки на 0x0.st через requests: {e}")
    
    return None


def upload_to_fileio(image_path: str) -> Optional[str]:
    """
    Загрузить изображение на file.io (временный хостинг)
    
    Args:
        image_path: Путь к изображению
        
    Returns:
        URL изображения или None
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        with open(image_path, 'rb') as f:
            files = {'file': (Path(image_path).name, f, 'image/png')}
            response = requests.post(
                "https://file.io",
                files=files,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                # Пробуем распарсить как JSON
                try:
                    result = response.json()
                    if result.get("success"):
                        return result.get("link")
                except ValueError:
                    # Если не JSON, пробуем как текст
                    text = response.text.strip()
                    if text and text.startswith("http"):
                        return text
    except Exception as e:
        print(f"Ошибка загрузки на file.io: {e}")
    
    return None


def upload_image(image_path: str, method: str = "auto") -> Optional[str]:
    """
    Загрузить изображение на публичный URL
    
    Args:
        image_path: Путь к изображению
        method: Метод загрузки ("auto", "0x0", "tmpfiles", "fileio", "imgur")
                "auto" - пробует методы по очереди, начиная с 0x0.st
        
    Returns:
        URL изображения или None
    """
    if method == "imgur":
        # Требует API ключ, пока не реализовано
        return None
    elif method == "0x0":
        return upload_to_0x0(image_path)
    elif method == "fileio":
        return upload_to_fileio(image_path)
    elif method == "tmpfiles":
        return upload_to_tmpfiles(image_path)
    else:  # auto - пробуем методы по очереди, начиная с 0x0.st
        # Пробуем 0x0.st (основной, самый надежный)
        url = upload_to_0x0(image_path)
        if url:
            return url
        
        # Пробуем tmpfiles как резервный
        url = upload_to_tmpfiles(image_path)
        if url:
            return url
        
        # Пробуем file.io как последний вариант
        url = upload_to_fileio(image_path)
        if url:
            return url
        
        return None
