"""
Клиент для работы с NanoBanana API
Адаптирован для веб-приложения
"""
import requests
import time
from typing import Optional, List
from .models import GenerationRequest, EditRequest, CombineRequest, APIResponse


class NanoBananaAPIClient:
    """Клиент для взаимодействия с NanoBanana API"""
    
    # Базовые URL для API согласно документации
    BASE_URL = "https://api.nanobananaapi.ai/api/v1/nanobanana"
    GENERATE_URL = f"{BASE_URL}/generate"
    GENERATE_PRO_URL = f"{BASE_URL}/generate-pro"
    TASK_INFO_URL = f"{BASE_URL}/record-info"
    CREDIT_URL = "https://api.nanobananaapi.ai/api/v1/common/credit"
    
    # Фиктивный callback URL (требуется API, но не используется для веб-приложения)
    DUMMY_CALLBACK = "https://example.com/callback"
    
    def __init__(self, api_key: str):
        """
        Инициализация клиента
        
        Args:
            api_key: API ключ от NanoBanana
        """
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def _create_task(self, url: str, data: dict) -> Optional[str]:
        """
        Создать задачу генерации
        
        Args:
            url: URL эндпоинта
            data: Данные для отправки
            
        Returns:
            taskId или None при ошибке
        """
        try:
            response = requests.post(
                url,
                headers=self.headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("code") == 200 and "data" in result:
                    task_id = result["data"].get("taskId")
                    if task_id:
                        return task_id
                    else:
                        # Для Pro API формат может быть другим
                        task_id = result["data"].get("taskId") or result.get("data", {}).get("task_id")
                        if task_id:
                            return task_id
                # Проверяем альтернативные форматы
                if result.get("code") == 200:
                    # Может быть напрямую в data
                    if isinstance(result.get("data"), dict):
                        task_id = result["data"].get("taskId") or result["data"].get("task_id")
                        if task_id:
                            return task_id
                return None
            else:
                return None
        except Exception as e:
            print(f"Ошибка создания задачи: {e}")
            return None
    
    def _get_task_status(self, task_id: str, max_wait: int = 300) -> dict:
        """
        Получить статус задачи с polling
        
        Args:
            task_id: ID задачи
            max_wait: Максимальное время ожидания в секундах
            
        Returns:
            Словарь с результатом задачи
        """
        start_time = time.time()
        poll_interval = 3  # Опрашиваем каждые 3 секунды
        
        while time.time() - start_time < max_wait:
            try:
                response = requests.get(
                    self.TASK_INFO_URL,
                    headers=self.headers,
                    params={"taskId": task_id},
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("code") == 200 and "data" in result:
                        data = result["data"]
                        success_flag = data.get("successFlag")
                        
                        # 0: GENERATING - задача обрабатывается
                        # 1: SUCCESS - успешно завершена
                        # 2: CREATE_TASK_FAILED - ошибка создания задачи
                        # 3: GENERATE_FAILED - ошибка генерации
                        
                        if success_flag == 1:
                            # Успешно завершено
                            response_data = data.get("response", {})
                            image_url = response_data.get("resultImageUrl")
                            return {
                                "success": True,
                                "image_url": image_url,
                                "task_id": task_id
                            }
                        elif success_flag in [2, 3]:
                            # Ошибка
                            error_msg = data.get("errorMessage", "Неизвестная ошибка генерации")
                            return {
                                "success": False,
                                "error": error_msg,
                                "task_id": task_id
                            }
                        # Иначе продолжаем ждать (success_flag == 0)
                
                time.sleep(poll_interval)
            except requests.exceptions.RequestException as e:
                print(f"Ошибка при опросе статуса: {e}")
                time.sleep(poll_interval)
            except Exception as e:
                print(f"Неожиданная ошибка: {e}")
                time.sleep(poll_interval)
        
        return {
            "success": False,
            "error": "Превышено время ожидания генерации",
            "task_id": task_id
        }
    
    def generate_image(self, request: GenerationRequest, reference_urls: List[str] = None) -> APIResponse:
        """
        Генерация изображения по текстовому описанию
        
        Args:
            request: Параметры генерации
            reference_urls: Список публичных URL референсных изображений (если уже загружены)
            
        Returns:
            APIResponse с результатом
        """
        # Используем обычный эндпоинт для Flash, Pro для Pro модели
        if request.model == "pro":
            return self._generate_pro(request, reference_urls)
        else:
            # Референсы поддерживаются только в Pro API
            if reference_urls:
                return APIResponse(
                    success=False,
                    error_message="Референсные изображения поддерживаются только в Pro модели"
                )
            return self._generate_standard(request)
    
    def _generate_standard(self, request: GenerationRequest) -> APIResponse:
        """Генерация через обычный эндпоинт"""
        # Используем указанный aspect ratio или по умолчанию "1:1"
        aspect_ratio = request.aspect_ratio or "1:1"
        
        data = {
            "prompt": request.prompt,
            "type": "TEXTTOIAMGE",
            "numImages": min(request.num_images, 4),  # Максимум 4
            "callBackUrl": self.DUMMY_CALLBACK,  # Обязательный параметр
            "image_size": aspect_ratio
        }
        
        # Создаем задачу
        task_id = self._create_task(self.GENERATE_URL, data)
        if not task_id:
            return APIResponse(
                success=False,
                error_message="Не удалось создать задачу генерации"
            )
        
        # Ожидаем завершения
        result = self._get_task_status(task_id)
        
        if result.get("success"):
            return APIResponse(
                success=True,
                image_url=result.get("image_url")
            )
        else:
            return APIResponse(
                success=False,
                error_message=result.get("error", "Ошибка генерации")
            )
    
    def _generate_pro(self, request: GenerationRequest, reference_urls: List[str] = None) -> APIResponse:
        """Генерация через Pro эндпоинт"""
        # Преобразуем разрешение
        resolution_map = {
            "1024": "1K",
            "2048": "2K",
            "4096": "4K"
        }
        resolution = resolution_map.get(request.resolution, "2K")
        
        # Используем указанный aspect ratio или по умолчанию "1:1"
        aspect_ratio = request.aspect_ratio or "1:1"
        
        data = {
            "prompt": request.prompt,
            "resolution": resolution,
            "callBackUrl": self.DUMMY_CALLBACK,  # Обязательный параметр
            "aspectRatio": aspect_ratio
        }
        
        # Добавляем референсные изображения если есть
        if reference_urls:
            if len(reference_urls) > 8:
                return APIResponse(
                    success=False,
                    error_message="Максимум 8 референсных изображений"
                )
            data["imageUrls"] = reference_urls
        
        # Создаем задачу
        task_id = self._create_task(self.GENERATE_PRO_URL, data)
        if not task_id:
            return APIResponse(
                success=False,
                error_message="Не удалось создать задачу генерации"
            )
        
        # Ожидаем завершения
        result = self._get_task_status(task_id)
        
        if result.get("success"):
            return APIResponse(
                success=True,
                image_url=result.get("image_url")
            )
        else:
            return APIResponse(
                success=False,
                error_message=result.get("error", "Ошибка генерации")
            )
    
    def edit_image(self, request: EditRequest, image_url: str = None) -> APIResponse:
        """
        Редактирование существующего изображения
        
        Args:
            request: Параметры редактирования
            image_url: Публичный URL изображения (если уже загружено)
            
        Returns:
            APIResponse с результатом
        """
        # Если URL не предоставлен, нужно загрузить изображение
        if not image_url:
            return APIResponse(
                success=False,
                error_message="Требуется публичный URL изображения. Загрузите изображение на публичный хостинг."
            )
        
        # Используем указанный aspect ratio или по умолчанию "1:1"
        aspect_ratio = request.aspect_ratio or "1:1"
        
        data = {
            "prompt": request.prompt,
            "type": "IMAGETOIAMGE",
            "imageUrls": [image_url],
            "numImages": 1,
            "callBackUrl": self.DUMMY_CALLBACK,
            "image_size": aspect_ratio
        }
        
        # Создаем задачу
        task_id = self._create_task(self.GENERATE_URL, data)
        if not task_id:
            return APIResponse(
                success=False,
                error_message="Не удалось создать задачу редактирования"
            )
        
        # Ожидаем завершения
        result = self._get_task_status(task_id)
        
        if result.get("success"):
            return APIResponse(
                success=True,
                image_url=result.get("image_url")
            )
        else:
            return APIResponse(
                success=False,
                error_message=result.get("error", "Ошибка редактирования")
            )
    
    def combine_images(self, request: CombineRequest, image_urls: List[str] = None) -> APIResponse:
        """
        Комбинирование нескольких изображений через Pro API
        
        Args:
            request: Параметры комбинирования
            image_urls: Список публичных URL изображений (если уже загружены)
            
        Returns:
            APIResponse с результатом
        """
        if len(request.image_paths) > 8:
            return APIResponse(
                success=False,
                error_message="Максимум 8 изображений для комбинирования"
            )
        
        # Если URL не предоставлены, нужно загрузить изображения
        if not image_urls:
            return APIResponse(
                success=False,
                error_message="Требуются публичные URL изображений. Загрузите изображения на публичный хостинг."
            )
        
        if len(image_urls) != len(request.image_paths):
            return APIResponse(
                success=False,
                error_message="Количество URL не соответствует количеству изображений"
            )
        
        # Преобразуем разрешение
        resolution_map = {
            "1024": "1K",
            "2048": "2K",
            "4096": "4K"
        }
        resolution = resolution_map.get(request.resolution, "2K")
        
        # Используем указанный aspect ratio или по умолчанию "1:1"
        aspect_ratio = request.aspect_ratio or "1:1"
        
        data = {
            "prompt": request.prompt,
            "imageUrls": image_urls,
            "resolution": resolution,
            "callBackUrl": self.DUMMY_CALLBACK,
            "aspectRatio": aspect_ratio
        }
        
        # Создаем задачу
        task_id = self._create_task(self.GENERATE_PRO_URL, data)
        if not task_id:
            return APIResponse(
                success=False,
                error_message="Не удалось создать задачу комбинирования"
            )
        
        # Ожидаем завершения
        result = self._get_task_status(task_id)
        
        if result.get("success"):
            return APIResponse(
                success=True,
                image_url=result.get("image_url")
            )
        else:
            return APIResponse(
                success=False,
                error_message=result.get("error", "Ошибка комбинирования")
            )
    
    def check_balance(self) -> dict:
        """
        Проверка баланса кредитов
        
        Returns:
            Словарь с информацией о балансе
        """
        try:
            response = requests.get(
                self.CREDIT_URL,
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("code") == 200:
                    credits = result.get("data", 0)
                    return {
                        "success": True,
                        "credits": credits,
                        "message": f"Доступно кредитов: {credits}"
                    }
                else:
                    return {
                        "success": False,
                        "error": result.get("msg", "Неизвестная ошибка")
                    }
            else:
                return {
                    "success": False,
                    "error": f"Ошибка {response.status_code}: {response.text}"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
