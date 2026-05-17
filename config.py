# ============================================================
# config.py — MediScan Pro Configuration Management
# ============================================================

import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class BaseConfig:
    # ── Core ─────────────────────────────────────────────────
    BASE_DIR   = os.path.abspath(os.path.dirname(__file__))
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    APP_NAME   = 'MediScan Pro'

    # ── Database ──────────────────────────────────────────────
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(BASE_DIR, 'instance', 'mediscan.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO                = False

    # ── Session ───────────────────────────────────────────────
    SESSION_TYPE              = 'filesystem'
    SESSION_FILE_DIR          = os.path.join(BASE_DIR, 'instance', 'sessions')
    SESSION_PERMANENT         = True
    SESSION_USE_SIGNER        = True
    SESSION_COOKIE_HTTPONLY   = True
    SESSION_COOKIE_SAMESITE   = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    # ── Flask-Login ───────────────────────────────────────────
    LOGIN_VIEW             = 'auth.login'
    LOGIN_MESSAGE          = 'Please log in to access this page.'
    LOGIN_MESSAGE_CATEGORY = 'warning'

    # ── CSRF ──────────────────────────────────────────────────
    WTF_CSRF_ENABLED    = True
    WTF_CSRF_TIME_LIMIT = 3600

    # ── File Uploads ──────────────────────────────────────────
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    UPLOAD_FOLDER      = os.path.join(BASE_DIR, 'instance', 'uploads')
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

    # ── ML Models ─────────────────────────────────────────────
    MODELS_FOLDER = os.path.join(BASE_DIR, 'ml_models', 'saved_models')

    # ── Bcrypt ────────────────────────────────────────────────
    BCRYPT_LOG_ROUNDS = 12

    # ── Pagination ────────────────────────────────────────────
    RECORDS_PER_PAGE = 10


class DevelopmentConfig(BaseConfig):
    DEBUG    = True
    TESTING  = False

    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(BaseConfig.BASE_DIR, 'instance', 'mediscan_dev.db')
    SQLALCHEMY_ECHO = True


class TestingConfig(BaseConfig):
    DEBUG    = True
    TESTING  = True

    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED        = False
    BCRYPT_LOG_ROUNDS       = 4
    SESSION_TYPE            = 'null'


class ProductionConfig(BaseConfig):
    DEBUG   = False
    TESTING = False

    SECRET_KEY = os.environ.get('SECRET_KEY')

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_ECHO         = False

    SESSION_COOKIE_SECURE   = True
    SESSION_COOKIE_SAMESITE = 'Strict'

    WTF_CSRF_TIME_LIMIT = 1800
    BCRYPT_LOG_ROUNDS   = 14


# ── Registry ──────────────────────────────────────────────────
config_by_name = {
    'development' : DevelopmentConfig,
    'testing'     : TestingConfig,
    'production'  : ProductionConfig,
    'default'     : DevelopmentConfig,
}


# ── Helpers ───────────────────────────────────────────────────
def allowed_file(filename: str) -> bool:
    return (
        '.' in filename and
        filename.rsplit('.', 1)[1].lower() in BaseConfig.ALLOWED_EXTENSIONS
    )


def get_config(env: str = None):
    env = env or os.environ.get('FLASK_ENV', 'development')
    return config_by_name.get(env, DevelopmentConfig)