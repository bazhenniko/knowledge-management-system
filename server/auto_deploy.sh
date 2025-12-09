#!/bin/bash
# 🚀 Автоматическая установка Giftbox API на сервер
# Использование: bash auto_deploy.sh

set -e  # Остановить при ошибке

echo "🚀 Начинаю установку Giftbox API..."

# Цвета для вывода
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 1. Установка необходимых пакетов
echo -e "${BLUE}📦 Устанавливаю необходимые пакеты...${NC}"
apt update
apt install -y python3 python3-pip python3-venv nginx postgresql-client

# 2. Создание структуры проекта
echo -e "${BLUE}📁 Создаю структуру проекта...${NC}"
mkdir -p /var/www/giftbox
cd /var/www/giftbox

# 3. Создание app.py
echo -e "${BLUE}📝 Создаю app.py...${NC}"
cat > /var/www/giftbox/app.py << 'EOFAPP'
#!/usr/bin/env python3
"""
API Server для работы с базой данных giftbox
Запускается через Gunicorn на порту 5000
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
import os

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Конфигурация базы данных
DB_CONFIG = {
    'host': 'localhost',
    'database': 'giftbox',
    'user': 'giftbox_user',
    'password': 'Ltnfh123'
}

def get_db_connection():
    """Создать подключение к БД"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        raise

