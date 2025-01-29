from django.contrib import admin
from .models import Book

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "created_at")
    search_fields = ("title", "author", "content")
