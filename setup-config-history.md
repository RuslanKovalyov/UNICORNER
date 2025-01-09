
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
    sudo chown -R www-data:www-data /home/ruslan/Desktop/UNICORNER/static
    sudo chown -R www-data:www-data /home/ruslan/Desktop/UNICORNER/media
    sudo chown -R ruslan:ruslan /home/ruslan/Desktop/UNICORNER/static
    sudo chmod -R 755 /home/ruslan/Desktop/UNICORNER/static
    sudo chmod -R 755 /home/ruslan/Desktop/UNICORNER/media
    #sudo systemctl reload nginx
```

## **NGINX**
```bash
    ...
    ...
```

## **Gunicorn**
```bash
    ...
    ...
```

