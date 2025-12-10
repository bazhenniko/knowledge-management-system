#!/usr/bin/env python3
"""
Local backend server for running Python Cloud Functions locally
Runs on port 8000 by default
"""
import os
import sys
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import importlib.util

PORT = int(os.environ.get('BACKEND_PORT', 8000))
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))

class MockContext:
    """Mock context object for local testing"""
    def __init__(self, request_id='local-request'):
        self.request_id = request_id
        self.function_name = 'local-function'
        self.function_version = 'local'
        self.memory_limit_in_mb = 256
        self.function_folder_id = 'local'
        self.deadline_ms = 0
        self.token = None
    
    def get_remaining_time_in_millis(self):
        return 30000

class BackendHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        """Override to add timestamps"""
        sys.stderr.write(f"[{self.log_date_time_string()}] {format % args}\n")
    
    def do_OPTIONS(self):
        """Handle CORS preflight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-User-Id, X-Auth-Token, X-Session-Id')
        self.send_header('Access-Control-Max-Age', '86400')
        self.end_headers()
    
    def do_GET(self):
        self.handle_request('GET')
    
    def do_POST(self):
        self.handle_request('POST')
    
    def do_PUT(self):
        self.handle_request('PUT')
    
    def do_DELETE(self):
        self.handle_request('DELETE')
    
    def handle_request(self, method):
        """Handle incoming request and route to appropriate function"""
        try:
            parsed_url = urlparse(self.path)
            path = parsed_url.path
            query_params = parse_qs(parsed_url.query)
            
            # Convert query params from lists to single values
            query_params = {k: v[0] if len(v) == 1 else v for k, v in query_params.items()}
            
            # Parse function name from path
            # /api/auth -> auth, /api/db -> external-db
            function_name = None
            if path.startswith('/api/'):
                endpoint = path[5:]  # Remove '/api/'
                if endpoint == 'auth':
                    function_name = 'auth'
                elif endpoint == 'db':
                    function_name = 'external-db'
                elif endpoint == 'email':
                    function_name = 'email-notifications'
                elif endpoint == 'password-reset':
                    function_name = 'password-reset'
            
            if not function_name:
                self.send_error(404, f"Function not found for path: {path}")
                return
            
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else ''
            
            # Build event object
            event = {
                'httpMethod': method,
                'path': path,
                'queryStringParameters': query_params,
                'headers': dict(self.headers),
                'body': body,
                'isBase64Encoded': False,
                'requestContext': {
                    'requestId': 'local-' + str(id(self)),
                    'identity': {
                        'sourceIp': self.client_address[0],
                        'userAgent': self.headers.get('User-Agent', '')
                    },
                    'httpMethod': method,
                    'requestTime': '',
                    'requestTimeEpoch': 0
                }
            }
            
            # Load and execute function
            function_path = os.path.join(BACKEND_DIR, function_name, 'index.py')
            if not os.path.exists(function_path):
                self.send_error(404, f"Function not found: {function_name}")
                return
            
            # Import module
            spec = importlib.util.spec_from_file_location("handler_module", function_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Execute handler
            context = MockContext()
            result = module.handler(event, context)
            
            # Send response
            status_code = result.get('statusCode', 200)
            headers = result.get('headers', {})
            response_body = result.get('body', '')
            
            self.send_response(status_code)
            for key, value in headers.items():
                self.send_header(key, value)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            if isinstance(response_body, str):
                self.wfile.write(response_body.encode('utf-8'))
            else:
                self.wfile.write(json.dumps(response_body).encode('utf-8'))
                
        except Exception as e:
            print(f"Error handling request: {e}")
            import traceback
            traceback.print_exc()
            self.send_error(500, str(e))

def run_server():
    """Start the local backend server"""
    server_address = ('', PORT)
    httpd = HTTPServer(server_address, BackendHandler)
    print(f"🚀 Local backend server running on http://localhost:{PORT}")
    print(f"Backend directory: {BACKEND_DIR}")
    print(f"Available endpoints:")
    print(f"  - /api/auth          -> backend/auth/")
    print(f"  - /api/db            -> backend/external-db/")
    print(f"  - /api/email         -> backend/email-notifications/")
    print(f"  - /api/password-reset -> backend/password-reset/")
    print()
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n⛔ Server stopped")
        httpd.server_close()

if __name__ == '__main__':
    run_server()
