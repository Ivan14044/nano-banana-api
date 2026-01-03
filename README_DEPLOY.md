# Быстрый деплой на Vercel и Railway

## Быстрая инструкция

### 1. Подготовка

```bash
# Убедитесь, что код загружен в GitHub репозиторий
git add .
git commit -m "Ready for deployment"
git push
```

### 2. Деплой Backend на Railway

1. Откройте [railway.app](https://railway.app)
2. Войдите через GitHub
3. New Project → Deploy from GitHub repo
4. Выберите репозиторий
5. В настройках:
   - **Root Directory**: `backend`
6. В Variables добавьте:
   ```
   FLASK_ENV=production
   CORS_ORIGINS=http://localhost:3000,http://localhost:5173
   ```
7. Скопируйте Railway URL (например: `https://your-app.up.railway.app`)

### 3. Деплой Frontend на Vercel

1. Откройте [vercel.com](https://vercel.com)
2. Войдите через GitHub
3. Add New Project → Import репозиторий
4. В настройках:
   - **Root Directory**: `frontend`
   - **Framework**: Vite
5. В Environment Variables добавьте:
   ```
   VITE_API_URL=https://your-app.up.railway.app/api
   ```
   (Замените на ваш Railway URL)
6. Deploy

### 4. Обновите CORS

В Railway Variables обновите:
```
CORS_ORIGINS=https://your-app.vercel.app,http://localhost:3000,http://localhost:5173
```
(Замените на ваш Vercel URL)

Готово! Приложение доступно по адресу Vercel.
