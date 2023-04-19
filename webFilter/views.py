from django.shortcuts import render
from django.urls import reverse
from django.http import Http404

#from django.http import HttpResponseRedirect
#from django.template import loader

import datetime
import holidays
from .models import Article
from .models import Word
from .arxivFilter import scorePaper, fetch_recent_papers

default_length=7

def is_working_day(check_day, holidays=holidays.US()):
    the_weekday = check_day.weekday()
    if (the_weekday != 5 and the_weekday != 6): # and check_day not in holidays):
        return True
    else:
        return False

def previous_working_day(check_day):
    most_recent = check_day - datetime.timedelta(1)
    if ( is_working_day(most_recent) ):
        return most_recent
    else:
        return previous_working_day(most_recent)
    
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
    date_request = previous_working_day(datetime.date.today())
    for day in range(day_offset):
        date_request = previous_working_day(date_request)
    print(previous_working_day(date_request))
    if len(Article.objects.filter(pub_date=previous_working_day(date_request))) == 0:
        try:
            print('Requested date: ' + str(date_request))
            date_request = previous_working_day(date_request) + datetime.timedelta(days=1)
            print('Passed date to filter: ' + str(date_request))
            papers = fetch_recent_papers(date_request )
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
            raise Http404("Could not fetch email")
    else:
        print('Papers already in database for ' + str(date_request))    
    try:
        day_before = date_request + datetime.timedelta(days=-1)
        articles = Article.objects.filter(pub_date=day_before)
        print("Showing papers from " + datetime.datetime.strftime(day_before,'%Y-%m-%d') + ". No. of papers: " + str(len(articles)))
        refresh_rank(articles)
        highest_ranked_list = articles.order_by('rank').reverse()[:no_to_display]
        whitelist = Word.objects.filter(is_white=True)
        blacklist = Word.objects.filter(is_white=False)
        if day_offset==0:
            context = { 'dateToDisplay': date_request, 'go_back_url':reverse('update', args=(day_offset+1,default_length)), 'go_forward_url':reverse('update', args=(day_offset,default_length)), 'current_url':reverse('update', args=(day_offset,7)),
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
    return update(request)
        
def remove(request, word_type):
    word_list = dict(request.POST)['words_to_remove']
    for word in word_list:
        w = Word.objects.get(term=word)
        w.delete()
    return update(request)
        

    