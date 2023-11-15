web: gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 8 --timeout 0 homeinventoryapp.wsgi:application
makemigrations: python manage.py makemigrations homeinventoryapi
migrate: python manage.py migrate collectstatic --noinput --clear
createuser: python manage.py createsuperuser --username admin --email admin@admin.com --noinput
