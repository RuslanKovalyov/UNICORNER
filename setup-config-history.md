
# Development History
This file contains the history of commands, configurations, and development steps used to build the UNICORNER COFFEE project.
It keeps the README focused on getting started while this file tracks internal development details, and is also useful for learning and reproducing purposes.

## **Create Django project and Main App**  
```bash
    cd UNICORNER
    source venv/bin/activate
    django-admin startproject unicorner .
    python3 -m django startapp main
    # Apply initial database migrations to set up the default Django tables
    python3 manage.py migrate
    # Test the Server
    python3 manage.py runserver
```

## **Setting Up Environment Variables**
.env file to store sensitive data
```bash
...
...
...

```