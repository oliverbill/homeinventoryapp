import os
import environ

if os.getenv("RUNNING_MIGRATIONS"):
    DATABASE_URL = 'postgres://djuser:Baleia302@//cloudsql/homeinventory-405011:europe-west1:dbsvc/db-dev'
    env = environ.Env()
    env.ENVIRON.setdefault(key='DATABASE_URL',value=DATABASE_URL)
    DATABASES = {'default': env.db()}

    if os.getenv("USE_CLOUD_SQL_AUTH_PROXY", None):
        DATABASES["default"]["HOST"] = "127.0.0.1"
        DATABASES["default"]["PORT"] = 5432
else:
    from config.base import *