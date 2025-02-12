import os
from pathlib import Path
import dj_database_url
from dotenv import load_dotenv
from decouple import config

# Load environment variables
load_dotenv()

# Import the new config
from config import config as app_config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = app_config['SECRET_KEY']

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = app_config['DEBUG']

ALLOWED_HOSTS = app_config['ALLOWED_HOSTS']

# Make sure OpenAI API key is set
OPENAI_API_KEY = config('OPENAI_API_KEY', default='')

LLAMA_PARSE_KEY = config('LLAMA_PARSE_KEY', default='')



CSRF_TRUSTED_ORIGINS = [
    "http://*.railway.app",
    "https://*.railway.app",
]

CORS_ALLOWED_ORIGINS = app_config['CORS_ALLOWED_ORIGINS']

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'api',
    # 'document_analysis',
    # 'vector_store',
    # 'pgvector',
     'research_assistant',
]



MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]



WSGI_APPLICATION = 'core.wsgi.application'

CORS_ALLOW_ALL_ORIGINS = False


# Governance-specific settings
GOVERNANCE_SETTINGS = {
    'MAX_DOCUMENTS': 3,
    'CHUNK_SIZE': 1000,
    'OVERLAP_SIZE': 200,
    'SUPPORTED_FORMATS': ['pdf', 'docx', 'txt']
}

# Monitoring settings
MONITORING_SETTINGS = {
    'LOG_LEVEL': 'INFO',
    'ENABLE_PERFORMANCE_TRACKING': True,
    'ENABLE_RICH_LOGGING': True,
    'TRACK_DOCUMENT_METRICS': True
}


# Research Assistant settings
RESEARCH_SETTINGS = {
    'MAX_DOCUMENTS': 5,
    'SUPPORTED_FORMATS': ['pdf', 'docx', 'txt'],
    'MIN_CONFIDENCE_SCORE': 0.2,
    'ENABLE_OCR': True,
    'OCR_LANGUAGE': 'eng'
}

# Document processing settings
PROCESSING_SETTINGS = {
    'CHUNK_SIZE': 1000,
    'MAX_TOKENS': 8000,
    'ENABLE_TABLE_EXTRACTION': True,
    'ENABLE_IMAGE_ANALYSIS': True
}

DATABASES = {
    'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
}

# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

# print("--------- DATABASE URL  ",app_config['DATABASE_URL'])

# DATABASES = {
#     'default': dj_database_url.config(default=app_config['DATABASE_URL'])
# }

# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = 'static/'

if app_config['STATIC_ROOT']:
    STATIC_ROOT = app_config['STATIC_ROOT']

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# If you need to allow specific HTTP methods
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

# If you need to allow specific headers
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# If you need to allow credentials (cookies, authorization headers)
CORS_ALLOW_CREDENTIALS = True

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ]
}










# try:
#             # First clear all previous_section references in document_sections
#             await sync_to_async(DocumentSection.objects.all().update)(previous_section=None)
#             print("[Database Cleanup] Cleared all previous section references")
            
#             # Then delete all sections
#             sections_count = await sync_to_async(DocumentSection.objects.all().delete)()
#             print(f"[Database Cleanup] Deleted {sections_count[0]} sections")
            
#             # Finally delete all documents
#             docs_count = await sync_to_async(DocumentMetadata.objects.all().delete)()
#             print(f"[Database Cleanup] Deleted {docs_count[0]} documents")
            
#             print("[Database Cleanup] Successfully cleared all database records")

#         except Exception as e:
#             print(f"[Database Cleanup] Error cleaning database: {str(e)}")
#             raise