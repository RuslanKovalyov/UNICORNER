"""
Database configuration for Search app
Completely separate from main project database
"""

import os
from pathlib import Path

# Get search app directory
SEARCH_APP_DIR = Path(__file__).resolve().parent.parent

# Separate database for search app
SEARCH_DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': SEARCH_APP_DIR / 'database' / 'search.sqlite3',
    }
}

# Database router to route search app to its own database
class SearchDatabaseRouter:
    """
    A router to control all database operations on models for the search app
    """
    
    search_app_labels = {'search'}
    
    def db_for_read(self, model, **hints):
        """Suggest the database to read from."""
        if model._meta.app_label in self.search_app_labels:
            return 'search_db'
        return None
    
    def db_for_write(self, model, **hints):
        """Suggest the database to write to."""
        if model._meta.app_label in self.search_app_labels:
            return 'search_db'
        return None
    
    def allow_relation(self, obj1, obj2, **hints):
        """Allow relations if models are in the same app."""
        db_set = {'default', 'search_db'}
        if obj1._state.db in db_set and obj2._state.db in db_set:
            return True
        return None
    
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """Ensure that the search app's models get created on the right database."""
        if app_label in self.search_app_labels:
            return db == 'search_db'
        elif db == 'search_db':
            return False
        return None
