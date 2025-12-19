"""
Application Configuration
"""
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///studybot.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file upload
    
    # Groq API Key (Free!) - Get yours at https://console.groq.com/keys
    GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
    
    # Email Configuration (Gmail example)
    # To use Gmail: Enable 2FA, then create an App Password at https://myaccount.google.com/apppasswords
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = ('Study Buddy', os.environ.get('MAIL_USERNAME'))
