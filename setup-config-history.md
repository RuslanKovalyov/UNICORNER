
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


