#! /bin/bash


/usr/local/bin/python3 /app/postgres.py

gunicorn -b 0.0.0.0:5000 --timeout 9999 --workers 8 flask_app:app --reload
