# Деплой на Vercel + Fly.io (бесплатный вариант)

## Архитектура

- **Frontend (React)** → Vercel (бесплатный домен: `your-app.vercel.app`)
- **Backend (Flask)** → Fly.io (бесплатный домен: `your-app.fly.dev`)
- **Один репозиторий** с монорепо структурой

## Предварительные требования

1. Аккаунт на [GitHub](https://github.com)
2. Аккаунт на [Vercel](https://vercel.com) (бесплатный)
3. Аккаунт на [Fly.io](https://fly.io) (бесплатный tier)
4. Установленный [Fly CLI](https://fly.io/docs/getting-started/installing-flyctl/)

## Шаг 1: Подготовка репозитория

Код уже загружен в GitHub репозиторий: `https://github.com/Ivan14044/nano-banana-api`

## Шаг 2: Деплой бэкенда на Fly.io

1. Установите Fly CLI (если еще не установлен):
   ```bash
   # Windows (PowerShell)
   powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"
   ```

2. Войдите в Fly.io:
   ```bash
   fly auth login
   ```

3. Перейдите в директорию backend:
   ```bash
   cd backend
   ```

4. Создайте Fly приложение:
   ```bash
   fly launch
   ```
   - Выберите регион
   - Не создавайте PostgreSQL (нажмите "n")
   - Не создавайте Redis (нажмите "n")

5. Откройте файл `fly.toml` и обновите его:
   ```toml
   app = "your-app-name"
   primary_region = "iad"  # или другой регион

   [build]

   [http_service]
     internal_port = 8080
     force_https = true
     auto_stop_machines = true
     auto_start_machines = true
     min_machines_running = 0
     processes = ["app"]

   [[services]]
     protocol = "tcp"
     internal_port = 8080
     processes = ["app"]

     [[services.ports]]
       port = 80
       handlers = ["http"]
       force_https = true

     [[services.ports]]
       port = 443
       handlers = ["tls", "http"]
   ```

6. Создайте файл `Dockerfile` в директории `backend`:
   ```dockerfile
   FROM python:3.11-slim

   WORKDIR /app

   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt

   COPY . .

   ENV PORT=8080
   CMD gunicorn -w 2 -b 0.0.0.0:$PORT --timeout 120 app:app
   ```

7. Установите переменные окружения:
   ```bash
   fly secrets set FLASK_ENV=production
   fly secrets set CORS_ORIGINS=http://localhost:3000,http://localhost:5173
   ```

8. Деплойте:
   ```bash
   fly deploy
   ```

9. После деплоя получите URL:
   ```bash
   fly status
   ```
   URL будет вида: `https://your-app-name.fly.dev`

## Шаг 3: Деплой фронтенда на Vercel

(См. инструкции в DEPLOY_RENDER.md, шаг 3)

## Шаг 4: Обновление CORS

```bash
fly secrets set CORS_ORIGINS=https://your-app.vercel.app,http://localhost:3000,http://localhost:5173
```

## Особенности Fly.io

- ✅ Бесплатный tier с 3 shared-cpu-1x VMs
- ✅ Автоматический HTTPS
- ✅ Нет "засыпания" сервисов
- ✅ Быстрый отклик
