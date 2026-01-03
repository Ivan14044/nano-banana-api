# NanoBanana Pro Web - Веб-версия приложения

Веб-версия десктопного приложения NanoBanana Pro для генерации и редактирования изображений через NanoBanana API.

## Структура проекта

```
nanobanana-web/
├── backend/                    # Flask бэкенд
│   ├── app.py                 # Главный Flask app
│   ├── api/                   # API эндпоинты
│   │   ├── routes.py          # Все API маршруты
│   │   ├── nanobanana_client.py  # Клиент NanoBanana API
│   │   └── models.py          # Модели данных
│   ├── database/              # База данных
│   │   └── db_manager.py      # Управление БД
│   ├── utils/                 # Утилиты
│   │   ├── image_uploader.py  # Загрузка на публичные хостинги
│   │   └── image_utils.py     # Работа с изображениями
│   ├── uploads/               # Загруженные изображения
│   │   ├── generated/         # Сгенерированные изображения
│   │   └── user/              # Загруженные пользователем
│   ├── data/                  # База данных
│   │   └── history.db         # SQLite база данных
│   └── requirements.txt       # Зависимости бэкенда
│
└── frontend/                    # React фронтенд
    ├── src/
    │   ├── components/        # React компоненты
    │   │   ├── ApiSettings.jsx
    │   │   ├── GenerationTab.jsx
    │   │   ├── EditingTab.jsx
    │   │   ├── CombineTab.jsx
    │   │   ├── GalleryTab.jsx
    │   │   └── ImageViewer.jsx
    │   ├── services/          # API клиент
    │   │   └── api.js         # Axios клиент
    │   ├── App.jsx            # Главный компонент
    │   └── main.jsx           # Точка входа
    ├── package.json
    └── vite.config.js
```

## Установка и запуск

### Требования

- Python 3.8+
- Node.js 16+
- npm или yarn

### Бэкенд

1. Перейдите в папку `backend`:
```bash
cd backend
```

2. Создайте виртуальное окружение (рекомендуется):
```bash
python -m venv venv
source venv/bin/activate  # На Windows: venv\Scripts\activate
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Запустите Flask сервер:
```bash
python app.py
```

Сервер будет доступен по адресу `http://localhost:5000`

### Фронтенд

1. Перейдите в папку `frontend`:
```bash
cd frontend
```

2. Установите зависимости:
```bash
npm install
```

3. Запустите dev сервер:
```bash
npm run dev
```

Приложение будет доступно по адресу `http://localhost:3000`

## Использование

1. Откройте приложение в браузере (`http://localhost:3000`)
2. Введите ваш API ключ от [nanobananaapi.ai](https://nanobananaapi.ai) в поле "API ключ"
3. Нажмите "Сохранить" для сохранения ключа
4. При необходимости проверьте баланс кредитов
5. Используйте вкладки для:
   - **Генерация** - создание изображений по текстовому описанию
   - **Редактирование** - модификация существующих изображений
   - **Комбинирование** - объединение нескольких изображений
   - **Галерея** - просмотр всех сгенерированных изображений

## API эндпоинты

- `POST /api/balance` - проверка баланса
- `POST /api/generate` - генерация изображения
- `POST /api/edit` - редактирование изображения
- `POST /api/combine` - комбинирование изображений
- `POST /api/upload` - загрузка файла на сервер
- `GET /api/gallery` - получение списка генераций
- `GET /api/gallery/<id>` - получение конкретной генерации
- `DELETE /api/gallery/<id>` - удаление генерации
- `GET /api/gallery/statistics` - получение статистики
- `GET /api/images/<path>` - получение изображения

## Развертывание

### Разработка

- Бэкенд: Flask dev server на порту 5000
- Фронтенд: Vite dev server на порту 3000

### Продакшен

Для продакшена рекомендуется:

1. **Бэкенд**: Использовать Gunicorn или uWSGI
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:create_app()
```

2. **Фронтенд**: Собрать статические файлы
```bash
cd frontend
npm run build
```

3. **Отдача статики**: Настроить nginx для отдачи статики фронтенда и проксирования API запросов на Flask

## Особенности

- Полностью асинхронная работа с NanoBanana API (polling каждые 3 секунды)
- Автоматическая загрузка изображений на публичные хостинги (0x0.st, tmpfiles.org)
- Хранение истории генераций в SQLite
- Темная тема интерфейса
- Полностью русскоязычный интерфейс

## Безопасность

- API ключ хранится в localStorage браузера
- Валидация загружаемых файлов (только изображения)
- Ограничение размера файлов (16MB)
- Санитизация путей к файлам

## Лицензия

Этот проект создан для личного использования.
