# Быстрый старт - NanoBanana Pro Web

## Быстрая установка

### 1. Бэкенд (Flask)

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Бэкенд запустится на `http://localhost:5000`

### 2. Фронтенд (React)

В новом терминале:

```bash
cd frontend
npm install
npm run dev
```

Фронтенд запустится на `http://localhost:3000`

## Первое использование

1. Откройте `http://localhost:3000` в браузере
2. Введите ваш API ключ от nanobananaapi.ai
3. Нажмите "Сохранить"
4. Начните генерировать изображения!

## Структура проекта

- `backend/` - Flask API сервер
- `frontend/` - React веб-приложение
- `backend/uploads/` - загруженные изображения
- `backend/data/` - база данных SQLite

## Возможности

✅ Генерация изображений по текстовому описанию
✅ Редактирование существующих изображений
✅ Комбинирование нескольких изображений
✅ Галерея всех сгенерированных изображений
✅ Темная тема интерфейса
✅ Полностью русскоязычный интерфейс
