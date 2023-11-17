STATICFILES_DIRS = ["static-djangoadmin/"]
DEFAULT_FILE_STORAGE = "storages.backends.gcloud.GoogleCloudStorage"
STATICFILES_STORAGE = "storages.backends.gcloud.GoogleCloudStorage"
GS_DEFAULT_ACL = "publicRead"
STATIC_ROOT = "static-djangoadmin/"