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
