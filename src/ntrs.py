"""NASA NTRS (Technical Reports Server) search.

Public-domain, authoritative US-government technical reports, including many failure-analysis
and fractography studies. Free and legal to search and cite (unlike paywalled ASM/ASTM text).
Standard library only, no API key.
"""

import urllib.request
import urllib.parse
import json

NTRS = "https://ntrs.nasa.gov/api/citations/search"
UA = "AgenticMatter-FailureAgent/1.0 (mailto:khanibtisam38@gmail.com)"


def search_ntrs(query, max_results=6):
    """Return a list of NASA technical reports (title, year, abstract, url) for a query."""
    params = urllib.parse.urlencode({"q": query})
    req = urllib.request.Request(f"{NTRS}?{params}", headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        payload = json.loads(r.read().decode("utf-8", "replace"))

    results = payload.get("results", []) or []
    out = []
    for it in results[:max_results]:
        nid = it.get("id")
        title = (it.get("title") or "").strip()
        abstract = " ".join((it.get("abstract") or "").split())
        # NTRS ids encode the original year as the first 4 digits (e.g. 19790012016 -> 1979).
        sid = str(nid or "")
        if sid[:2] in ("19", "20"):
            year = sid[:4]
        else:
            year = str(it.get("distributionDate") or it.get("created") or "")[:4]
        if title:
            out.append({"id": nid, "title": title, "year": year, "abstract": abstract,
                        "url": f"https://ntrs.nasa.gov/citations/{nid}" if nid else ""})
    return out
