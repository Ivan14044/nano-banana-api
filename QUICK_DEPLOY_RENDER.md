# Быстрый деплой на Render.com (5 минут)

## Шаг 1: Render.com (Backend) - 3 минуты

1. Откройте https://render.com
2. New + → Web Service
3. Подключите репозиторий `nano-banana-api`
4. Настройки:
   - **Name**: `nanobanana-backend`
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn -w 2 -b 0.0.0.0:$PORT --timeout 120 app:app`
   - **Plan**: Free
5. Environment Variables:
   - `FLASK_ENV=production`
   - `CORS_ORIGINS=http://localhost:3000,http://localhost:5173`
6. Create Web Service
7. Скопируйте URL (например: `https://nanobanana-backend.onrender.com`)

## Шаг 2: Vercel (Frontend) - 2 минуты

1. Откройте https://vercel.com
2. Add New Project → Import `nano-banana-api`
3. Настройки:
   - **Root Directory**: `frontend`
4. Environment Variables:
   - `VITE_API_URL=https://nanobanana-backend.onrender.com/api`
5. Deploy

## Шаг 3: Обновить CORS - 1 минута

В Render.com → Environment:
```
CORS_ORIGINS=https://your-app.vercel.app,http://localhost:3000,http://localhost:5173
```

Готово! 🎉

**Примечание:** На бесплатном плане Render сервис "засыпает" после 15 минут неактивности. Первый запрос может занять 30-60 секунд.
