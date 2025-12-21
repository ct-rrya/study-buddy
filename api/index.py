"""
Vercel Serverless Entry Point
"""
from http.server import BaseHTTPRequestHandler
import sys
import os

# Add parent directory to path so imports work
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from flask import Flask
from flask_login import LoginManager

# Initialize Flask app with correct paths for Vercel
app = Flask(__name__, 
            template_folder=os.path.join(parent_dir, 'templates'),
            static_folder=os.path.join(parent_dir, 'static'))

# Load config
from config import Config
app.config.from_object(Config)

# Initialize database
from models import db, User
db.init_app(app)

# Initialize Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Initialize Flask-Mail
try:
    from flask_mail import Mail
    mail = Mail(app)
except Exception:
    mail = None

# Register blueprints
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.study import study_bp
from routes.social import social_bp

try:
    from routes.auth import mail as auth_mail
    auth_mail.init_app(app)
except Exception:
    pass

app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(study_bp)
app.register_blueprint(social_bp)

# Create database tables
with app.app_context():
    try:
        db.create_all()
    except Exception as e:
        print(f"Database init error: {e}")

# Vercel handler class
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        from io import BytesIO
        
        # Create WSGI environ
        environ = {
            'REQUEST_METHOD': 'GET',
            'SCRIPT_NAME': '',
            'PATH_INFO': self.path.split('?')[0],
            'QUERY_STRING': self.path.split('?')[1] if '?' in self.path else '',
            'SERVER_NAME': 'vercel',
            'SERVER_PORT': '443',
            'SERVER_PROTOCOL': 'HTTP/1.1',
            'wsgi.version': (1, 0),
            'wsgi.url_scheme': 'https',
            'wsgi.input': BytesIO(b''),
            'wsgi.errors': sys.stderr,
            'wsgi.multithread': False,
            'wsgi.multiprocess': False,
            'wsgi.run_once': True,
            'HTTP_HOST': self.headers.get('Host', ''),
            'HTTP_COOKIE': self.headers.get('Cookie', ''),
        }
        
        # Add all headers
        for key, value in self.headers.items():
            key = 'HTTP_' + key.upper().replace('-', '_')
            environ[key] = value
        
        # Response storage
        response_started = []
        response_headers = []
        
        def start_response(status, headers):
            response_started.append(status)
            response_headers.extend(headers)
        
        # Call Flask app
        response = app(environ, start_response)
        
        # Send response
        status_code = int(response_started[0].split(' ')[0])
        self.send_response(status_code)
        for header, value in response_headers:
            self.send_header(header, value)
        self.end_headers()
        
        for chunk in response:
            self.wfile.write(chunk)
    
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        
        from io import BytesIO
        
        environ = {
            'REQUEST_METHOD': 'POST',
            'SCRIPT_NAME': '',
            'PATH_INFO': self.path.split('?')[0],
            'QUERY_STRING': self.path.split('?')[1] if '?' in self.path else '',
            'CONTENT_TYPE': self.headers.get('Content-Type', ''),
            'CONTENT_LENGTH': content_length,
            'SERVER_NAME': 'vercel',
            'SERVER_PORT': '443',
            'SERVER_PROTOCOL': 'HTTP/1.1',
            'wsgi.version': (1, 0),
            'wsgi.url_scheme': 'https',
            'wsgi.input': BytesIO(body),
            'wsgi.errors': sys.stderr,
            'wsgi.multithread': False,
            'wsgi.multiprocess': False,
            'wsgi.run_once': True,
            'HTTP_HOST': self.headers.get('Host', ''),
            'HTTP_COOKIE': self.headers.get('Cookie', ''),
        }
        
        for key, value in self.headers.items():
            key = 'HTTP_' + key.upper().replace('-', '_')
            environ[key] = value
        
        response_started = []
        response_headers = []
        
        def start_response(status, headers):
            response_started.append(status)
            response_headers.extend(headers)
        
        response = app(environ, start_response)
        
        status_code = int(response_started[0].split(' ')[0])
        self.send_response(status_code)
        for header, value in response_headers:
            self.send_header(header, value)
        self.end_headers()
        
        for chunk in response:
            self.wfile.write(chunk)
