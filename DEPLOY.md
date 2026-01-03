# Инструкция по деплою NanoBanana Pro Web

## Варианты деплоя

### Вариант 1: Vercel + Railway (платный после пробного периода)
См. инструкции ниже.

### Вариант 2: Vercel + Render.com (бесплатный) ⭐ Рекомендуется
См. [DEPLOY_RENDER.md](DEPLOY_RENDER.md) - подробные инструкции для бесплатного деплоя.

### Вариант 3: Vercel + Fly.io (бесплатный)
См. [DEPLOY_FLY.md](DEPLOY_FLY.md) - инструкции для Fly.io.

## Архитектура (Railway вариант)

- **Frontend (React)** → Vercel (бесплатный домен: `your-app.vercel.app`)
- **Backend (Flask)** → Railway (бесплатный домен: `your-app.up.railway.app`)
- **Один репозиторий** с монорепо структурой

## Предварительные требования

1. Аккаунт на [GitHub](https://github.com)
2. Аккаунт на [Vercel](https://vercel.com) (бесплатный)
3. Аккаунт на [Railway](https://railway.app) (бесплатный, 500 часов/месяц)

## Шаг 1: Подготовка репозитория

1. Создайте новый репозиторий на GitHub
2. Загрузите код в репозиторий:

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/your-username/your-repo.git
git push -u origin main
```

## Шаг 2: Деплой бэкенда на Railway

1. Перейдите на [Railway](https://railway.app) и войдите через GitHub
2. Нажмите "New Project"
3. Выберите "Deploy from GitHub repo"
4. Выберите ваш репозиторий
5. В настройках проекта:
   - **Root Directory**: `backend`
   - Railway автоматически определит Python проект

6. Настройте переменные окружения в Railway:
   - Перейдите в Settings → Variables
   - Добавьте:
     ```
     FLASK_ENV=production
     CORS_ORIGINS=http://localhost:3000,http://localhost:5173
     ```
   - `PORT` устанавливается автоматически Railway

7. После деплоя Railway предоставит URL вида: `https://your-app.up.railway.app`
8. Скопируйте этот URL - он понадобится для настройки фронтенда

## Шаг 3: Деплой фронтенда на Vercel

1. Перейдите на [Vercel](https://vercel.com) и войдите через GitHub
2. Нажмите "Add New Project"
3. Импортируйте ваш репозиторий
4. В настройках проекта:
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build` (или оставьте автоматическое определение)
   - **Output Directory**: `dist`
   - **Install Command**: `npm install` (или оставьте автоматическое определение)

5. Настройте переменные окружения:
   - Перейдите в Settings → Environment Variables
   - Добавьте:
     ```
     VITE_API_URL=https://your-app.up.railway.app/api
     ```
     (Замените на ваш Railway URL)

6. Нажмите "Deploy"
7. После деплоя Vercel предоставит URL вида: `https://your-app.vercel.app`

## Шаг 4: Обновление CORS на бэкенде

1. Вернитесь в Railway
2. Обновите переменную окружения `CORS_ORIGINS`:
   ```
   CORS_ORIGINS=https://your-app.vercel.app,http://localhost:3000,http://localhost:5173
   ```
   (Замените на ваш Vercel URL)

3. Railway автоматически перезапустит приложение

## Шаг 5: Проверка работы

1. Откройте ваш Vercel URL в браузере
2. Введите API ключ от nanobananaapi.ai
3. Попробуйте сгенерировать изображение
4. Проверьте, что все функции работают

## Обновление кода

После каждого push в GitHub:
- **Vercel** автоматически пересоберет и задеплоит фронтенд
- **Railway** автоматически пересоберет и задеплоит бэкенд

## Переменные окружения

### Vercel (Frontend)

- `VITE_API_URL` - URL бэкенда на Railway (например: `https://your-app.up.railway.app/api`)

### Railway (Backend)

- `FLASK_ENV=production` - режим продакшена
- `PORT` - устанавливается автоматически Railway
- `CORS_ORIGINS` - разрешенные домены через запятую (добавьте Vercel URL)

## Проблемы и решения

### CORS ошибки

Если видите CORS ошибки в консоли браузера:
1. Убедитесь, что `CORS_ORIGINS` в Railway содержит ваш Vercel URL
2. Проверьте, что URL начинается с `https://`
3. Перезапустите приложение в Railway

### Backend не отвечает

1. Проверьте логи в Railway Dashboard
2. Убедитесь, что переменные окружения установлены
3. Проверьте, что порт настроен правильно

### Frontend не подключается к API

1. Проверьте переменную `VITE_API_URL` в Vercel
2. Убедитесь, что URL заканчивается на `/api`
3. Проверьте, что бэкенд доступен по этому URL

## Бесплатные лимиты

### Vercel
- Неограниченное количество деплоев
- 100GB bandwidth/месяц
- Автоматический HTTPS

### Railway
- 500 часов/месяц бесплатно
- $5 кредитов/месяц
- Автоматический HTTPS

## Подключение кастомного домена

### Vercel
1. Перейдите в Settings → Domains
2. Добавьте ваш домен
3. Следуйте инструкциям по настройке DNS

### Railway
1. Перейдите в Settings → Domains
2. Добавьте ваш домен
3. Настройте CNAME запись в DNS

## Поддержка

При возникновении проблем проверьте:
- Логи в Vercel Dashboard
- Логи в Railway Dashboard
- Консоль браузера (F12)
- Правильность переменных окружения
