from config.base import *

import os
from pathlib import Path
from urllib.parse import urlparse

import environ

from utils import str_to_dict

BASE_DIR = Path(__file__).resolve().parent.parent

APP_SETTINGS_PROD_FILENAME = 'APPLICATION_SETTINGS'
APP_SETTINGS_DEV_FILENAME = 'APPLICATION_SETTINGS_DEV'

APPLICATION_SETTINGS_CONTENT = os.getenv(APP_SETTINGS_PROD_FILENAME) or os.getenv(APP_SETTINGS_DEV_FILENAME)
app_settings_secret_value = None

if APPLICATION_SETTINGS_CONTENT:
    app_settings_secret_value = str_to_dict(APPLICATION_SETTINGS_CONTENT)
    print(f'APPLICATION_SETTINGS: {app_settings_secret_value}')
    SECRET_KEY = app_settings_secret_value['SECRET_KEY']
    DEBUG = app_settings_secret_value['DEBUG']
    DATABASE_URL = app_settings_secret_value['DATABASE_URL']
    env = environ.Env()
    env.ENVIRON.setdefault(key='DATABASE_URL',value=DATABASE_URL)
    DATABASES = {'default': env.db()}
    GS_BUCKET_NAME = app_settings_secret_value['GS_BUCKET_NAME']
    STATICFILES_DIRS = []
    DEFAULT_FILE_STORAGE = "storages.backends.gcloud.GoogleCloudStorage"
    STATICFILES_STORAGE = "storages.backends.gcloud.GoogleCloudStorage"
    GS_DEFAULT_ACL = "publicRead"
    STATIC_ROOT = "static-djangoadmin/"

CLOUDRUN_SERVICE_URL = os.getenv("CLOUDRUN_SERVICE_URL", default=None)
if CLOUDRUN_SERVICE_URL:
    ALLOWED_HOSTS = [urlparse(CLOUDRUN_SERVICE_URL).netloc]
    CSRF_TRUSTED_ORIGINS = [CLOUDRUN_SERVICE_URL]
else:
    ALLOWED_HOSTS = ["*"]

if os.getenv("USE_CLOUD_SQL_AUTH_PROXY", None):
    DATABASES["default"]["HOST"] = "127.0.0.1"
    DATABASES["default"]["PORT"] = 5432

from config.local import *