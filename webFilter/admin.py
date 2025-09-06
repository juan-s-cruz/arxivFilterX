from django.contrib import admin

from .models import Article
from .models import Word

admin.site.register(Article)
admin.site.register(Word)