"""ArXiv scraping utilities.

A Python module to retrieve records from arXiv.org for given
categories and a specific date range.

Author: Mahdi Sadjadi (sadjadi.seyedmahdi[AT]gmail[DOT]com)
Edited: Juan S. Cruz (jscruz19[AT]gmail[DOT]com)
"""

from __future__ import print_function
from urllib.error import HTTPError
from urllib.request import urlopen
import xml.etree.ElementTree as ET
import datetime
import time
from typing import Dict, List, Optional, Union

import logging as log


logging = log.getLogger(__name__)

from .constants import OAI, ARXIV, BASE


class Record(object):
    """Holds a single arXiv record.

    This is a light wrapper around an ``xml.etree.ElementTree.Element``
    node that provides convenient accessors for common arXiv metadata
    fields.

    Args:
      xml_record: XML element representing an ``arXiv:arXiv`` record.

    Attributes:
      xml: Backing XML element for the record.
      id: The arXiv identifier, e.g. ``2301.01234``.
      url: The human-readable arXiv abstract URL for the record.
      title: The paper title.
      abstract: The paper abstract with newlines normalized to spaces.
      cats: Space-separated category string.
      created: ISO 8601 creation date string.
      updated: ISO 8601 last-updated date string.
      doi: DOI string if provided, otherwise empty string.
      authors: List of author full names (``First Last``).
      affiliation: List of affiliations for the authors, if available.
    """

    def __init__(self, xml_record: ET.Element) -> None:
        """Initializes a Record from an XML node.

        Args:
          xml_record: XML element for the record (``arXiv:arXiv``).
        """
        self.xml = xml_record
        self.id = self._get_text(ARXIV, "id")
        self.url = "https://arxiv.org/abs/" + self.id
        self.title = self._get_text(ARXIV, "title")
        self.abstract = self._get_text(ARXIV, "abstract")
        self.cats = self._get_text(ARXIV, "categories")
        self.created = self._get_text(ARXIV, "created")
        self.updated = self._get_text(ARXIV, "updated")
        self.doi = self._get_text(ARXIV, "doi")
        self.authors = self._get_authors()
        self.affiliation = self._get_affiliation()

    def _get_text(self, namespace: str, tag: str) -> str:
        """Returns the text content of a namespaced XML tag.

        Args:
          namespace: XML namespace prefix string (e.g., ``ARXIV``).
          tag: Name of the tag to find within the record.

        Returns:
          The stripped text content if present, otherwise an empty string.
        """
        try:
            return self.xml.find(namespace + tag).text.strip().replace("\n", " ")
        except:
            return ""

    def _get_name(self, parent: ET.Element, attribute: str) -> str:
        """Returns a text attribute for an author element.

        Args:
          parent: Author XML element.
          attribute: Name of the child tag to retrieve.

        Returns:
          The text of the attribute if present, otherwise ``"n/a"``.
        """
        try:
            return parent.find(ARXIV + attribute).text
        except:
            return "n/a"

    def _get_authors(self) -> List[str]:
        """Extracts full author names.

        Returns:
          List of author names in ``First Last`` order.
        """
        authors_xml = self.xml.findall(ARXIV + "authors/" + ARXIV + "author")
        last_names = [self._get_name(author, "keyname") for author in authors_xml]
        first_names = [self._get_name(author, "forenames") for author in authors_xml]
        full_names = [a + " " + b for a, b in zip(first_names, last_names)]
        return full_names

    def _get_affiliation(self) -> List[str]:
        """Extracts affiliations for the authors.

        Returns:
          List of affiliation strings if present; otherwise an empty list.
        """
        authors = self.xml.findall(ARXIV + "authors/" + ARXIV + "author")
        try:
            affiliation = [
                author.find(ARXIV + "affiliation").text for author in authors
            ]
            return affiliation
        except:
            return []

    def output(self) -> Dict[str, Union[str, List[str]]]:
        """Returns the record as a dictionary.

        Returns:
          A mapping with keys: ``title``, ``id``, ``abstract``, ``categories``,
          ``doi``, ``created``, ``updated``, ``authors``, ``affiliation``, and
          ``url``.
        """
        d = {
            "title": self.title,
            "id": self.id,
            "abstract": self.abstract,
            "categories": self.cats,
            "doi": self.doi,
            "created": self.created,
            "updated": self.updated,
            "authors": self.authors,
            "affiliation": self.affiliation,
            "url": self.url,
        }
        return d


