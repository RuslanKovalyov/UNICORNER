from django.shortcuts import render
from .models import Category


def home(request):
    categories = Category.objects.prefetch_related('products').all()
    return render(request, 'main/home.html', {'categories': categories})

def contacts(request):
    return render(request, 'main/contacts.html')
