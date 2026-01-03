# Быстрый деплой за 5 минут

## Шаг 1: GitHub репозиторий

```bash
git init
git add .
git commit -m "Ready for deployment"
git remote add origin https://github.com/your-username/your-repo.git
git push -u origin main
```

## Шаг 2: Railway (Backend) - 2 минуты

1. Откройте https://railway.app
2. New Project → Deploy from GitHub repo
3. Выберите репозиторий
4. Settings → Root Directory: `backend`
5. Variables → Добавьте:
   - `FLASK_ENV=production`
   - `CORS_ORIGINS=http://localhost:3000,http://localhost:5173`
6. Скопируйте URL (например: `https://your-app.up.railway.app`)

## Шаг 3: Vercel (Frontend) - 2 минуты

1. Откройте https://vercel.com
2. Add New Project → Import репозиторий
3. Settings:
   - Root Directory: `frontend`
   - Framework: Vite
4. Environment Variables:
   - `VITE_API_URL=https://your-app.up.railway.app/api`
5. Deploy

## Шаг 4: Обновить CORS - 1 минута

В Railway Variables обновите:
```
CORS_ORIGINS=https://your-app.vercel.app,http://localhost:3000,http://localhost:5173
```

Готово! 🎉

Ваш сайт доступен по адресу: `https://your-app.vercel.app`
