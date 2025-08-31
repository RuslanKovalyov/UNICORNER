from django.shortcuts import render


def search_view(request):
    """Simple search view that prints query to console"""
    query = request.GET.get('q', '')
    
    # Print the search query to Python console
    if query:
        print(f"Search query: {query}")
    
    context = {
        'query': query,
    }
    
    return render(request, 'search_engine/search.html', context)
