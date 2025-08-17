from django.shortcuts import render
from .llm_connector import call_llm

import logging as log

logging = log.getLogger(__name__)


# Create your views here.
def index(request):
    return render(request, "llm_search/index.html")


def explain(request):
    if request.method == "POST":
        topic = request.POST.get("topic", "")
        logging.info(f"Received topic: {topic}")
        if topic:
            explanation = call_llm(topic)
            return render(
                request,
                "llm_search/index.html",
                {"explanation": explanation, "topic": topic},
            )
    return render(request, "llm_search/index.html")
