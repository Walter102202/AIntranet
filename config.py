import os
import secrets
from datetime import timedelta

class Config:
    # Modo de ejecución
    FLASK_ENV = os.environ.get('FLASK_ENV', 'production')
    DEBUG = FLASK_ENV == 'development'

    # Configuración general - SECRET_KEY requerida en producción
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        if FLASK_ENV == 'development':
            SECRET_KEY = 'dev-secret-key-insecure-local-only'
        else:
            raise RuntimeError(
                'SECRET_KEY no está configurada. '
                'Establece la variable de entorno SECRET_KEY para producción.'
            )

    # Configuración de base de datos MySQL
    DB_CONFIG = {
        'host': os.environ.get('DB_HOST', 'localhost'),
        'user': os.environ.get('DB_USER', 'root'),
        'password': os.environ.get('DB_PASSWORD', ''),
        'database': os.environ.get('DB_NAME', 'intranet_db')
    }

    # Configuración de sesión
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)  # 8 horas por defecto
    SESSION_COOKIE_SECURE = FLASK_ENV != 'development'  # True en producción (HTTPS)
    SESSION_COOKIE_HTTPONLY = True  # Protección contra XSS
    SESSION_COOKIE_SAMESITE = 'Lax'  # Protección contra CSRF

    # Configuración de uploads
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB máximo
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt', 'png', 'jpg', 'jpeg'}

    # Configuración OAuth - Microsoft
    MICROSOFT_CLIENT_ID = os.environ.get('MICROSOFT_CLIENT_ID', '')
    MICROSOFT_CLIENT_SECRET = os.environ.get('MICROSOFT_CLIENT_SECRET', '')
    MICROSOFT_TENANT_ID = os.environ.get('MICROSOFT_TENANT_ID', 'common')  # 'common' para multi-tenant
    MICROSOFT_AUTHORITY = f"https://login.microsoftonline.com/{MICROSOFT_TENANT_ID}"
    MICROSOFT_REDIRECT_URI = os.environ.get('MICROSOFT_REDIRECT_URI', 'http://localhost:5000/auth/microsoft/callback')
    MICROSOFT_SCOPE = ['User.Read', 'email', 'profile', 'openid']

    # Configuración OAuth - Google
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
    GOOGLE_REDIRECT_URI = os.environ.get('GOOGLE_REDIRECT_URI', 'http://localhost:5000/auth/google/callback')
    GOOGLE_SCOPE = [
        'https://www.googleapis.com/auth/userinfo.email',
        'https://www.googleapis.com/auth/userinfo.profile',
        'openid'
    ]
    GOOGLE_DISCOVERY_URL = 'https://accounts.google.com/.well-known/openid-configuration'
