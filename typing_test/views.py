from django.shortcuts import render
from .models import Book
import random
import re

def typing_test(request):
    word_limit = request.GET.get("words", 50)
    word_limit = max(10, min(int(word_limit), 200))

    # Get cleaning options and timer value from the request
    remove_punctuation = request.GET.get("remove_punctuation", "false") == "true"
    remove_numbers = request.GET.get("remove_numbers", "false") == "true"
    lowercase = request.GET.get("lowercase", "false") == "true"
    timer = request.GET.get("timer", "60")

    book = Book.objects.order_by("?").first()
    if book:
        test_text = book.get_book()
        length = 2000
        start = test_text.find(" ", random.randint(0, len(test_text) - length))
        start += 1
        test_text = test_text[start:start+length]

        if remove_punctuation:
            test_text = re.sub(r"[^\w\s]", "", test_text)
        if remove_numbers:
            test_text = re.sub(r"\d+", "", test_text)
        if lowercase:
            test_text = test_text.lower()
    else:
        test_text = "No books available. Please add books in the admin panel."

    return render(request, "typing/test.html", {
        "test_text": test_text,
        "remove_punctuation": remove_punctuation,
        "remove_numbers": remove_numbers,
        "lowercase": lowercase,
        "timer": timer
    })
