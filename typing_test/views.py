from django.shortcuts import render
from .models import Book
import random

def typing_test(request):
    word_limit = request.GET.get("words", 50)  # Allow setting word limit via URL
    word_limit = max(10, min(int(word_limit), 200))  # Restrict range

    # Select a random book
    book = Book.objects.order_by("?").first()

    if book:
        test_text = book.get_book()
        
        
        # restrict the letters limit to 1000
        length = 2000
        # start from a random word in the text and get the substring of length 1000 laters
        start = test_text.find(" ", random.randint(0, len(test_text) - length))
        # delete the spaces at the start
        start += 1
        
        # get the substring of length 1000
        test_text = test_text[start:start+length]
        
        # test_text = book.get_random_paragraph(word_limit)
    else:
        test_text = "No books available. Please add books in the admin panel."

    return render(request, 'typing/test.html', {'test_text': test_text})
