# -*- coding: utf-8 -*-

from fuzzywuzzy import fuzz as metric
import datetime
import pytz
# import imaplib
import time
import arxivscraper

#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------

# ORG_EMAIL   = "@gmail.com"
# FROM_EMAIL  = "   " + ORG_EMAIL
# FROM_PWD    = "   "
# SMTP_SERVER = "imap.gmail.com"
# SMTP_PORT   = 993

#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------

def fetch_recent_papers(requested_date):
    try:
        eastern = pytz.timezone("US/Eastern")
        target_day = eastern.localize(datetime.datetime(requested_date.year, requested_date.month, requested_date.day,0,0,0))
        day_interval = datetime.timedelta(days=-1)
        target_date_end = target_day.strftime("%Y-%m-%d")
        target_date_start = (requested_date + day_interval).strftime("%Y-%m-%d")
        print("Start of intervarl: " + str(target_date_start))
        print("End of intervarl: " + str(target_date_end))
        cats = ["astro-ph.CO","astro-ph.HE","gr-qc","hep-ph","hep-th","math-ph","physics.comp-ph"]
        
        recent_papers = []
        scraper = arxivscraper.Scraper(category='physics', date_from=target_date_start,date_until=target_date_end, filters={'categories':cats})
        query_results = scraper.scrape()
        # counter = 0
        for paper in query_results:
            paper_date = eastern.localize(datetime.datetime.strptime(paper['created'],'%Y-%m-%d'))
            print(paper_date)
            if target_day + 2*day_interval <= paper_date < target_day:
                recent_papers.append(paper)
                print("Adding paper")
            # else:
                # print('Discarding paper')
                # counter = counter + 1 
        return recent_papers
    except Exception as e:
        print("Error while scraphing arxiv.org")


# def read_email(dateRequest):
#     try:
#         print('Requested date: ' + str(dateRequest))
#         mail = imaplib.IMAP4_SSL(SMTP_SERVER)
#         mail.login(FROM_EMAIL,FROM_PWD)        
#         mail.select('inbox')      
#         dateCrit = "(ON {0})".format(dateRequest.strftime("%d-%b-%Y") )
#         type, data = mail.search(None, '(FROM "no-reply@arXiv.org")', dateCrit)
#         mail_ids = data[0]
#         id_list = mail_ids.split()
#         latest_email_id = id_list[-1]
#         typ, data =  mail.fetch(latest_email_id, "(BODY[TEXT])") 
#         typ, data2 =  mail.fetch(latest_email_id, "(BODY[HEADER.FIELDS (DATE)])") 
#         date_time_str = str(data2[0][1]).replace("b'Date: ","").replace("\\r\\n\\r\\n'","")[:-6]
#         date_time_obj = datetime.datetime.strptime(date_time_str, '%a, %d %b %Y %H:%M:%S')
#         msgDate = dateRequest
#         #There is a date difference with the stamp in the actual email
#         body = str(data[0][1])[2:-1]
#         mail.close()
#         mail.logout()
#         return body, msgDate
#     except Exception as e:
#         print(str(e))
        
# def extractor(paper):
#     entry = {}
#     entry["title"] = paper.title
#     entry["authors"] = list(map(lambda auth: auth.name, paper.authors))
#     entry["abstract"] = paper.summary    
#     entry["link"] = paper.links[0].href
#     entry["pub_date"] = paper.published
#     return entry
        
# def arxivParser(recent_papers, papers):
#     for paper in recent_papers:    
#         new_entry = extractor(paper)
#         papers.append(new_entry)
    # sep = "------------------------------------------------------------------------------"
    # myList = paper.split(sep)[6:-1]
    # i = 0    
    # while myList[i].find("%%--%%--") == -1:
    #     entry = extractor(myList[i])
    #     papers.append(entry)
    #     i+=1 

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

