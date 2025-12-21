"""
Study Motivation Bot - Main Application
"""
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file

from flask import Flask
from flask_login import LoginManager
from flask_mail import Mail
from flask_socketio import SocketIO
from config import Config
from models import db, User

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
mail = Mail(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Register blueprints
from routes.auth import auth_bp, mail as auth_mail
auth_mail.init_app(app)  # Initialize mail in auth blueprint
from routes.dashboard import dashboard_bp
from routes.study import study_bp
from routes.social import social_bp

app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(study_bp)
app.register_blueprint(social_bp)

# Import and register socket events
from routes.sockets import register_socket_events
register_socket_events(socketio)

# Create database tables
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    socketio.run(app, debug=True)
