# Инструкция по развёртыванию на собственном сервере

Этот проект полностью независим от облачной платформы poehali.dev и может быть развёрнут на любом сервере с Python и Node.js.

## Архитектура

```
┌─────────────────┐
│   Nginx (80)    │  ← Пользователь
└────────┬────────┘
         │
    ┌────┴────────────────────┐
    │                         │
    ▼                         ▼
┌─────────────┐      ┌──────────────────┐
│  Frontend   │      │  Backend Python  │
│  (Vite)     │      │  (port 8000)     │
│  статика    │      └────────┬─────────┘
└─────────────┘               │
                              ▼
                      ┌───────────────┐
                      │  PostgreSQL   │
                      │  (TimeWeb)    │
                      └───────────────┘
```

## Требования

- **Сервер**: Ubuntu/Debian с root доступом
- **Python**: 3.9+
- **Node.js**: 18+
- **База данных**: PostgreSQL (например, TimeWeb Cloud)
- **Nginx**: для проксирования запросов

## Шаг 1: Подготовка сервера

```bash
# Установите необходимые пакеты
sudo apt update
sudo apt install -y python3 python3-pip python3-venv nginx nodejs npm git

# Клонируйте репозиторий (или загрузите через GitHub)
git clone <ваш-репозиторий>
cd knowledge-management-system
```

## Шаг 2: Настройка Backend (Python)

```bash
cd backend

# Запустите скрипт установки
chmod +x setup.sh
./setup.sh

# Создайте .env файл с реальными данными
cp .env.example .env
nano .env

# Добавьте строку подключения к вашей БД TimeWeb:
# DATABASE_CONNECTION_TIMEWEB=postgresql://user:pass@host:port/db
```

**Тестовый запуск backend:**
```bash
source venv/bin/activate
python3 run_local.py
```

Должно появиться:
```
🚀 Local backend server running on http://localhost:8000
Available endpoints:
  - /api/auth          -> backend/auth/
  - /api/db            -> backend/external-db/
  - /api/email         -> backend/email-notifications/
  - /api/password-reset -> backend/password-reset/
```

## Шаг 3: Настройка Frontend

```bash
cd ..  # Вернитесь в корень проекта

# Установите зависимости
npm install

# Соберите production build
npm run build

# Результат будет в папке dist/
```

## Шаг 4: Настройка Nginx

Создайте конфигурацию для вашего домена:

```bash
sudo nano /etc/nginx/sites-available/ab-education
```

Вставьте конфигурацию:

```nginx
server {
    listen 80;
    server_name ab-education.ru www.ab-education.ru;

    # Frontend статика
    root /var/www/knowledge-management-system/dist;
    index index.html;

    # Сжатие
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    # Frontend SPA маршрутизация
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Backend API прокси на Python сервер
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # CORS заголовки
        add_header Access-Control-Allow-Origin * always;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Content-Type, X-User-Id, X-Auth-Token, X-Session-Id" always;
        
        # OPTIONS preflight
        if ($request_method = OPTIONS) {
            return 204;
        }
    }

    # Кэширование статики
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

**Активируйте конфигурацию:**

```bash
sudo ln -s /etc/nginx/sites-available/ab-education /etc/nginx/sites-enabled/
sudo nginx -t  # Проверка конфигурации
sudo systemctl reload nginx
```

## Шаг 5: Автозапуск Backend (systemd)

Создайте systemd service для автоматического запуска Python backend:

```bash
sudo nano /etc/systemd/system/km-backend.service
```

Содержимое:

```ini
[Unit]
Description=Knowledge Management Backend Server
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/knowledge-management-system/backend
Environment="PATH=/var/www/knowledge-management-system/backend/venv/bin"
EnvironmentFile=/var/www/knowledge-management-system/backend/.env
ExecStart=/var/www/knowledge-management-system/backend/venv/bin/python3 /var/www/knowledge-management-system/backend/run_local.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

**Запустите сервис:**

```bash
sudo systemctl daemon-reload
sudo systemctl enable km-backend
sudo systemctl start km-backend
sudo systemctl status km-backend
```

## Шаг 6: SSL сертификат (опционально, но рекомендуется)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d ab-education.ru -d www.ab-education.ru
```

Certbot автоматически настроит HTTPS и добавит редирект с HTTP.

## Проверка работы

1. **Frontend**: Откройте http://ab-education.ru — должна загрузиться страница входа
2. **Backend API**: Проверьте http://ab-education.ru/api/auth?action=check — должен вернуть JSON
3. **Логи Backend**: `sudo journalctl -u km-backend -f`
4. **Логи Nginx**: `sudo tail -f /var/log/nginx/error.log`

## Обновление проекта

Когда вы обновляете код через poehali.dev и пушите в GitHub:

```bash
cd /var/www/knowledge-management-system
git pull origin main

# Пересоберите frontend
npm install
npm run build

# Перезапустите backend (если были изменения)
sudo systemctl restart km-backend

# Перезагрузите nginx
sudo systemctl reload nginx
```

## Структура проекта после развёртывания

```
/var/www/knowledge-management-system/
├── backend/
│   ├── venv/              # Python виртуальное окружение
│   ├── .env               # Переменные окружения (БД)
│   ├── run_local.py       # Локальный сервер Python
│   ├── auth/              # Функция авторизации
│   ├── external-db/       # Функция работы с БД
│   └── ...
├── dist/                  # Собранный frontend (nginx раздаёт отсюда)
├── src/                   # Исходники frontend
└── node_modules/          # Зависимости Node.js
```

## Troubleshooting

### Backend не запускается
```bash
# Проверьте логи
sudo journalctl -u km-backend -n 50

# Проверьте .env файл
cat backend/.env

# Проверьте подключение к БД
psql "postgresql://user:pass@host:port/db"
```

### 502 Bad Gateway
```bash
# Проверьте, запущен ли backend
sudo systemctl status km-backend

# Проверьте, слушает ли порт 8000
sudo netstat -tulpn | grep 8000
```

### CORS ошибки
```bash
# Проверьте nginx конфигурацию
sudo nginx -t
sudo systemctl reload nginx
```

### База данных не подключается
- Проверьте строку подключения в `backend/.env`
- Убедитесь, что IP сервера добавлен в whitelist TimeWeb Cloud
- Проверьте SSL сертификат (должен скачаться автоматически при первом запуске)

## Мониторинг

```bash
# Статус всех сервисов
sudo systemctl status km-backend nginx

# Логи Backend
sudo journalctl -u km-backend -f

# Логи Nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Использование ресурсов
htop
```

---

**Готово!** Теперь ваш проект работает полностью автономно на вашем сервере без зависимости от poehali.dev. 🚀
