Django website that builds a database of papers from arXiv.org and saves its title, abstract, link and upload date to rank papers according to a set of whitewords and blackwords.

Current version uses the arXiv API scraper based on 

https://github.com/Mahdisadjadi/arxivscraper

In its current state, it can be tested by running a local server with a randomly generated secret key for every session. 

This requires the python modules stated in `requirements.txt`, they are installed automatically with pip (or conda if you are using Anaconda), the packages below should be enough (versions are stated in the requirements file):

- python
- django
- pytz
- fuzzywuzzy

Clone the repository and open a terminal (or Anaconda prompt if in Windows) on that directory. Then use:

`python manage.py runserver`

and visit on your browser:

http://127.0.0.1:8000/webFilter/

A sample database is included. 
