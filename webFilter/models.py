from django.db import models

class Article(models.Model):
    title_text = models.CharField(max_length=200, unique=True)
    pub_date = models.DateField('date published')
    abstract = models.TextField()
    authors = models.CharField(max_length=400)
    real_url = models.CharField(max_length=100)
    rank = models.FloatField(default=0)
    
    def  __str__(self):
        return self.title_text
    
    def number_of_authors(self):
        split_authors_and = self.authors.split(' and ')
        sep_authors = []
        for item in split_authors_and:
            item = item.split(', ')
            for auth in item:
                sep_authors.append(auth)
        return len(sep_authors)
    
    def is_single_author(self):
        return self.number_of_authors(self) == 1
    
    def set_abstract(self, new_abstract):
        self.abstract = new_abstract
    
class Word(models.Model):
    term = models.CharField(max_length=50, unique=True)
    is_white = models.BooleanField(default=True)

    def __str__(self):
        return self.term