import os
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent

IS_PRODUCTION_FRONTEND = os.environ.get('IS_PRODUCTION_FRONTEND', 'false').lower() == 'true'
IS_PRODUCTION_BACKEND = os.environ.get('IS_PRODUCTION_BACKEND', 'false').lower() == 'true'

config = {
    'DEBUG': not IS_PRODUCTION_BACKEND,
    'SECRET_KEY': os.environ.get('DJANGO_SECRET_KEY', 'dev-secret-key'),
    'ALLOWED_HOSTS': ['docgraphapi.up.railway.app', 'localhost', '127.0.0.1', '*'],
    'CORS_ALLOWED_ORIGINS': [
        'https://docgraph.up.railway.app',
        'http://localhost:3000',
    ],
    'DATABASE_URL': os.environ.get('POSTGRES_URL') if IS_PRODUCTION_BACKEND else os.environ.get('POSTGRES_URL_DEV'),
    # 'STATIC_ROOT': BASE_DIR / 'staticfiles',
    'STATIC_ROOT': os.path.join(BASE_DIR, 'staticfiles'),
}


