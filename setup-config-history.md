
# Development History
This file contains the history of commands, configurations, and development steps used to build the UNICORNER COFFEE project.
It keeps the README focused on getting started while this file tracks internal development details, and is also useful for learning and reproducing purposes.

## **Create Django project and Main App**  
```bash
    mkdir UNICORNER
    cd UNICORNER
    python3.13 -m venv venv
    source venv/bin/activate
    pip install Django==5.1.4
    django-admin startproject unicorner .
    python3 -m django startapp main
    # Apply initial database migrations to set up the default Django tables
    python3 manage.py migrate
    # Test the Server
    python3 manage.py runserver
```

## **Setting Up Environment Variables**
create a .env file to store sensitive data
```bash
    pip install python-decouple
```

## **Install Pillow to handle image-related functionality, such as processing and storing images in ImageField**
```bash
    python -m pip install pillow==11.1.0
```

## **Create Models of Products and Run the following commands to create the database tables**
```bash
    python manage.py makemigrations
    python manage.py migrate
```

## **Update requirements.txt**
```bash
    python -m pip freeze > requirements.txt
```

## **Create a Superuser**
```bash
    python manage.py createsuperuser
```

# Production server

## **Python Installation**
```bash
    # 1. Update the System
    sudo apt update && sudo apt upgrade -y

    # 2. Install Required Build Dependencies
    sudo apt install -y software-properties-common build-essential \
        libssl-dev libffi-dev zlib1g-dev libbz2-dev libreadline-dev \
        libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev \
        xz-utils tk-dev libxml2-dev libxmlsec1-dev liblzma-dev

    # 3. Download Python 3.13.1 Source Code
    wget https://www.python.org/ftp/python/3.13.1/Python-3.13.1.tgz

    # 4. Extract the Source Code
    tar xvf Python-3.13.1.tgz
    cd Python-3.13.1

    # 5. Configure the Build with Optimizations
    ./configure --enable-optimizations

    # 6. Compile and Install Python
    make -j$(nproc)
    sudo make altinstall

    # 7. Verify the Installation
    python3.13 --version

    # 8. Clean Up Installation Files
    cd ..
    rm -rf Python-3.13.1 Python-3.13.1.tgz
```

## **Move project to the server**
    ...
    ...
    ...

## **Collect all static files to the STATIC_ROOT directory
```bash
    python manage.py collectstatic
```

## **Set Permissions**
```bash
    sudo chown -R ruslan:www-data /home/ruslan/Desktop/UNICORNER/media
    sudo chmod -R 775 /home/ruslan/Desktop/UNICORNER/media
    sudo chown -R ruslan:www-data /home/ruslan/Desktop/UNICORNER/static
    sudo chmod -R 775 /home/ruslan/Desktop/UNICORNER/static

    # sudo systemctl daemon-reload
    # sudo systemctl restart unicorner_django_app.service
    # sudo systemctl reload nginx
```

## **NGINX**
```bash
    # sudo nano /etc/nginx/sites-available/unicorner

    # Upstream to Gunicorn
    upstream server_django {
        server 127.0.0.1:8080;
    }

    server {
        listen 443 ssl http2; # managed by Certbot
        server_name unicorner.coffee www.unicorner.coffee;

        ssl_certificate /etc/letsencrypt/live/unicorner.coffee/fullchain.pem; # managed by Certbot
        ssl_certificate_key /etc/letsencrypt/live/unicorner.coffee/privkey.pem; # managed by Certbot
        include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot
        ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # managed by Certbot

        # Serve Static Files
        location /static/ {
            alias /home/ruslan/Desktop/UNICORNER/static/;
            autoindex off;
            access_log off;
            expires max;
        }

        # Serve Media Files
        location /media/ {
            alias /home/ruslan/Desktop/UNICORNER/media/;
            autoindex off;
            access_log off;
            expires max;
        }

        # Proxy Pass to Django
        location / {
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header Host $host;
            proxy_redirect off;
            client_max_body_size 50M;
            proxy_pass http://server_django;
        }
    }

    # Redirect www to non-www with HTTPS
    server {
        listen 80;
        server_name www.unicorner.coffee;
        return 301 https://unicorner.coffee$request_uri;
    }

    # Redirect HTTP to HTTPS
    server {
        listen 80;
        server_name unicorner.coffee www.unicorner.coffee;
        return 301 https://unicorner.coffee$request_uri;
    }

    # sudo nginx -t
    # sudo systemctl reload nginx

```

## **Gunicorn**
```bash
    # sudo nano /etc/systemd/system/unicorner_django_app.service

    [Unit]
    Description=Gunicorn daemon for unicorner_django_app
    After=network.target

    [Service]
    PermissionsStartOnly=true
    User=ruslan
    Group=www-data
    WorkingDirectory=/home/ruslan/Desktop/UNICORNER
    ExecStart=/home/ruslan/Desktop/UNICORNER/venv/bin/python3 -m gunicorn --workers 8 --bind 0.0.0.0:8080 unicorner.wsgi:application
    ExecReload=/bin/kill -s HUP $MAINPID
    KillMode=mixed
    TimeoutStopSec=5
    PrivateTmp=true
    Restart=on-failure

    [Install]
    WantedBy=multi-user.target

    # sudo systemctl restart unicorner_django_app.service

```

