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
