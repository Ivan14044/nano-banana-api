"""
API маршруты для Flask приложения
"""
from flask import Blueprint, request, jsonify, send_from_directory, current_app
from pathlib import Path
from datetime import datetime
import os
import threading

from .nanobanana_client import NanoBananaAPIClient
from .models import GenerationRequest, EditRequest, CombineRequest
from ..database.db_manager import DatabaseManager
from ..utils.image_utils import url_to_image, base64_to_image
from ..utils.image_uploader import upload_image

api_bp = Blueprint('api', __name__)

# Глобальные переменные для хранения клиентов и менеджеров БД
# В продакшене лучше использовать Flask session или Redis
api_clients = {}  # {api_key: NanoBananaAPIClient}
db_manager = DatabaseManager()


def get_api_client(api_key: str) -> NanoBananaAPIClient:
    """Получить или создать API клиент для ключа"""
    if api_key not in api_clients:
        api_clients[api_key] = NanoBananaAPIClient(api_key)
    return api_clients[api_key]


@api_bp.route('/balance', methods=['POST'])
def check_balance():
    """Проверка баланса кредитов"""
    try:
        data = request.json
        api_key = data.get('api_key')
        
        if not api_key:
            return jsonify({'success': False, 'error': 'API ключ не предоставлен'}), 400
        
        client = get_api_client(api_key)
        result = client.check_balance()
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/generate', methods=['POST'])
def generate_image():
    """Генерация изображения"""
    try:
        data = request.json
        api_key = data.get('api_key')
        
        if not api_key:
            return jsonify({'success': False, 'error': 'API ключ не предоставлен'}), 400
        
        # Создаем запрос
        gen_request = GenerationRequest(
            prompt=data.get('prompt', ''),
            model=data.get('model', 'flash'),
            resolution=data.get('resolution', '2048'),
            negative_prompt=data.get('negative_prompt'),
            num_images=data.get('num_images', 1),
            aspect_ratio=data.get('aspect_ratio', '1:1'),
            reference_images=data.get('reference_images')
        )
        
        if not gen_request.prompt:
            return jsonify({'success': False, 'error': 'Промпт не может быть пустым'}), 400
        
        client = get_api_client(api_key)
        
        # Загружаем референсные изображения если есть
        reference_urls = None
        if gen_request.reference_images:
            reference_urls = []
            for ref_path in gen_request.reference_images:
                # Путь должен быть относительным от uploads/user/
                full_path = Path(current_app.config['UPLOAD_FOLDER']) / Path(ref_path).name
                if full_path.exists():
                    url = upload_image(str(full_path))
                    if url:
                        reference_urls.append(url)
                    else:
                        return jsonify({
                            'success': False,
                            'error': f'Не удалось загрузить референсное изображение: {ref_path}'
                        }), 400
        
        # Генерируем изображение
        response = client.generate_image(gen_request, reference_urls)
        
        if response.success and response.image_url:
            # Сохраняем изображение на сервер
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"generated_{timestamp}.png"
            save_path = Path(current_app.config['GENERATED_FOLDER']) / filename
            
            crop_to_aspect = data.get('crop_to_aspect', False)
            success = url_to_image(
                response.image_url,
                str(save_path),
                aspect_ratio=gen_request.aspect_ratio,
                resolution=gen_request.resolution,
                crop_to_aspect=crop_to_aspect
            )
            
            if success:
                # Сохраняем в БД
                relative_path = f"generated/{filename}"
                gen_id = db_manager.add_generation(
                    gen_type="generate",
                    prompt=gen_request.prompt,
                    model=gen_request.model,
                    image_path=relative_path,
                    resolution=gen_request.resolution,
                    negative_prompt=gen_request.negative_prompt
                )
                
                return jsonify({
                    'success': True,
                    'image_url': f"/api/images/{relative_path}",
                    'image_path': relative_path,
                    'id': gen_id
                })
            else:
                return jsonify({'success': False, 'error': 'Ошибка сохранения изображения'}), 500
        else:
            return jsonify({
                'success': False,
                'error': response.error_message or 'Неизвестная ошибка генерации'
            }), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/edit', methods=['POST'])
