from django.contrib import admin
from .models import Category, Product

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'title', 'category', 'price')
    search_fields = ('name', 'category__name')
    list_filter = ('category',)

# change the admin site header from Django Administration to UNICORNER CLUB
admin.site.site_header = 'UNICORNER CLUB'
