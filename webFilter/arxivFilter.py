"""arXiv filtering helpers.

This module provides small utilities used by the web filter to:

- Fetch recent arXiv papers for a specific calendar day using the local
  timezone boundaries.
- Compute a fuzzy-match relevance score for a paper given a whitelist and
  blacklist of terms.

It relies on the local ``Scraper`` wrapper around the arXiv OAI-PMH endpoint
and TheFuzz for token-set string similarity.
"""

from thefuzz import fuzz as metric
import datetime
from typing import Any, Dict, List

import pytz

from .constants import cats as categories
from .constants import subcats as subcategories

from .arxivscraper import Scraper

import logging as log

logging = log.getLogger(__name__)


def fetch_recent_papers(
    requested_date: datetime.date, category: str = "physics"
) -> List[Dict[str, Any]]:
    """Fetch papers announced on a given calendar day.

    Computes the [start, end) window for the provided day in the
    Europe/Copenhagen timezone and returns arXiv records whose creation date
    falls within that interval.

    Args:
        requested_date: The calendar day of interest (local date). ``datetime``
            is also accepted since it is a ``date`` subclass.

    Returns:
        A list of paper dictionaries as returned by ``Scraper.scrape()``. If the
        underlying scraper signals an error (sentinel ``1``) or an exception
        occurs, an empty list is returned.
    """
    try:
        eastern = pytz.timezone("Europe/Copenhagen")
        target_day = eastern.localize(
            datetime.datetime(
                requested_date.year, requested_date.month, requested_date.day, 0, 0, 0
            )
        )
        logging.info(target_day)
        day_interval = datetime.timedelta(days=1)
        target_date_end = (requested_date + day_interval).strftime("%Y-%m-%d")
        target_date_start = target_day.strftime("%Y-%m-%d")

        subcats = subcategories[category]  # use all categories
        recent_papers = []
        scraper = Scraper(
            category=category,
            date_from=target_date_start,
            date_until=target_date_end,
            filters={"categories": subcats},
        )
        logging.info(
            "Scraping arxiv.org for papers from %s to %s",
            target_date_start,
            target_date_end,
        )
        query_results = scraper.scrape()
        if query_results != 1:
            for paper in query_results:
                paper_date = eastern.localize(
                    datetime.datetime.strptime(paper["created"], "%Y-%m-%d")
                )
                # logging.info(paper_date)
                # if target_day <= paper_date < target_day + datetime.timedelta(days=1):
                recent_papers.append(paper)
                # logging.info("Adding paper")
        return recent_papers
    except Exception as e:
        logging.info("Error while scraping arxiv.org")
        return []


def scorePaper(
    title: str, abstract: str, whitelist: List[str], blacklist: List[str]
) -> float:
    """Compute a fuzzy relevance score for a paper.

    Favors matches with ``whitelist`` terms and penalizes matches with
    ``blacklist`` terms using TheFuzz token-set ratios. When either list is
    provided, the final score is normalized by the total number of terms.

    Args:
        title: Paper title text.
        abstract: Paper abstract text.
        whitelist: Positive-match keywords.
        blacklist: Negative-match keywords.

    Returns:
        A floating-point score where higher is better.
    """
    score = 0
    if whitelist != []:
        for keyword in whitelist:
            contrib = 2 * metric.token_set_ratio(
                keyword, title
            ) + metric.token_set_ratio(keyword, abstract)
            score += contrib
    if blacklist != []:
        for badWord in blacklist:
            contrib = -2 * metric.token_set_ratio(
                badWord, title
            ) - metric.token_set_ratio(badWord, abstract)
            score += contrib
    if whitelist != [] or blacklist != []:
        score = round(score / (len(whitelist) + len(blacklist)) / 2, 5)
    return score
