from django.shortcuts import render
from django.http import JsonResponse, HttpResponseBadRequest
from .llm_connector import call_llm
from .vector_store import search as vector_search

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


def search(request):
    if request.method != "GET":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    query = (request.GET.get("q", "") or "").strip()
    if not query:
        return HttpResponseBadRequest("Missing 'q' parameter")

    k_param = request.GET.get("k")
    try:
        k = int(k_param) if k_param else 5
        k = max(1, min(k, 50))
    except Exception:
        return HttpResponseBadRequest("Invalid 'k' parameter")

    try:
        results = vector_search(query, k=k)
        cleaned = []
        for r in results:
            item = {
                k: r.get(k)
                for k in [
                    "id",
                    "title",
                    "text",
                    "authors",
                    "abstract",
                    "pub_date",
                    "url",
                ]
                if k in r
            }
            if "distance" in r:
                item["distance"] = r["distance"]
            elif "_distance" in r:
                item["distance"] = r["_distance"]
            cleaned.append(item)
        return JsonResponse({"query": query, "k": k, "results": cleaned})
    except Exception as e:
        logging.exception("Vector search failed: %s", e)
        return JsonResponse({"error": "Search failed"}, status=500)
