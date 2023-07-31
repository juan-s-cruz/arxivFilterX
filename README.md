Django website that builds a database of papers from arXiv.org and saves its title, abstract, link and upload date to rank papers according to a set of whitewords and blackwords.

Current version uses the arXiv API scraper based on 

https://github.com/Mahdisadjadi/arxivscraper

In its current state, it can be tested by running a local server. To do so, clone the repository and open a terminal on that directory. Then use 
`python manage.py runserver`

and visit on your browser:

http://127.0.0.1:8000/webFilter/

A sample database is included. 
