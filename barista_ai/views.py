from django.shortcuts import render

def barista_ai_interface(request):
    """
    Main interface for Barista AI - renders the embedded Open Web UI
    """
    context = {
        'ai_server_url': 'https://ai.unicorner.coffee',
    }
    return render(request, 'barista_ai/interface.html', context)
