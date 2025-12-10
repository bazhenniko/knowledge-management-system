'''
Business: Direct PostgreSQL connection to TimeWeb Cloud database for knowledge management
Args: event with httpMethod, queryStringParameters or body containing action (query/list/stats)
Returns: HTTP response with database results in JSON format
'''

import json
import os
import ssl
import tempfile
import urllib.request
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, Any
from dotenv import load_dotenv

# Загружаем .env файл из родительской директории
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    method: str = event.get('httpMethod', 'GET')
    
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Accept, X-Auth-Token, X-User-Id, X-Session-Id',
                'Access-Control-Max-Age': '86400'
            },
            'isBase64Encoded': False,
            'body': ''
        }
    
    try:
        if method == 'GET':
            query_params = event.get('queryStringParameters', {})
            action = query_params.get('action')
            body_data = query_params
        elif method in ['POST', 'PUT', 'DELETE']:
            body_data = json.loads(event.get('body', '{}'))
            action = body_data.get('action')
            if method == 'PUT' and not action:
                action = 'update'
            elif method == 'DELETE' and not action:
                action = 'delete'
        else:
            return error_response(405, 'Method not allowed')
        
        # Получаем DATABASE_URL из окружения
        database_url = os.environ.get('DATABASE_URL')
        
        if not database_url:
            return error_response(500, 'Database connection not configured')
        
        # Скачиваем SSL сертификат
        cert_file = tempfile.NamedTemporaryFile(mode='w', suffix='.crt', delete=False)
        cert_content = urllib.request.urlopen('https://st.timeweb.com/cloud-static/ca.crt').read().decode('utf-8')
        cert_file.write(cert_content)
        cert_file.close()
        
        # Парсим DATABASE_URL и подключаемся
        conn = psycopg2.connect(database_url, sslrootcert=cert_file.name)
        conn.autocommit = True
        
        if action == 'query':
            result = handle_query(conn, body_data)
        elif action == 'list':
            result = handle_list(conn, body_data)
        elif action == 'stats':
            result = handle_stats(conn, body_data)
        elif action == 'create':
            result = handle_create(conn, body_data)
        elif action == 'update':
            result = handle_update(conn, body_data)
        elif action == 'delete':
            result = handle_delete(conn, body_data)
        else:
            result = error_response(400, f'Unknown action: {action}')
        
        conn.close()
        os.unlink(cert_file.name)
        
        return result
    
    except psycopg2.Error as e:
        return error_response(500, f'Database error: {str(e)}')
    except Exception as e:
        return error_response(500, f'Error: {str(e)}')

def handle_query(conn, params):
    query = params.get('query')
    if not query:
        return error_response(400, 'Query is required')
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            if query.strip().upper().startswith('SELECT'):
                rows = cur.fetchall()
                return success_response({'rows': rows, 'count': len(rows)})
            else:
                return success_response({'message': 'Query executed successfully', 'rowcount': cur.rowcount})
    except psycopg2.Error as e:
        return error_response(400, f'Query error: {str(e)}')

def handle_list(conn, params):
    table = params.get('table')
    if not table:
        return error_response(400, 'Table name is required')
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(f'SELECT * FROM {table} LIMIT 100')
            rows = cur.fetchall()
            return success_response({'rows': rows, 'count': len(rows)})
    except psycopg2.Error as e:
        return error_response(400, f'List error: {str(e)}')

def handle_stats(conn, params):
    # Получаем схему из параметров или используем схему с префиксом t_p
    schema = params.get('schema')
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Если схема не указана, найдём все схемы с t_p
            if not schema:
                cur.execute("""
                    SELECT schema_name 
                    FROM information_schema.schemata 
                    WHERE schema_name LIKE 't_p%'
                    LIMIT 1
                """)
                result = cur.fetchone()
                schema = result['schema_name'] if result else 'public'
            
            # Получаем таблицы из схемы
            cur.execute(f"""
                SELECT table_name, 
                       (SELECT COUNT(*) FROM information_schema.columns 
                        WHERE table_schema = '{schema}' AND table_name = t.table_name) as column_count
                FROM information_schema.tables t
                WHERE table_schema = '{schema}'
                ORDER BY table_name
            """)
            tables = cur.fetchall()
            
            # Подсчитываем записи в каждой таблице
            total_records = 0
            table_list = []
            for table in tables:
                table_name = table['table_name']
                cur.execute(f'SELECT COUNT(*) as count FROM "{schema}"."{table_name}"')
                count_row = cur.fetchone()
                record_count = count_row['count'] if count_row else 0
                total_records += record_count
                
                table_list.append({
                    'table_name': table_name,
                    'column_count': table['column_count'],
                    'record_count': record_count
                })
            
            return success_response({
                'tables': table_list,
                'totalTables': len(table_list),
                'totalRecords': total_records,
                'schema': schema
            })
    except psycopg2.Error as e:
        return error_response(400, f'Stats error: {str(e)}')

def handle_create(conn, params):
    table = params.get('table')
    data = params.get('data')
    
    if not table or not data:
        return error_response(400, 'Table and data are required')
    
    try:
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['%s'] * len(data))
        query = f'INSERT INTO {table} ({columns}) VALUES ({placeholders}) RETURNING *'
        
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, list(data.values()))
            row = cur.fetchone()
            return success_response({'row': row})
    except psycopg2.Error as e:
        return error_response(400, f'Create error: {str(e)}')

def handle_update(conn, params):
    table = params.get('table')
    data = params.get('data')
    where = params.get('where')
    
    if not table or not data or not where:
        return error_response(400, 'Table, data, and where are required')
    
    try:
        set_clause = ', '.join([f'{k} = %s' for k in data.keys()])
        query = f'UPDATE {table} SET {set_clause} WHERE {where} RETURNING *'
        
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, list(data.values()))
            rows = cur.fetchall()
            return success_response({'rows': rows, 'count': len(rows)})
    except psycopg2.Error as e:
        return error_response(400, f'Update error: {str(e)}')

def handle_delete(conn, params):
    table = params.get('table')
    where = params.get('where')
    
    if not table or not where:
        return error_response(400, 'Table and where are required')
    
    try:
        query = f'DELETE FROM {table} WHERE {where} RETURNING *'
        
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            rows = cur.fetchall()
            return success_response({'deleted': rows, 'count': len(rows)})
    except psycopg2.Error as e:
        return error_response(400, f'Delete error: {str(e)}')

def success_response(data):
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'isBase64Encoded': False,
        'body': json.dumps(data)
    }

def error_response(status_code, message):
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'isBase64Encoded': False,
        'body': json.dumps({'error': message})
    }