class Scraper(object):
    """Scrapes arXiv records for a category and date range.

    If ``date_from`` is not provided, the first day of the current month is
    used. If ``date_until`` is not provided, the current day is used.

    Args:
      category: ArXiv set/category (e.g., ``cs.LG`` or ``stat``).
      date_from: Start date in ``YYYY-MM-DD``. Updated e-prints are included even
        if originally created outside the range. Defaults to first day of the
        current month.
      date_until: End date in ``YYYY-MM-DD``. Updated e-prints are included even
        if originally created outside the range. Defaults to today.
      t: Waiting time in seconds between retries when the API responds with
        HTTP 503. Defaults to 30.
      timeout: Maximum scraping time in seconds before stopping. Defaults to 300.
      filters: Optional filters to limit saved results. Keys may include
        ``subcats``, ``author``, ``title``, or ``abstract``; values are lists of
        case-insensitive substrings to match.

    Examples:
      Returning all e-prints from ``stat`` category:

          import arxivscraper.arxivscraper as ax
          scraper = ax.Scraper(
              category='stat', date_from='2017-12-23', date_until='2017-12-25', t=10,
              filters={'affiliation': ['facebook'], 'abstract': ['learning']},
          )
          output = scraper.scrape()
    """

    def __init__(
        self,
        category: str,
        date_from: Optional[str] = None,
        date_until: Optional[str] = None,
        t: int = 30,
        timeout: int = 300,
        filters: Optional[Dict[str, List[str]]] = None,
    ) -> None:
        self.cat = str(category)
        self.t = t
        self.timeout = timeout
        DateToday = datetime.date.today()
        if date_from is None:
            self.f = str(DateToday.replace(day=1))
        else:
            self.f = date_from
        if date_until is None:
            self.u = str(DateToday)
        else:
            self.u = date_until
        self.url = (
            BASE
            + "from="
            + self.f
            + "&until="
            + self.u
            + "&metadataPrefix=arXiv&set=%s" % self.cat
        )
        self.filters = filters or {}
        if not self.filters:
            self.append_all = True
        else:
            self.append_all = False
            self.keys = self.filters.keys()

    def scrape(self) -> List[Dict[str, Union[str, List[str]]]]:
        """Fetches arXiv records for the configured query.

        Returns:
          A list of record dictionaries as produced by ``Record.output``.

        Raises:
          HTTPError: Re-raises non-503 HTTP errors encountered during fetching.
        """
        logging.info("Starting to scrape arXiv...")
        t0 = time.time()
        tx = time.time()
        elapsed = 0.0
        url = self.url
        ds = []
        k = 1
        while True:
            try:
                logging.info("Fetching up to %d records...", 1000 * k)
                logging.info(url)
                response = urlopen(url)
            except HTTPError as e:
                if e.code == 503:
                    self.t = int(e.hdrs.get("retry-after", 30)) + 1
                    logging.info(e.headers)
                    logging.info(
                        "Got 503. Retrying after {0:d} seconds.".format(self.t)
                    )
                    time.sleep(self.t)
                    continue
                else:
                    logging.info("Unknown error")
                    raise
            k += 1
            xml = response.read()
            root = ET.fromstring(xml)
            records = root.findall(OAI + "ListRecords/" + OAI + "record")
            for record in records:
                meta = record.find(OAI + "metadata").find(ARXIV + "arXiv")
                record = Record(meta).output()
                if self.append_all:
                    ds.append(record)
                else:
                    save_record = False
                    for key in self.keys:
                        for word in self.filters[key]:
                            if word.lower() in record[key]:
                                save_record = True

                    if save_record:
                        ds.append(record)

            try:
                token = root.find(OAI + "ListRecords").find(OAI + "resumptionToken")
            except:
                return 1
            if token is None or token.text is None:
                break
            else:
                url = BASE + "resumptionToken=%s" % token.text

            ty = time.time()
            elapsed += ty - tx
            if elapsed >= self.timeout:
                break
            else:
                tx = time.time()

        t1 = time.time()
        logging.info("fetching is completed in {0:.1f} seconds.".format(t1 - t0))
        logging.info("Total number of records {:d}".format(len(ds)))
        return ds
