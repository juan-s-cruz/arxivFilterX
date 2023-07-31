# -*- coding: utf-8 -*-

from fuzzywuzzy import fuzz as metric
import datetime
import pytz
# import imaplib
# import time
from .arxivscraper import Scraper

#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------

# Takes in a given date and fetches the arXiv articles made public between the given date and the following day
def fetch_recent_papers(requested_date):
    try:
        eastern = pytz.timezone("US/Eastern")
        target_day = eastern.localize(datetime.datetime(requested_date.year, requested_date.month, requested_date.day,0,0,0))
        print(target_day)
        day_interval = datetime.timedelta(days=1)
        target_date_end = (requested_date + day_interval).strftime("%Y-%m-%d")
        target_date_start = target_day.strftime("%Y-%m-%d")
        print("Start of interval: " + str(target_date_start))
        print("End of interval: " + str(target_date_end))
        cats = ["astro-ph.CO","astro-ph.HE","gr-qc","hep-ph","hep-th","math-ph","physics.comp-ph"]
        recent_papers = []
        scraper = Scraper(category='physics', date_from=target_date_start,date_until=target_date_end, filters={'categories':cats})
        query_results = scraper.scrape()
        if query_results != 1:        
            for paper in query_results:
                paper_date = eastern.localize(datetime.datetime.strptime(paper['created'],'%Y-%m-%d'))
                # print(paper_date)
                # if target_day <= paper_date < target_day + datetime.timedelta(days=1):
                recent_papers.append(paper)
                # print("Adding paper")
        return recent_papers
    except Exception as e:
        print("Error while scraping arxiv.org")


def scorePaper(title, abstract, whitelist, blacklist):
    score = 0
    if whitelist != []:
        for keyword in whitelist:
            contrib = 2*metric.token_set_ratio(keyword,title) + metric.token_set_ratio(keyword,abstract) 
            score += contrib
    if blacklist != []:
        for badWord in blacklist:
            contrib = -2*metric.token_set_ratio(badWord,title) - metric.token_set_ratio(badWord,abstract)
            score += contrib
    if ( whitelist != [] or blacklist != [] ):
        score = round(score / ( len(whitelist)+len(blacklist) ) / 2, 5)
    return score    