def edit_image():
    """Редактирование изображения"""
    try:
        data = request.json
        api_key = data.get('api_key')
        
        if not api_key:
            return jsonify({'success': False, 'error': 'API ключ не предоставлен'}), 400
        
        image_path = data.get('image_path')  # Относительный путь от uploads/user/
        if not image_path:
            return jsonify({'success': False, 'error': 'Путь к изображению не предоставлен'}), 400
        
        # Полный путь к изображению
        full_image_path = Path(current_app.config['UPLOAD_FOLDER']) / Path(image_path).name
        
        if not full_image_path.exists():
            return jsonify({'success': False, 'error': 'Изображение не найдено'}), 404
        
        # Загружаем изображение на публичный хостинг
        public_url = upload_image(str(full_image_path))
        if not public_url:
            return jsonify({
                'success': False,
                'error': 'Не удалось загрузить изображение на публичный хостинг'
            }), 500
        
        # Создаем запрос
        edit_request = EditRequest(
            image_path=str(full_image_path),
            prompt=data.get('prompt', ''),
            model=data.get('model', 'flash'),
            resolution=data.get('resolution'),
            negative_prompt=data.get('negative_prompt'),
            aspect_ratio=data.get('aspect_ratio', '1:1')
        )
        
        if not edit_request.prompt:
            return jsonify({'success': False, 'error': 'Промпт не может быть пустым'}), 400
        
        client = get_api_client(api_key)
        response = client.edit_image(edit_request, public_url)
        
        if response.success and response.image_url:
            # Сохраняем изображение на сервер
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"edited_{timestamp}.png"
            save_path = Path(current_app.config['GENERATED_FOLDER']) / filename
            
            crop_to_aspect = data.get('crop_to_aspect', False)
            success = url_to_image(
                response.image_url,
                str(save_path),
                aspect_ratio=edit_request.aspect_ratio,
                resolution=edit_request.resolution,
                crop_to_aspect=crop_to_aspect
            )
            
            if success:
                # Сохраняем в БД
                relative_path = f"generated/{filename}"
                gen_id = db_manager.add_generation(
                    gen_type="edit",
                    prompt=edit_request.prompt,
                    model=edit_request.model,
                    image_path=relative_path,
                    resolution=edit_request.resolution,
                    negative_prompt=edit_request.negative_prompt
                )
                
                return jsonify({
                    'success': True,
                    'image_url': f"/api/images/{relative_path}",
                    'image_path': relative_path,
                    'id': gen_id
                })
            else:
                return jsonify({'success': False, 'error': 'Ошибка сохранения изображения'}), 500
        else:
            return jsonify({
                'success': False,
                'error': response.error_message or 'Неизвестная ошибка редактирования'
            }), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/combine', methods=['POST'])
def combine_images():
    """Комбинирование изображений"""
    try:
        data = request.json
        api_key = data.get('api_key')
        
        if not api_key:
            return jsonify({'success': False, 'error': 'API ключ не предоставлен'}), 400
        
        image_paths = data.get('image_paths', [])  # Список относительных путей
        if len(image_paths) < 2:
            return jsonify({'success': False, 'error': 'Нужно минимум 2 изображения'}), 400
        if len(image_paths) > 8:
            return jsonify({'success': False, 'error': 'Максимум 8 изображений'}), 400
        
        # Загружаем все изображения на публичный хостинг
        public_urls = []
        for image_path in image_paths:
            full_path = Path(current_app.config['UPLOAD_FOLDER']) / Path(image_path).name
            if not full_path.exists():
                return jsonify({
                    'success': False,
                    'error': f'Изображение не найдено: {image_path}'
                }), 404
            
            public_url = upload_image(str(full_path))
            if not public_url:
                return jsonify({
                    'success': False,
                    'error': f'Не удалось загрузить изображение на публичный хостинг: {image_path}'
                }), 500
            public_urls.append(public_url)
        
        # Создаем запрос
        combine_request = CombineRequest(
            image_paths=[str(Path(current_app.config['UPLOAD_FOLDER']) / Path(p).name) for p in image_paths],
            prompt=data.get('prompt', ''),
            model=data.get('model', 'pro'),
            resolution=data.get('resolution', '2048'),
            negative_prompt=data.get('negative_prompt'),
            aspect_ratio=data.get('aspect_ratio', '1:1')
        )
        
        if not combine_request.prompt:
            return jsonify({'success': False, 'error': 'Промпт не может быть пустым'}), 400
        
        client = get_api_client(api_key)
        response = client.combine_images(combine_request, public_urls)
        
        if response.success and response.image_url:
            # Сохраняем изображение на сервер
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"combined_{timestamp}.png"
            save_path = Path(current_app.config['GENERATED_FOLDER']) / filename
            
            crop_to_aspect = data.get('crop_to_aspect', False)
            success = url_to_image(
                response.image_url,
                str(save_path),
                aspect_ratio=combine_request.aspect_ratio,
                resolution=combine_request.resolution,
                crop_to_aspect=crop_to_aspect
            )
            
            if success:
                # Сохраняем в БД
                relative_path = f"generated/{filename}"
                gen_id = db_manager.add_generation(
                    gen_type="combine",
                    prompt=combine_request.prompt,
                    model=combine_request.model,
                    image_path=relative_path,
                    resolution=combine_request.resolution,
                    negative_prompt=combine_request.negative_prompt
                )
                
                return jsonify({
                    'success': True,
                    'image_url': f"/api/images/{relative_path}",
                    'image_path': relative_path,
                    'id': gen_id
                })
            else:
                return jsonify({'success': False, 'error': 'Ошибка сохранения изображения'}), 500
        else:
            return jsonify({
                'success': False,
                'error': response.error_message or 'Неизвестная ошибка комбинирования'
            }), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/upload', methods=['POST'])
