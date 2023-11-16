import os

env_content = os.environ.get("APPLICATION_SETTINGS_DEV")
print(f'APPLICATION_SETTINGS_DEV: {env_content}')
print(env_content, file=open('.env', 'a'))
