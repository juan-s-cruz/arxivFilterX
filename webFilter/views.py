from django.shortcuts import render
from django.urls import reverse
from django.http import Http404

#from django.http import HttpResponseRedirect
#from django.template import loader

import datetime
from .models import Article
from .models import Word
from .arxivFilter import scorePaper, fetch_recent_papers

default_length=7

def previous_working_day(date):
    candidate = date - datetime.timedelta(days=1)
    if candidate.weekday() == 6:
        return candidate - datetime.timedelta(days=2)
    elif candidate.weekday() == 5:
        return candidate - datetime.timedelta(days=1)
    else:
        return candidate

"""
TODO: Filter out weekends perhaps
"""  
def check_date(date):
    return date - datetime.timedelta(days=1)

    
def refresh_rank(articles):
    whitelist = []
    for word in Word.objects.filter(is_white=True):
            whitelist.append(word.term)
    blacklist = []
    for word in Word.objects.filter(is_white=False):
            blacklist.append(word.term)
    for a in articles:
        a.rank=scorePaper(a.title_text, a.abstract, whitelist, blacklist)
        a.save()
    

def index(request):
    return update(request, 0)

# Updates the list of papers according to the request received, the days to look back and the length of the list
def update(request, day_offset, no_to_display=default_length):
    date_request = datetime.date.today() - datetime.timedelta(days=day_offset)
    query_date = check_date(date_request)
    # if len(Article.objects.filter(pub_date=query_date)) == 0:
    try:
        papers = fetch_recent_papers(query_date)
        for paper in papers:
            # print('Entering for loop within scraped papers')
            try:
                myArt = Article.objects.get(title_text=paper['title'])
                myArt.pub_date= (datetime.datetime.strptime(paper['created'],'%Y-%m-%d')).date()
                authors_str = ""
                for auth in paper['authors'][:-1]:
                    authors_str+= auth + ", "
                authors_str += paper['authors'][-1]
                myArt.authors= authors_str
                myArt.set_abstract(paper['abstract'])
                myArt.real_url=paper['url']
                myArt.save()
            except Article.DoesNotExist:
                # print('Article was not in database, creating new article.')
                paper_pubDate = (datetime.datetime.strptime(paper['created'],'%Y-%m-%d')).date()
                # print(str(paper['authors']))
                authors_str = ""
                for auth in paper['authors'][:-1]:
                    authors_str+= auth + ", "
                authors_str += paper['authors'][-1]
                myNewArt = Article(title_text=paper['title'], pub_date=paper_pubDate, abstract=paper['abstract'], authors=authors_str, real_url=paper['url'])
                myNewArt.save()                    
    except:
        raise Http404("Could not fetch recent papers.")
    # else:
    #     print('Papers already in database for ' + str(query_date))    
    try:
        day_before = previous_working_day(date_request)
        articles = Article.objects.filter(pub_date__gte=day_before, pub_date__lte=date_request)
        print("Showing papers from " + datetime.datetime.strftime(day_before,'%Y-%m-%d') + ". No. of papers: " + str(len(articles)))
        refresh_rank(articles)
        highest_ranked_list = articles.order_by('rank').reverse()[:no_to_display]
        whitelist = Word.objects.filter(is_white=True)
        blacklist = Word.objects.filter(is_white=False)
        if day_offset==0:
            context = {'dateToDisplay': date_request,'go_back_url':reverse('update', args=(day_offset+1,default_length)), 'go_forward_url':reverse('update', args=(day_offset,default_length)), 'current_url':reverse('update', args=(day_offset,7)),
            'highest_ranked_list': highest_ranked_list, 'whitelist': whitelist, 'blacklist': blacklist, 
            }
        else:
            context = { 'dateToDisplay': date_request, 'go_back_url':reverse('update', args=(day_offset+1,default_length)), 'go_forward_url':reverse('update', args=(day_offset-1,default_length)), 'current_url':reverse('update', args=(day_offset,7)),
            'highest_ranked_list': highest_ranked_list, 'whitelist': whitelist, 'blacklist': blacklist, 
            }
        return render(request, 'webFilter/index.html', context)
    except Article.DoesNotExist:
        raise Http404("No articles matched the criteria")

def add_word(request, word_type):
    if( word_type == 'white'):
        status=True
    else:
        status=False
    a = Word(term=request.POST['word_toAdd'], is_white=status)
    a.save()
    return update(request,0)
        
def remove(request, word_type):
    word_list = dict(request.POST)['words_to_remove']
    for word in word_list:
        w = Word.objects.get(term=word)
        w.delete()
    return update(request,0)
        

    