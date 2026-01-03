"""
Главный Flask приложение для NanoBanana Pro Web
"""
from flask import Flask
from flask_cors import CORS
from pathlib import Path
import os

# Импортируем маршруты
from api.routes import api_bp


def create_app():
    """Создание и настройка Flask приложения"""
    app = Flask(__name__)
    
    # Получаем разрешенные origins из переменных окружения
    allowed_origins = os.getenv(
        'CORS_ORIGINS',
        'http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173'
    ).split(',')
    
    # Настройка CORS для работы с React фронтендом
    CORS(app, resources={
        r"/api/*": {
            "origins": allowed_origins,
            "methods": ["GET", "POST", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # Создаем необходимые папки
    base_dir = Path(__file__).parent
    uploads_dir = base_dir / "uploads"
    uploads_generated_dir = uploads_dir / "generated"
    uploads_user_dir = uploads_dir / "user"
    data_dir = base_dir / "data"
    
    for directory in [uploads_dir, uploads_generated_dir, uploads_user_dir, data_dir]:
        directory.mkdir(parents=True, exist_ok=True)
    
    # Регистрируем blueprint для API
    app.register_blueprint(api_bp, url_prefix="/api")
    
    # Health check endpoint для Railway
    @app.route('/health')
    def health():
        return {'status': 'ok'}, 200
    
    # Настройка для загрузки файлов
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB максимум
    app.config['UPLOAD_FOLDER'] = str(uploads_user_dir)
    app.config['GENERATED_FOLDER'] = str(uploads_generated_dir)
    app.config['DATA_FOLDER'] = str(data_dir)
    
    return app


# Создаем экземпляр приложения для Gunicorn
app = create_app()

if __name__ == "__main__":
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') != 'production'
    app.run(debug=debug, host="0.0.0.0", port=port)
