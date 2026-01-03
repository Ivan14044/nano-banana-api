# Деплой на Vercel + Render.com (бесплатный вариант)

## Архитектура

- **Frontend (React)** → Vercel (бесплатный домен: `your-app.vercel.app`)
- **Backend (Flask)** → Render.com (бесплатный домен: `your-app.onrender.com`)
- **Один репозиторий** с монорепо структурой

## Предварительные требования

1. Аккаунт на [GitHub](https://github.com)
2. Аккаунт на [Vercel](https://vercel.com) (бесплатный)
3. Аккаунт на [Render.com](https://render.com) (бесплатный tier)

## Шаг 1: Подготовка репозитория

Код уже загружен в GitHub репозиторий: `https://github.com/Ivan14044/nano-banana-api`

## Шаг 2: Деплой бэкенда на Render.com

1. Перейдите на [Render.com](https://render.com) и войдите через GitHub
2. Нажмите "New +" → "Web Service"
3. Выберите "Build and deploy from a Git repository"
4. Подключите ваш репозиторий `nano-banana-api`
5. В настройках проекта:
   - **Name**: `nanobanana-backend` (или любое другое имя)
   - **Region**: Выберите ближайший регион
   - **Branch**: `main`
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn -w 2 -b 0.0.0.0:$PORT --timeout 120 app:app`

6. Настройте переменные окружения:
   - Нажмите "Advanced" → "Add Environment Variable"
   - Добавьте:
     ```
     FLASK_ENV=production
     CORS_ORIGINS=http://localhost:3000,http://localhost:5173
     ```
   - `PORT` устанавливается автоматически Render

7. Выберите **Free** план
8. Нажмите "Create Web Service"
9. После деплоя Render предоставит URL вида: `https://nanobanana-backend.onrender.com`
10. Скопируйте этот URL - он понадобится для настройки фронтенда

**Важно:** На бесплатном плане Render:
- Сервис "засыпает" после 15 минут неактивности
- Первый запрос после пробуждения может занять 30-60 секунд
- Это нормально для бесплатного tier

## Шаг 3: Деплой фронтенда на Vercel

1. Перейдите на [Vercel](https://vercel.com) и войдите через GitHub
2. Нажмите "Add New Project"
3. Импортируйте ваш репозиторий `nano-banana-api`
4. В настройках проекта:
   - **Framework Preset**: Vite (определяется автоматически)
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build` (автоматически)
   - **Output Directory**: `dist` (автоматически)
   - **Install Command**: `npm install` (автоматически)

5. Настройте переменные окружения:
   - Перейдите в Settings → Environment Variables
   - Добавьте:
     ```
     VITE_API_URL=https://nanobanana-backend.onrender.com/api
     ```
     (Замените на ваш Render URL)

6. Нажмите "Deploy"
7. После деплоя Vercel предоставит URL вида: `https://your-app.vercel.app`

## Шаг 4: Обновление CORS на бэкенде

1. Вернитесь в Render.com
2. Перейдите в ваш Web Service → Environment
3. Обновите переменную `CORS_ORIGINS`:
   ```
   CORS_ORIGINS=https://your-app.vercel.app,http://localhost:3000,http://localhost:5173
   ```
   (Замените на ваш Vercel URL)

4. Render автоматически перезапустит сервис

## Шаг 5: Проверка работы

1. Откройте ваш Vercel URL в браузере
2. Введите API ключ от nanobananaapi.ai
3. Попробуйте сгенерировать изображение
4. Первый запрос может занять время (если сервис "спал")

## Обновление кода

После каждого push в GitHub:
- **Vercel** автоматически пересоберет и задеплоит фронтенд
- **Render** автоматически пересоберет и задеплоит бэкенд

## Переменные окружения

### Vercel (Frontend)

- `VITE_API_URL` - URL бэкенда на Render (например: `https://nanobanana-backend.onrender.com/api`)

### Render (Backend)

- `FLASK_ENV=production` - режим продакшена
- `PORT` - устанавливается автоматически Render
- `CORS_ORIGINS` - разрешенные домены через запятую (добавьте Vercel URL)

## Особенности бесплатного плана Render

- ✅ Бесплатный HTTPS
- ✅ Автоматический деплой из GitHub
- ⚠️ Сервис "засыпает" после 15 минут неактивности
- ⚠️ Первый запрос после пробуждения может занять 30-60 секунд
- ⚠️ Ограничение на CPU и память

## Проблемы и решения

### CORS ошибки

Если видите CORS ошибки:
1. Убедитесь, что `CORS_ORIGINS` в Render содержит ваш Vercel URL
2. Проверьте, что URL начинается с `https://`
3. Дождитесь перезапуска сервиса в Render

### Backend не отвечает

1. Проверьте логи в Render Dashboard
2. Убедитесь, что переменные окружения установлены
3. Проверьте, что сервис не "спит" (сделайте запрос к `/health`)

### Медленный первый запрос

Это нормально для бесплатного плана Render. Сервис просыпается за 30-60 секунд.

## Подключение кастомного домена

### Vercel
1. Перейдите в Settings → Domains
2. Добавьте ваш домен
3. Следуйте инструкциям по настройке DNS

### Render
1. Перейдите в Settings → Custom Domains
2. Добавьте ваш домен
3. Настройте CNAME запись в DNS
