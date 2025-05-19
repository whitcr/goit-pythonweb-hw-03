from http.server import HTTPServer, BaseHTTPRequestHandler
import os
from urllib.parse import parse_qs
import json
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

PORT = 3000
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

env = Environment(loader=FileSystemLoader(os.path.join(BASE_DIR, 'templates')))

def read_data():
    path = os.path.join(BASE_DIR, 'storage', 'data.json')
    if not os.path.exists(path):
        return {}
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_data(username, message):
    path = os.path.join(BASE_DIR, 'storage', 'data.json')
    data = read_data()
    now = str(datetime.now())
    data[now] = {
        "username": username,
        "message": message
    }
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ('/', '/index.html'):
            self.render_template('index.html')
        elif self.path == '/message.html':
            self.render_template('message.html')
        elif self.path == '/read.html':
            data = read_data()
            template = env.get_template('read.html')
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html = template.render(messages=data)
            self.wfile.write(html.encode())
        elif self.path.startswith('/static/'):
            self.handle_static()
        else:
            self.render_template('error.html', code=404)

    def do_POST(self):
        if self.path == '/message.html':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            fields = parse_qs(post_data.decode())
            username = fields.get('username', [''])[0]
            message = fields.get('message', [''])[0]
            save_data(username, message)
            self.send_response(303)
            self.send_header('Location', '/read.html')
            self.end_headers()
        else:
            self.render_template('error.html', code=404)

    def handle_static(self):
        static_path = self.path.lstrip('/')
        full_path = os.path.join(BASE_DIR, static_path)
        if not os.path.isfile(full_path):
            self.render_template('error.html', code=404)
            return
        self.send_response(200)
        if full_path.endswith('.css'):
            self.send_header('Content-Type', 'text/css')
        elif full_path.endswith('.png'):
            self.send_header('Content-Type', 'image/png')
        else:
            self.send_header('Content-Type', 'application/octet-stream')
        self.end_headers()
        with open(full_path, 'rb') as f:
            self.wfile.write(f.read())

    def render_template(self, filename, code=200):
        try:
            template = env.get_template(filename)
            self.send_response(code)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html = template.render()
            self.wfile.write(html.encode())
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b'Internal Server Error')

if __name__ == '__main__':
    os.makedirs(os.path.join(BASE_DIR, 'storage'), exist_ok=True)
    if not os.path.exists(os.path.join(BASE_DIR, 'storage', 'data.json')):
        with open(os.path.join(BASE_DIR, 'storage', 'data.json'), 'w', encoding='utf-8') as f:
            json.dump({}, f)
    httpd = HTTPServer(('localhost', PORT), Handler)
    print(f"Serving on http://localhost:{PORT}")
    httpd.serve_forever()
