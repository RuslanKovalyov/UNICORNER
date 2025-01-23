from django.shortcuts import render

def typing_test(request):
    # Hardcoded text for now
    test_text = "The quick brown fox jumps over the lazy dog."
    return render(request, 'typing/test.html', {'test_text': test_text})
