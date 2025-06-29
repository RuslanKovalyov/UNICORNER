from django.contrib.auth.decorators import user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy


def staff_required(function=None, redirect_field_name='next', login_url='admin:login'):
    """
    Decorator for views that checks that the user is logged in and is a staff member.
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated and u.is_staff,
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator


def manager_or_admin_required(user):
    """
    Check if user is staff (manager) or superuser (admin)
    """
    return user.is_authenticated and (user.is_staff or user.is_superuser)


class WarehouseAuthenticationMiddleware:
    """
    Middleware to protect warehouse URLs from non-staff users
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if the request is for warehouse app
        if request.path.startswith('/warehouse/'):
            # Allow access only to staff members
            if not (request.user.is_authenticated and request.user.is_staff):
                # Redirect to admin login
                return redirect(f'/admin/login/?next={request.path}')
        
        response = self.get_response(request)
        return response
