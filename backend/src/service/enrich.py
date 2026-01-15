import re
import time
from urllib.parse import urljoin, urlparse
from typing import Tuple

import requests


EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
MAILTO_RE = re.compile(r"mailto:([^\"\'\?\s>]+)", re.IGNORECASE)
TEL_RE = re.compile(r"tel:([+0-9][0-9\s().-]{5,})", re.IGNORECASE)

CONTACT_WORDS = ["contact", "contact-us", "contacts", "support", "help", "a-propos", "about", "mentions-legales"]
CONTACT_PATH_GUESSES = ["/contact", "/contact-us", "/contacts", "/support", "/help", "/a-propos", "/about"]


def _normalize_url(url: str) -> str:
    u = (url or "").strip()
    if not u:
        return ""
    if not u.startswith(("http://", "https://")):
        u = "https://" + u
    return u


def _same_domain(a: str, b: str) -> bool:
    try:
        return urlparse(a).netloc.lower() == urlparse(b).netloc.lower()
    except Exception:
        return False


def _fetch(session: requests.Session, url: str, timeout: int) -> Tuple[str, dict]:
    headers = {
        "User-Agent": "prospecting/1.0 (contact: randriamanjakacedric@gmail.com)",
        "Accept": "text/html,application/xhtml+xml",
    }
    t0 = time.perf_counter()
    try:
        r = session.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        sec = time.perf_counter() - t0
        status = int(getattr(r, "status_code", 0) or 0)
        html = (r.text or "") if status and status < 400 else ""
        return html, {"url": url, "ok": bool(status and status < 400), "status": status, "seconds": round(sec, 3)}
    except Exception as e:
        sec = time.perf_counter() - t0
        return "", {"url": url, "ok": False, "status": 0, "seconds": round(sec, 3), "error": str(e)}


def _extract(html: str) -> dict:
    emails = []
    for m in MAILTO_RE.findall(html or ""):
        if m and m not in emails:
            emails.append(m.strip())

    for e in EMAIL_RE.findall(html or ""):
        if e and e not in emails:
            emails.append(e.strip())

    phones = []
    for m in TEL_RE.findall(html or ""):
        p = (m or "").strip()
        if p and p not in phones:
            phones.append(p)

    return {"emails": emails, "telephones": phones}


def _find_contact_urls(base: str, html: str, limit: int = 2) -> list[str]:
    if not html:
        return []
    anchors = re.findall(r'<a[^>]+href=["\']([^"\']+)["\']', html, flags=re.IGNORECASE)
    out = []
    for href in anchors:
        h = (href or "").strip()
        if not h or h.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue
        low = h.lower()
        if any(w in low for w in CONTACT_WORDS):
            full = urljoin(base, h)
            if _same_domain(base, full) and full not in out:
                out.append(full)
        if len(out) >= limit:
            break
    return out


def enrich_prospects(prospects: list[dict], return_meta: bool = False, timeout: int = 15, delay: float = 0.7):
    t0 = time.perf_counter()
    s = requests.Session()
    enriched = 0

    for p in prospects:
        p["enrich_attempted"] = False
        p["enrich_seconds"] = None
        p["enrich_error"] = None

        site = _normalize_url(p.get("site") or "")
        if not site:
            continue

        p["enrich_attempted"] = True
        t_item = time.perf_counter()

        try:
            html, info = _fetch(s, site, timeout=timeout)
            extracted = _extract(html)

            # pages contact
            urls = _find_contact_urls(site, html, limit=2)
            if not urls:
                for path in CONTACT_PATH_GUESSES:
                    urls.append(urljoin(site, path))
                    if len(urls) >= 2:
                        break

            for u in urls:
                time.sleep(delay)
                html2, _ = _fetch(s, u, timeout=timeout)
                ex2 = _extract(html2)
                extracted["emails"] += [x for x in ex2["emails"] if x not in extracted["emails"]]
                extracted["telephones"] += [x for x in ex2["telephones"] if x not in extracted["telephones"]]

            # merge dans prospect
            p["emails"] = list(dict.fromkeys((p.get("emails") or []) + extracted["emails"]))
            p["telephones"] = list(dict.fromkeys((p.get("telephones") or []) + extracted["telephones"]))

            enriched += 1

        except Exception as e:
            p["enrich_error"] = str(e)

        p["enrich_seconds"] = round(time.perf_counter() - t_item, 3)

    total = time.perf_counter() - t0
    meta = {
        "enabled": True,
        "enriched_count": enriched,
        "total_seconds": round(total, 3),
        "avg_seconds": round(total / enriched, 3) if enriched else 0.0,
    }
    return (prospects, meta) if return_meta else prospects
