from datetime import timedelta
import os
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

    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = 465
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    MAIL_TIMEOUT = int(os.getenv('MAIL_TIMEOUT', '20'))
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', 'saeedmuqsin2@gmail.com')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', 'rcfzaihcwuqinduz')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', MAIL_USERNAME)

class DevelopmentConfig(Config):
    DEBUG = True
    environment = 'development'
    SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2://postgres:hellosaeed@localhost:5432/repair_hub_db'

class ProductionConfig(Config):
    environment = 'production'
    SQLALCHEMY_DATABASE_URI = "sqlite:///repair_hub.db"
      # Replace 'correct-hostname' with the actual hostname

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    environment = 'testing'