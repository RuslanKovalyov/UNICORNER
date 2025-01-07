from django.shortcuts import render
from .models import Category


def home(request):
    categories = Category.objects.prefetch_related('products').all()
    return render(request, 'main/home.html', {'categories': categories})

def contacts(request):
    title = 'Contact Us'
    return render(request, 'main/contacts.html', {'title': title})

def terms_and_privacy(request):
    title = 'Terms and Privacy Policy'
    return render(request, 'main/terms_and_privacy.html', {'title': title})

# def opensource_license(request):
#     return render(request, 'main/opensource_license.html')

# def about(request):
#     return render(request, 'main/about.html')