# Health check
@app.route('/api/health', methods=['GET'])
def health():
    """Проверка работоспособности API"""
    try:
        conn = get_db_connection()
        conn.close()
        return jsonify({
            'status': 'ok',
            'message': 'API работает, подключение к БД успешно'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# Получить все подарочные коробки
@app.route('/api/boxes', methods=['GET'])
def get_boxes():
    """Получить список всех подарочных коробок"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute('''
            SELECT id, title, description, price, image_url, created_at
            FROM gift_boxes
            ORDER BY created_at DESC
        ''')
        
        boxes = cur.fetchall()
        cur.close()
        conn.close()
        
        return jsonify(boxes)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Получить одну коробку по ID
@app.route('/api/boxes/<int:box_id>', methods=['GET'])
def get_box(box_id):
    """Получить информацию о конкретной коробке"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute('''
            SELECT id, title, description, price, image_url, created_at
            FROM gift_boxes
            WHERE id = %s
        ''', (box_id,))
        
        box = cur.fetchone()
        cur.close()
        conn.close()
        
        if box:
            return jsonify(box)
        else:
            return jsonify({'error': 'Коробка не найдена'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Создать заказ
@app.route('/api/orders', methods=['POST'])
def create_order():
    """Создать новый заказ"""
    try:
        data = request.get_json()
        
        # Валидация данных
        required_fields = ['box_id', 'customer_name', 'customer_email', 'customer_phone']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Поле {field} обязательно'}), 400
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute('''
            INSERT INTO orders (box_id, customer_name, customer_email, customer_phone)
            VALUES (%s, %s, %s, %s)
            RETURNING id, box_id, customer_name, customer_email, customer_phone, created_at
        ''', (data['box_id'], data['customer_name'], data['customer_email'], data['customer_phone']))
        
        order = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'message': 'Заказ создан успешно',
            'order': order
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Получить все заказы
@app.route('/api/orders', methods=['GET'])
def get_orders():
    """Получить список всех заказов"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute('''
            SELECT 
                o.id,
                o.box_id,
                o.customer_name,
                o.customer_email,
                o.customer_phone,
                o.created_at,
                g.title as box_title,
                g.price as box_price
            FROM orders o
            LEFT JOIN gift_boxes g ON o.box_id = g.id
            ORDER BY o.created_at DESC
        ''')
        
        orders = cur.fetchall()
        cur.close()
        conn.close()
        
        return jsonify(orders)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Для разработки
    app.run(host='0.0.0.0', port=5000, debug=False)
EOFAPP

# 4. Создание requirements.txt
echo -e "${BLUE}📝 Создаю requirements.txt...${NC}"
cat > /var/www/giftbox/requirements.txt << 'EOFREQ'
Flask==3.0.0
Flask-CORS==4.0.0
psycopg2-binary==2.9.9
gunicorn==21.2.0
EOFREQ

# 5. Создание gunicorn.conf.py
echo -e "${BLUE}📝 Создаю gunicorn.conf.py...${NC}"
cat > /var/www/giftbox/gunicorn.conf.py << 'EOFGUN'
"""Конфигурация Gunicorn для production"""

# Адрес и порт
bind = "127.0.0.1:5000"

# Количество worker процессов
workers = 2

# Класс worker
worker_class = "sync"

# Таймауты
timeout = 120
keepalive = 5

# Логирование
accesslog = "/var/log/giftbox/access.log"
errorlog = "/var/log/giftbox/error.log"
loglevel = "info"

# Daemon mode
daemon = False

# PID file
pidfile = "/var/run/giftbox.pid"
EOFGUN

# 6. Настройка Python окружения
echo -e "${BLUE}🐍 Настраиваю Python окружение...${NC}"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 7. Создание папок для логов
echo -e "${BLUE}📋 Создаю папки для логов...${NC}"
mkdir -p /var/log/giftbox
chown www-data:www-data /var/log/giftbox

# 8. Настройка прав доступа
echo -e "${BLUE}🔒 Настраиваю права доступа...${NC}"
chown -R www-data:www-data /var/www/giftbox
chmod -R 755 /var/www/giftbox

# 9. Создание systemd сервиса
echo -e "${BLUE}⚙️  Создаю systemd сервис...${NC}"
cat > /etc/systemd/system/giftbox.service << 'EOFSVC'
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
EOFSVC

# 10. Запуск сервиса
echo -e "${BLUE}🚀 Запускаю сервис...${NC}"
systemctl daemon-reload
systemctl enable giftbox
systemctl start giftbox

# Проверка статуса
sleep 2
if systemctl is-active --quiet giftbox; then
    echo -e "${GREEN}✅ Сервис запущен успешно!${NC}"
else
    echo -e "${RED}❌ Ошибка запуска сервиса!${NC}"
    systemctl status giftbox
    exit 1
fi

# 11. Настройка nginx
echo -e "${BLUE}🌐 Настраиваю nginx...${NC}"
cat > /etc/nginx/sites-available/ab-education.ru << 'EOFNGINX'
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
        
        # Добавляем таймауты
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Frontend (статические файлы)
    location / {
        root /var/www/giftbox/dist;
        try_files $uri $uri/ /index.html;
    }
}
EOFNGINX

# Включение конфига
ln -sf /etc/nginx/sites-available/ab-education.ru /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Проверка конфига nginx
if nginx -t; then
    echo -e "${GREEN}✅ Конфиг nginx валиден${NC}"
    systemctl restart nginx
    echo -e "${GREEN}✅ nginx перезапущен${NC}"
else
    echo -e "${RED}❌ Ошибка в конфиге nginx!${NC}"
    exit 1
fi

# 12. Финальная проверка
echo -e "${BLUE}🧪 Проверяю работу API...${NC}"
sleep 2

# Проверка через localhost
HEALTH_CHECK=$(curl -s http://localhost:5000/api/health)
if echo "$HEALTH_CHECK" | grep -q "ok"; then
    echo -e "${GREEN}✅ API работает через localhost:5000${NC}"
else
    echo -e "${RED}❌ API не отвечает на localhost:5000${NC}"
    echo "$HEALTH_CHECK"
fi

# Проверка через nginx
NGINX_CHECK=$(curl -s http://localhost/api/health)
if echo "$NGINX_CHECK" | grep -q "ok"; then
    echo -e "${GREEN}✅ API работает через nginx${NC}"
else
    echo -e "${RED}⚠️  API не отвечает через nginx${NC}"
    echo "$NGINX_CHECK"
fi

# 13. Вывод итоговой информации
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   🎉 УСТАНОВКА ЗАВЕРШЕНА УСПЕШНО! 🎉     ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}📡 API доступен по адресам:${NC}"
echo "   http://ab-education.ru/api/health"
echo "   http://ab-education.ru/api/boxes"
echo "   http://ab-education.ru/api/orders"
echo ""
echo -e "${BLUE}🔧 Управление сервисом:${NC}"
echo "   systemctl status giftbox    # Статус"
echo "   systemctl restart giftbox   # Перезапуск"
echo "   systemctl stop giftbox      # Остановка"
echo ""
echo -e "${BLUE}📋 Логи:${NC}"
echo "   tail -f /var/log/giftbox/error.log   # Логи ошибок"
echo "   tail -f /var/log/giftbox/access.log  # Логи запросов"
echo "   journalctl -u giftbox -f             # Системные логи"
echo ""
echo -e "${BLUE}🔐 Следующий шаг (опционально):${NC}"
echo "   certbot --nginx -d ab-education.ru -d www.ab-education.ru"
echo "   (для установки SSL сертификата)"
echo ""
