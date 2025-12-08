# 🚀 Инструкция по деплою API на сервер

## 1. Подключись к серверу
```bash
ssh root@89.169.47.23
# Пароль: p^o9L2P?UP^+n3
```

## 2. Установи необходимые пакеты
```bash
apt update
apt install -y python3 python3-pip python3-venv nginx postgresql-client
```

## 3. Создай структуру проекта
```bash
mkdir -p /var/www/giftbox
cd /var/www/giftbox
```

## 4. Загрузи код API на сервер

### Вариант A: Через GitHub (рекомендуется)
```bash
# Если у тебя есть GitHub репозиторий
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git .
```

### Вариант B: Через SCP с твоего компьютера
```bash
# На твоём компьютере (в папке проекта):
scp server/app.py root@89.169.47.23:/var/www/giftbox/
scp server/requirements.txt root@89.169.47.23:/var/www/giftbox/
scp server/gunicorn.conf.py root@89.169.47.23:/var/www/giftbox/
```

### Вариант C: Создай файлы вручную
```bash
# На сервере создай app.py:
nano /var/www/giftbox/app.py
# Скопируй содержимое из server/app.py и сохрани (Ctrl+O, Enter, Ctrl+X)

# Создай requirements.txt:
nano /var/www/giftbox/requirements.txt
# Скопируй содержимое из server/requirements.txt и сохрани
```

## 5. Настрой Python окружение
```bash
cd /var/www/giftbox

# Создай виртуальное окружение
python3 -m venv venv

# Активируй его
source venv/bin/activate

# Установи зависимости
pip install -r requirements.txt
```

## 6. Проверь подключение к БД
```bash
# Проверь, что PostgreSQL доступен
psql -h localhost -U giftbox_user -d giftbox -c "SELECT COUNT(*) FROM gift_boxes;"
# Пароль: Ltnfh123
```

## 7. Создай systemd сервис для автозапуска
```bash
cat > /etc/systemd/system/giftbox.service << 'EOF'
[Unit]
Description=Giftbox API Service
After=network.target postgresql.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/var/www/giftbox
Environment="PATH=/var/www/giftbox/venv/bin"
ExecStart=/var/www/giftbox/venv/bin/gunicorn --config gunicorn.conf.py app:app
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF
```

## 8. Создай папки для логов
```bash
mkdir -p /var/log/giftbox
chown www-data:www-data /var/log/giftbox
```

## 9. Настрой права доступа
```bash
chown -R www-data:www-data /var/www/giftbox
chmod -R 755 /var/www/giftbox
```

## 10. Запусти сервис
```bash
systemctl daemon-reload
systemctl enable giftbox
systemctl start giftbox
systemctl status giftbox
```

## 11. Настрой nginx
```bash
cat > /etc/nginx/sites-available/ab-education.ru << 'EOF'
server {
    listen 80;
    server_name ab-education.ru www.ab-education.ru;

    # API proxy
    location /api/ {
        proxy_pass http://127.0.0.1:5000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Frontend (статические файлы)
    location / {
        root /var/www/giftbox/dist;
        try_files $uri $uri/ /index.html;
    }
}
EOF

# Включи конфиг
ln -sf /etc/nginx/sites-available/ab-education.ru /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Проверь конфиг
nginx -t

# Перезапусти nginx
systemctl restart nginx
```

## 12. Проверь работу API
```bash
# Проверь health endpoint
curl http://localhost:5000/api/health

# Проверь через nginx
curl http://89.169.47.23/api/health

# Или через домен (если настроен DNS)
curl http://ab-education.ru/api/health
```

## 13. Настрой SSL (опционально, но рекомендуется)
```bash
apt install -y certbot python3-certbot-nginx
certbot --nginx -d ab-education.ru -d www.ab-education.ru
```

## Управление сервисом
```bash
# Остановить
systemctl stop giftbox

# Запустить
systemctl start giftbox

# Перезапустить
systemctl restart giftbox

# Посмотреть статус
systemctl status giftbox

# Посмотреть логи
tail -f /var/log/giftbox/error.log
tail -f /var/log/giftbox/access.log
journalctl -u giftbox -f
```

## Troubleshooting

### API не запускается
```bash
# Проверь логи
journalctl -u giftbox -n 50
cat /var/log/giftbox/error.log

# Проверь права
ls -la /var/www/giftbox

# Попробуй запустить вручную
cd /var/www/giftbox
source venv/bin/activate
python3 app.py
```

### Ошибка подключения к БД
```bash
# Проверь, что PostgreSQL запущен
systemctl status postgresql

# Проверь подключение
psql -h localhost -U giftbox_user -d giftbox
```

### nginx не работает
```bash
# Проверь конфиг
nginx -t

# Посмотри логи
tail -f /var/log/nginx/error.log
```

## Готово! 🎉
Теперь твой API доступен по адресу:
- http://ab-education.ru/api/health
- http://ab-education.ru/api/boxes
- http://ab-education.ru/api/orders
