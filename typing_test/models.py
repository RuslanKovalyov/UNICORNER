from django.db import models
import random
import re
import html
from unidecode import unidecode

class Book(models.Model):
    credits = models.CharField(max_length=255, blank=True, null=True)  # Book source/author credit
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255, blank=True, null=True)
    content = models.TextField(help_text="Paste the full text of the book here.")
    release_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.author if self.author else 'Unknown'}"
    

    def get_random_paragraph(self, word_limit=50):
        """
        Returns a cleaned, random paragraph from the book, limited to a certain number of words.
        """

        # Split into paragraphs & remove empty lines
        paragraphs = [p.strip() for p in self.content.split("\n") if p.strip()]
        if not paragraphs:
            return ""

        # Randomly select a paragraph
        paragraph = random.choice(paragraphs)

        # 1️⃣ **Decode HTML entities** (Fix `&quot;` issue)
        paragraph = html.unescape(paragraph)

        # 2️⃣ **Convert non-English characters to closest English equivalent**
        paragraph = unidecode(paragraph)

        # 3️⃣ **Remove unwanted symbols, allowing only English letters, numbers, spaces & common punctuation**
        paragraph = re.sub(r"[^a-zA-Z0-9\s.!?;:,'\"-]", "", paragraph)

        # 4️⃣ **Replace double quotes with escaped double quotes
        paragraph = paragraph.replace('"', "'")

        # 5️⃣ **Trim paragraph to required word count**
        words = re.findall(r'\S+', paragraph)
        if len(words) > word_limit:
            paragraph = " ".join(words[:word_limit]) + "..."

        return paragraph

    def get_book(self):
        """
        Returns the full text of the book.
        """
        text = self.content
        
        # convert newlines to spaces & remove empty lines
        text = " ".join([line.strip() for line in text.split("\n") if line.strip()])
        
        # 1️⃣ **Decode HTML entities** (Fix `&quot;` issue)
        text = html.unescape(text)
        
        # 2️⃣ **Convert non-English characters to closest English equivalent**
        text = unidecode(text)
        
        # 3️⃣ **Remove unwanted symbols, allowing only English letters, numbers, spaces & common punctuation**
        text = re.sub(r"[^a-zA-Z0-9\s.!?;:,'\"-]", "", text)
        
        # 4️⃣ **Replace double quotes with escaped double quotes
        text = text.replace('"', "'")
        
        return text
        
        