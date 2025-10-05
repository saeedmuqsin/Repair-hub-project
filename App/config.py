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
    MAIL_USERNAME = 'saeedmuhsin200@gmail.com'   # Replace
    MAIL_PASSWORD = str(uuid.uuid4()) # Use App Password (not Gmail password)
    MAIL_DEFAULT_SENDER = ('RepairHub', 'saeedmuhsin200@gmail.com')


class DevelopmentConfig(Config):
    DEBUG = True
    environment = 'development'
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:0557468637saeed.@localhost:3306/repair_hub'

class ProductionConfig(Config):
    DEBUG = True
    environment = 'production'
    SQLALCHEMY_DATABASE_URI = "postgresql+psycopg2://postgres:hellosaeed123.@db.xvpjjdqdvrbiaicexhpj.supabase.co:5432/repair_hub"

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    environment = 'testing'