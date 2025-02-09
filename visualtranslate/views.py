from django.shortcuts import render

# A temporary/simple dict of words without any embedding space of related/similar meanings (only for demonstration)
words = {
    "apple": [{'apple-fruit': "image_path"}, {'apple-food': "image_path"}, {'apple-tree': "image_path"}, {'apple-red': "image_path"}, {'apple-juice': "image_path"}],
    "banana": [{'banana-fruit': "image_path"}, {'banana-food': "image_path"}, {'banana-yellow': "image_path"}, {'banana-palm': "image_path"}, {'banana-monkey': "image_path"}],
    "carrot": [{'carrot-vegetable': "image_path"}, {'carrot-food': "image_path"}, {'carrot-orange': "image_path"}, {'carrot-root': "image_path"}, {'carrot-rabbit': "image_path"}],
    "dog": [{'dog-animal': "image_path"}, {'dog-pet': "image_path"}, {'dog-friend': "image_path"}, {'dog-bark': "image_path"}, {'dog-tail': "image_path"}],
    "elephant": [{'elephant-animal': "image_path"}, {'elephant-big': "image_path"}, {'elephant-gray': "image_path"}, {'elephant-trunk': "image_path"}, {'elephant-tusk': "image_path"}],
    "fish": [{'fish-animal': "image_path"}, {'fish-water': "image_path"}, {'fish-swim': "image_path"}, {'fish-scale': "image_path"}, {'fish-ocean': "image_path"}],
    "love": [{'love-emotion': "image_path"}, {'love-heart': "image_path"}, {'love-care': "image_path"}, {'love-affection': "image_path"}, {'love-romance': "image_path"}],
    "coffee": [{'coffee-drink': "image_path"}, {'coffee-beverage': "image_path"}, {'coffee-caffeine': "image_path"}, {'coffee-morning': "image_path"}, {'coffee-aroma': "image_path"}],
    "python": [{'python-animal': "image_path"}, {'python-snake': "image_path"}, {'python-reptile': "image_path"}, {'python-cold-blooded': "image_path"}, {'python-slither': "image_path"}],
    # "python": ["language", "programming", "snake", "code", "computer"], # must process words in different contexts
}

def visualtranslate(request):
    word = request.GET.get("word", "") # Get word from user input (if any)
    
    # make sure the word is in lower case and no space added
    word_cleaned = word.lower().replace(" ", "")
    
    # use lower case to avoid case sensitivity
    if word_cleaned in words:    
        word_data = words[word_cleaned]
    else:
        word_data = None
        
    return render(request, "visualtranslate/visualtranslate.html", {"word": word, "word_data": word_data})
