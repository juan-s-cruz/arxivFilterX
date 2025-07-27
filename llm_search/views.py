from django.shortcuts import render

from .llm_connector import call_llm


# Create your views here.
def index(request):
    answer = {"llm_says": call_llm()}
    return render(request, "llm_search/index.html", context=answer)
