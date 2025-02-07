from django.shortcuts import render

# hello world html
def visualtranslate(request):
    return render(request, 'visualtranslate/visualtranslate.html')
