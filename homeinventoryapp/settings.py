import os
from pathlib import Path
from urllib.parse import urlparse

import dj_database_url
import environ

from utils import str_to_dict

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

APP_SETTINGS_DEV_FILENAME = 'APPLICATION_SETTINGS_DEV'
APP_SETTINGS_PROD_FILENAME = 'APPLICATION_SETTINGS'
app_settings_secret_value = None

IS_PROD_ENV = os.getenv(APP_SETTINGS_PROD_FILENAME)
IS_DEV_ENV = os.getenv(APP_SETTINGS_DEV_FILENAME)
IS_LOCAL_ENV = os.getenv(APP_SETTINGS_PROD_FILENAME) is None and os.getenv(APP_SETTINGS_DEV_FILENAME) is None

APPLICATION_SETTINGS_CONTENT = None
DATABASES = {}

if IS_DEV_ENV:
    APPLICATION_SETTINGS_CONTENT = os.getenv(APP_SETTINGS_DEV_FILENAME)
elif IS_PROD_ENV:
    APPLICATION_SETTINGS_CONTENT = os.getenv(APP_SETTINGS_PROD_FILENAME)
elif IS_LOCAL_ENV:
    env = environ.Env()
    environ.Env.read_env(os.path.join(BASE_DIR, '.env'))
    DEBUG = env.get_value('DEBUG',default=None)
    STATIC_ROOT = "./static-djangoadmin"
    if DEBUG is None:
        SECRET_KEY = 'django-insecure-g%307@2mqxm41xo1utug+q5-pmo*-hez6d-t7k76xhg$upm-4f'
        DEBUG = True
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': BASE_DIR / 'db.sqlite3',
            }
        }
    else:
        DEBUG = env('DEBUG')
        SECRET_KEY = env('SECRET_KEY')
        DATABASES = {'default': env.db()}
        # print(DATABASES['default'])

if not IS_LOCAL_ENV:
    app_settings_secret_value = str_to_dict(APPLICATION_SETTINGS_CONTENT)
    checking = app_settings_secret_value is not None and len(app_settings_secret_value) > 0
    print(f'APPLICATION_SETTINGS is loaded: {checking}')
    SECRET_KEY = app_settings_secret_value['SECRET_KEY']
    DEBUG = app_settings_secret_value['DEBUG']
    DATABASE_URL = app_settings_secret_value['DATABASE_URL']
    DATABASES['default'] = dj_database_url.config(default=DATABASE_URL)
    GS_BUCKET_NAME = app_settings_secret_value['GS_BUCKET_NAME']
    STATICFILES_DIRS = ["static-djangoadmin/"]
    DEFAULT_FILE_STORAGE = "storages.backends.gcloud.GoogleCloudStorage"
    STATICFILES_STORAGE = "storages.backends.gcloud.GoogleCloudStorage"
    GS_DEFAULT_ACL = "publicRead"
    STATIC_ROOT = "static-djangoadmin/"
    print(DATABASES['default'])

if os.getenv("USE_CLOUD_SQL_AUTH_PROXY", None):
    DATABASES["default"]["HOST"] = "127.0.0.1"
    DATABASES["default"]["PORT"] = 5432

# If defined, add service URL to Django security settings
CLOUDRUN_SERVICE_URL = os.getenv("CLOUDRUN_SERVICE_URL", default=None)
if CLOUDRUN_SERVICE_URL:
    ALLOWED_HOSTS = [urlparse(CLOUDRUN_SERVICE_URL).netloc]
    CSRF_TRUSTED_ORIGINS = [CLOUDRUN_SERVICE_URL]
else:
    ALLOWED_HOSTS = ["*"]

REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,
}

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'homeinventoryapi',
    'rest_framework.authtoken',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'homeinventoryapp.urls'

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

WSGI_APPLICATION = 'homeinventoryapp.wsgi.application'

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

STATIC_URL = 'static/'


# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
