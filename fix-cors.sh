#!/bin/bash

# Универсальный скрипт для замены URL в собранном React приложении
# Использование: ./fix-cors.sh /путь/к/dist https://ваш-домен.com

DIST_PATH="${1:-/var/www/giftbox/dist}"
YOUR_DOMAIN="${2:-https://giftbox.ab-education.ru}"

echo "🚀 Начинаю исправление CORS..."
echo "📁 Путь к dist: $DIST_PATH"
echo "🌐 Ваш домен: $YOUR_DOMAIN"

# Создаем бэкап
echo "📦 Создаю бэкап..."
cp -r "$DIST_PATH" "${DIST_PATH}_backup_$(date +%Y%m%d_%H%M%S)"

# Находим все JS файлы и заменяем URL
echo "🔧 Заменяю URL в JS файлах..."
find "$DIST_PATH" -type f -name "*.js" -exec sed -i "s|https://functions\.poehali\.dev|$YOUR_DOMAIN/api|g" {} \;

echo "✅ Готово! URL заменены на $YOUR_DOMAIN/api"
echo ""
echo "📋 Теперь добавь в nginx конфиг:"
echo ""
cat << 'EOF'
    location /api/ {
        proxy_pass https://functions.poehali.dev/;
        proxy_set_header Host functions.poehali.dev;
        proxy_ssl_server_name on;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # CORS headers (на всякий случай)
        add_header Access-Control-Allow-Origin *;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
        add_header Access-Control-Allow-Headers "Content-Type, Authorization";
    }
EOF
echo ""
echo "Затем: nginx -t && systemctl restart nginx"
