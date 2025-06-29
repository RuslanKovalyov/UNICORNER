from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Category, Product
from datetime import datetime

# Unregister the default User admin
admin.site.unregister(User)

# Custom User Admin with warehouse access management
@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'warehouse_access')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')
    actions = ['grant_warehouse_access', 'revoke_warehouse_access']
    
    def warehouse_access(self, obj):
        """Display warehouse access status"""
        if obj.is_superuser:
            return "Admin (Full Access)"
        elif obj.is_staff:
            return "Manager (Warehouse Access)"
        else:
            return "User (No Warehouse Access)"
    warehouse_access.short_description = 'Warehouse Access Level'
    
    def grant_warehouse_access(self, request, queryset):
        """Action to grant warehouse access by making users staff"""
        updated = queryset.update(is_staff=True)
        self.message_user(request, f'{updated} users granted warehouse access (made staff).')
    grant_warehouse_access.short_description = "Grant warehouse access (make staff)"
    
    def revoke_warehouse_access(self, request, queryset):
        """Action to revoke warehouse access by removing staff status"""
        # Don't remove staff status from superusers
        updated = queryset.filter(is_superuser=False).update(is_staff=False)
        self.message_user(request, f'{updated} users had warehouse access revoked.')
    revoke_warehouse_access.short_description = "Revoke warehouse access (remove staff status)"

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