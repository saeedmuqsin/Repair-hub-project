from datetime import timedelta
import uuid
import psycopg2

class Config:
    SECRET_KEY = str(uuid.uuid4())
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    REMEMBER_COOKIE_DURATION = timedelta(days=7)
    PERMANENT_SESSION_LIFETIME= timedelta(minutes=120)
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'saeedmuhsin200@gmail.com'   # Replace with your email
    MAIL_PASSWORD = 'your_app_password_here' # Use App Password (not Gmail password) - Set as environment variable in production
    MAIL_DEFAULT_SENDER = ('RepairHub', 'saeedmuhsin200@gmail.com')
    

class DevelopmentConfig(Config):
    DEBUG = True
    environment = 'development'
    SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2://postgres:hellosaeed123.@localhost:5432/repair_hub'

class ProductionConfig(Config):
    environment = 'production'
    SQLALCHEMY_DATABASE_URI = "sqlite:///repair_hub.db"
      # Replace 'correct-hostname' with the actual hostname

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    environment = 'testing'