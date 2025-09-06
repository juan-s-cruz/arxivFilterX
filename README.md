# ArxivFilterX

## Introduction
The project started as a personal attempt to filter out daily scientific articles in my field of research at the time. It has however served the purpose of teaching me about programming and incidentally machine learning. The project contains a website, based on the Django framework, that builds a database of papers from arXiv.org.

# Serving the website

After cloning the repository, you have two options:

## Docker
The project is currently containerized, `Dockerfile` included, and includes a `Makefile` with the necessary options to mount local models and use CUDA cores. 
After building the image with

`make build`

you can start the server with:

`make run_server`

## Python installation

To use a specific python installation you can install an environment with the necessary requirements with 

`make install_python_env`

or install the requirments from `requirements.txt` in the environment of your choosing and open a terminal (or Anaconda prompt if in Windows) on that directory. Then use:

`python manage.py runserver`

to serve the website. Below I describe the different apps and endpoints available.

# Apps within the website

## webFilter
This app integrates with arXiv.org API, fetches and saves recently released articles in a small local database. Only the article's title, abstract, link and upload date are stored, in order to rank the papers according to a set of white-words and black-words appearing in their abstracts.

Current version uses the arXiv API scraper based on 

https://github.com/Mahdisadjadi/arxivscraper

In its current state, it can be tested by running a local server with a randomly generated secret key for every session. 

This requires the python modules stated in `requirements.txt`, they are installed automatically with pip (or conda if you are using Anaconda), the packages below should be enough (versions are stated in the requirements file):

- python
- django
- pytz
- fuzzywuzzy

A sample database is included. 

http://127.0.0.1:8000/webFilter/


## llm_search app

This new app in the project is my attempt to put LLMs to good use and make our lives easier by summarizing, categorizing and answering questions.

Starting point a retrieving system with a locally run model of your choice.

http://127.0.0.1:8000/llm_search/