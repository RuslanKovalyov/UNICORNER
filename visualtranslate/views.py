from django.shortcuts import render

def visualtranslate(request):
    word = request.GET.get("word", "")  # Get word from user input (if any)
    return render(request, "visualtranslate/visualtranslate.html", {"word": word})
