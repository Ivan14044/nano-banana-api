# Переменные окружения

## Vercel (Frontend)

В настройках проекта Vercel → Settings → Environment Variables добавьте:

```
VITE_API_URL=https://your-app.up.railway.app/api
```

**Важно:** Замените `your-app.up.railway.app` на ваш реальный Railway URL после деплоя бэкенда.

## Railway (Backend)

В настройках проекта Railway → Variables добавьте:

```
FLASK_ENV=production
CORS_ORIGINS=https://your-app.vercel.app,http://localhost:3000,http://localhost:5173
```

**Важно:** 
- Замените `your-app.vercel.app` на ваш реальный Vercel URL после деплоя фронтенда
- `PORT` устанавливается автоматически Railway, не нужно добавлять вручную

## Порядок настройки

1. Сначала деплойте backend на Railway и получите URL
2. Затем деплойте frontend на Vercel с переменной `VITE_API_URL`
3. После получения Vercel URL обновите `CORS_ORIGINS` в Railway
