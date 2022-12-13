FROM python:3.9

WORKDIR ./app
COPY . .
RUN chmod 775 script.sh
RUN pip install --upgrade pip && pip install --no-cache-dir --upgrade -r requirements.txt

# Download db certificate
RUN apt update
RUN apt install -y wget
RUN mkdir -p ~/.postgresql && \
    wget "https://storage.yandexcloud.net/cloud-certs/CA.pem" -O ~/.postgresql/root.crt && \
    chmod 0600 ~/.postgresql/root.crt

# Create db tables and files folders.
#RUN /usr/local/bin/python3 /app/postgres.py
#CMD gunicorn -b 0.0.0.0:5000 --timeout 9999 --workers 8 flask_app:app --reload
