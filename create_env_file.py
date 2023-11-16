import os

env_content = os.environ.get("APPLICATION_SETTINGS_DEV")
print(f'APPLICATION_SETTINGS_DEV loaded?: {env_content is not None}')
print(env_content, file=open('.env', 'a'))
