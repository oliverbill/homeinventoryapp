from config.base import *

import os
from urllib.parse import urlparse

import environ

from utils import str_to_dict

APP_SETTINGS_PROD_FILENAME = 'APPLICATION_SETTINGS'
APP_SETTINGS_DEV_FILENAME = 'APPLICATION_SETTINGS_DEV'

app_settings_from_secrets = os.getenv(APP_SETTINGS_PROD_FILENAME) or os.getenv(APP_SETTINGS_DEV_FILENAME)

CLOUDRUN_SERVICE_URL = os.getenv("CLOUDRUN_SERVICE_URL", default=None)
if CLOUDRUN_SERVICE_URL:
    ALLOWED_HOSTS = [urlparse(CLOUDRUN_SERVICE_URL).netloc]
    CSRF_TRUSTED_ORIGINS = [CLOUDRUN_SERVICE_URL]
else:
    ALLOWED_HOSTS = ["*"]

if app_settings_from_secrets:
    app_settings_secret_value = str_to_dict(app_settings_from_secrets)
    # print(f'APPLICATION_SETTINGS: {app_settings_secret_value}')
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

    if os.getenv("USE_CLOUD_SQL_AUTH_PROXY", None):
        DATABASES["default"]["HOST"] = "127.0.0.1"
        DATABASES["default"]["PORT"] = 5432
else:
    from config.local import *


