"""
Vercel Serverless Entry Point - WSGI Handler
"""
import sys
import os
import tempfile

# Add parent directory to path
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

# Initialize Flask app
app = Flask(__name__, 
            template_folder=os.path.join(parent_dir, 'templates'),
            static_folder=os.path.join(parent_dir, 'static'),
            instance_path=tempfile.gettempdir())

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

# Vercel expects 'app' to be the WSGI application
# This is the simplest and most compatible approach
