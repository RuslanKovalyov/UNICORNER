from django.contrib import admin
from .models import Category, Product
from datetime import datetime

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'title', 'category', 'price')
    search_fields = ('name', 'category__name')
    list_filter = ('category',)

# Customizing the admin site header based on the time of day
if datetime.now().hour < 12:
    admin.site.site_header = 'Good Morning'
elif 12 <= datetime.now().hour < 18:
    admin.site.site_header = 'Good Afternoon'
else:
    admin.site.site_header = 'Good Evening'

admin.site.index_title = 'UNICORNER coffee'
admin.site.site_title = 'UNICORNER coffee'