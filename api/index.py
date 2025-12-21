"""
Vercel Serverless Entry Point
"""
import sys
import os

# Add parent directory to path so imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from flask import Flask
from flask_login import LoginManager
from flask_mail import Mail
from config import Config
from models import db, User

# Initialize Flask app
app = Flask(__name__, 
            template_folder='../templates',
            static_folder='../static')
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
mail = Mail(app)
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Register blueprints
from routes.auth import auth_bp, mail as auth_mail
auth_mail.init_app(app)
from routes.dashboard import dashboard_bp
from routes.study import study_bp
from routes.social import social_bp

app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(study_bp)
app.register_blueprint(social_bp)

# Create database tables on first request
@app.before_request
def create_tables():
    # Only run once
    if not hasattr(app, '_tables_created'):
        db.create_all()
        app._tables_created = True

# Vercel handler
def handler(request):
    return app(request.environ, request.start_response)

# For local testing
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