def upload_file():
    """Загрузка файла на сервер"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'Файл не предоставлен'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'Имя файла пустое'}), 400
        
        # Проверяем расширение
        allowed_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.gif'}
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in allowed_extensions:
            return jsonify({
                'success': False,
                'error': f'Неподдерживаемый формат файла. Разрешенные: {", ".join(allowed_extensions)}'
            }), 400
        
        # Сохраняем файл
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{file.filename}"
        save_path = Path(current_app.config['UPLOAD_FOLDER']) / filename
        file.save(str(save_path))
        
        return jsonify({
            'success': True,
            'filename': filename,
            'path': f"user/{filename}",
            'url': f"/api/images/user/{filename}"
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/images/<path:filename>', methods=['GET'])
def get_image(filename):
    """Получить изображение"""
    try:
        # Безопасность: проверяем, что путь не выходит за пределы uploads
        safe_path = Path(filename)
        if '..' in str(safe_path) or safe_path.is_absolute():
            return jsonify({'error': 'Неверный путь'}), 400
        
        # Определяем папку на основе пути
        if filename.startswith('generated/'):
            directory = current_app.config['GENERATED_FOLDER']
            # Убираем префикс 'generated/' из имени файла
            file_name = filename.replace('generated/', '', 1)
            file_path = Path(directory) / file_name
        elif filename.startswith('user/'):
            directory = current_app.config['UPLOAD_FOLDER']
            # Убираем префикс 'user/' из имени файла
            file_name = filename.replace('user/', '', 1)
            file_path = Path(directory) / file_name
        else:
            # Пробуем найти в обеих папках по имени файла
            file_name = safe_path.name
            gen_path = Path(current_app.config['GENERATED_FOLDER']) / file_name
            user_path = Path(current_app.config['UPLOAD_FOLDER']) / file_name
            
            if gen_path.exists():
                directory = current_app.config['GENERATED_FOLDER']
                file_path = gen_path
            elif user_path.exists():
                directory = current_app.config['UPLOAD_FOLDER']
                file_path = user_path
            else:
                return jsonify({'error': 'Изображение не найдено'}), 404
        
        if not file_path.exists():
            return jsonify({'error': 'Изображение не найдено'}), 404
        
        return send_from_directory(str(directory), file_name)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/gallery', methods=['GET'])
def get_gallery():
    """Получить список генераций для галереи"""
    try:
        gen_type = request.args.get('type')
        search_query = request.args.get('search')
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        
        generations = db_manager.get_generations(
            limit=limit,
            offset=offset,
            gen_type=gen_type,
            search_query=search_query
        )
        
        # Преобразуем пути в URL
        for gen in generations:
            if gen.get('image_path'):
                gen['image_url'] = f"/api/images/{gen['image_path']}"
        
        return jsonify({
            'success': True,
            'generations': generations
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/gallery/<int:gen_id>', methods=['GET'])
def get_generation(gen_id):
    """Получить конкретную генерацию"""
    try:
        gen = db_manager.get_generation_by_id(gen_id)
        if not gen:
            return jsonify({'success': False, 'error': 'Генерация не найдена'}), 404
        
        if gen.get('image_path'):
            gen['image_url'] = f"/api/images/{gen['image_path']}"
        
        return jsonify({
            'success': True,
            'generation': gen
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/gallery/<int:gen_id>', methods=['DELETE'])
def delete_generation(gen_id):
    """Удалить генерацию"""
    try:
        gen = db_manager.get_generation_by_id(gen_id)
        if not gen:
            return jsonify({'success': False, 'error': 'Генерация не найдена'}), 404
        
        # Удаляем файл если существует
        image_path = gen.get('image_path')
        if image_path:
            if image_path.startswith('generated/'):
                file_path = Path(current_app.config['GENERATED_FOLDER']) / Path(image_path).name
            elif image_path.startswith('user/'):
                file_path = Path(current_app.config['UPLOAD_FOLDER']) / Path(image_path).name
            else:
                file_path = None
            
            if file_path and file_path.exists():
                try:
                    file_path.unlink()
                except Exception as e:
                    print(f"Ошибка удаления файла: {e}")
        
        # Удаляем из БД
        deleted = db_manager.delete_generation(gen_id)
        
        if deleted:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Не удалось удалить генерацию'}), 500
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/gallery/statistics', methods=['GET'])
def get_statistics():
    """Получить статистику по генерациям"""
    try:
        stats = db_manager.get_statistics()
        return jsonify({
            'success': True,
            'statistics': stats
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
