import re
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import urljoin, urlparse
from typing import Optional, Dict, Any

import requests

# Accès DB via SQL brut (psycopg3)
try:
    from ..db import fetch_one, execute, Json
    HAS_DB = True
except Exception:
    HAS_DB = False

# --- Optionnel: validation très fiable des numéros au format international (+...)
# pip install phonenumbers
try:
    import phonenumbers

    HAS_PHONENUMBERS = True
except Exception:
    HAS_PHONENUMBERS = False


# -------------------------
# Regex: Emails (ANTI faux emails .png/.jpg/.jpeg/.svg/.webp...)
# -------------------------
EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
OBF_EMAIL_RE = re.compile(
    r"([a-zA-Z0-9._%+-]+)\s*(?:@|\(at\)|\[at\]| at )\s*([a-zA-Z0-9.-]+)\s*(?:\.|\(dot\)|\[dot\]| dot )\s*([a-zA-Z]{2,})",
    re.IGNORECASE,
)
MAILTO_RE = re.compile(r"mailto:([^\"\'\?\s>]+)", re.IGNORECASE)

# TLDs à rejeter (faux positifs d'assets: logo@2x.png, icon@3x.jpg, etc.)
BAD_EMAIL_TLDS = {
    "png", "jpg", "jpeg", "gif", "svg", "webp", "ico", "bmp", "tif", "tiff",
    "css", "js", "pdf", "woff", "woff2", "ttf", "eot", "mp4", "mp3", "bet", "se", 
}


def _sanitize_email_candidate(e: str) -> str | None:
    """
    Nettoie + valide un email candidat.
    Rejette les faux positifs type logo@2x.png
    """
    if not e:
        return None

    s = (e or "").strip()
    if not s:
        return None

    # enlever query/fragment/path
    s = s.split("?", 1)[0].split("#", 1)[0].split("/", 1)[0]

    # enlever ponctuation autour
    s = s.strip().strip(" \t\r\n\"'<>[](){}.,;:")

    # normalisation légère
    s = s.replace(" ", "")
    if "@" not in s:
        return None

    try:
        local, domain = s.rsplit("@", 1)
    except ValueError:
        return None

    if not local or not domain:
        return None

    if "." not in domain:
        return None

    # tld
    tld = domain.rsplit(".", 1)[-1].lower()
    if tld in BAD_EMAIL_TLDS:
        return None

    # garde-fous basiques
    if ".." in s:
        return None
    if len(local) > 64 or len(domain) > 255:
        return None

    return s


# -------------------------
# Regex: Phones
# -------------------------
PHONE_RE = re.compile(r"(?<!\d)(?:\+?\d[\d\s().-]{7,}\d)(?!\d)")
TEL_LINK_RE = re.compile(r"tel:([+0-9][0-9\s().-]{5,})", re.IGNORECASE)

PHONE_CTX_RE = re.compile(
    r"(?:\b(?:tel|tél|téléphone|telephone|phone|mobile|call|hotline|whatsapp|support)\b\s*[:：]?\s*)"
    r"(\+?\d[\d\s().-]{7,}\d)",
    re.IGNORECASE,
)

PHONE_CTX_RE2 = re.compile(
    r"(?:电话|電話|联系我们|聯絡|聯絡我們|客服|客户服务|문의|고객센터|연락처|お問い合わせ|お問合せ)\s*[:：]?\s*(\+?\d[\d\s().-]{7,}\d)",
    re.IGNORECASE,
)


# -------------------------
# WhatsApp
# -------------------------
WHATSAPP_RE = re.compile(
    r"(https?://(?:wa\.me/|api\.whatsapp\.com/|web\.whatsapp\.com/)[^\s\"\'<>]+)",
    re.IGNORECASE,
)


# -------------------------
# Contact discovery (multilingue)
# -------------------------
CONTACT_KEYWORDS = [
    # EN / FR
    "contact",
    "contact-us",
    "contacts",
    "contactez",
    "contactez-nous",
    "nous-contacter",
    "support",
    "help",
    "customer-service",
    "about",
    "about-us",
    "a-propos",
    "apropos",
    "company",
    "legal",
    "impressum",
    "mentions-legales",
    "privacy",
    "terms",
    # ES / PT / IT
    "contacto",
    "contato",
    "contatti",
    "assistenza",
    "chi-siamo",
    "acerca",
    "sobre",
    # DE / NL
    "kontakt",
    "kundenservice",
    "hilfe",
    "over-ons",
    "klantenservice",
    # RU / UA
    "контакты",
    "контакт",
    "поддержка",
    "о-нас",
    # AR
    "اتصل",
    "اتصل-بنا",
    "تواصل",
    "الدعم",
    "من-نحن",
    # ZH
    "联系",
    "联系我们",
    "聯絡",
    "聯絡我們",
    "客服",
    "客户服务",
    "關於",
    "关于我们",
    # JA
    "お問い合わせ",
    "お問合せ",
    "会社概要",
    "サポート",
    # KO
    "문의",
    "고객센터",
    "연락처",
    "회사소개",
]

CONTACT_PATH_GUESSES = [
    "/contact",
    "/contact-us",
    "/contacts",
    "/support",
    "/help",
    "/a-propos",
    "/about",
    "/about-us",
    "/mentions-legales",
    "/legal",
    "/impressum",
    "/privacy",
    "/terms",
    # ZH
    "/联系",
    "/联系我们",
    "/聯絡",
    "/聯絡我們",
    # JA / KO (rare)
    "/お問い合わせ",
    "/문의",
]


# -------------------------
# HTML cleanup / normalization
# -------------------------
def _strip_scripts_and_styles(html: str) -> str:
    if not html:
        return ""
    html = re.sub(
        r"<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>",
        " ",
        html,
        flags=re.IGNORECASE,
    )
    html = re.sub(
        r"<style\b[^<]*(?:(?!<\/style>)<[^<]*)*<\/style>",
        " ",
        html,
        flags=re.IGNORECASE,
    )
    return html


def _html_to_visible_text(html: str) -> str:
    """
    Convertit HTML -> texte visible (sans tags/script/style).
    Important: réduit les faux emails dans src/href/assets.
    """
    if not html:
        return ""
    html = _strip_scripts_and_styles(html)
    html = re.sub(r"<!--.*?-->", " ", html, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _normalize_url(url: str) -> str:
    if not url:
        return ""
    url = url.strip()
    if not url:
        return ""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url


def _same_domain(a: str, b: str) -> bool:
    try:
        return urlparse(a).netloc.lower() == urlparse(b).netloc.lower()
    except Exception:
        return False


# -------------------------
# HTTP fetch (avec timing)
# -------------------------
def _fetch_html(session: requests.Session, url: str, timeout: int = 15) -> tuple[str, dict]:
    """
    Retourne (html, info):
      info = {
        url, ok, status_code, fetch_seconds, bytes, error
      }
    """
    headers = {
        "User-Agent": "prospect-com/0.1 (+contact: randriamanjakacedric@gmail.com)",
        "Accept": "text/html,application/xhtml+xml",
    }

    t0 = time.perf_counter()
    try:
        r = session.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        elapsed = time.perf_counter() - t0

        status = int(getattr(r, "status_code", 0) or 0)
        txt = r.text or "" if status < 400 else ""
        b = len(txt.encode("utf-8", errors="ignore")) if txt else 0

        return txt, {
            "url": url,
            "ok": bool(status and status < 400),
            "status_code": status,
            "fetch_seconds": round(elapsed, 3),
            "bytes": b,
            "error": None if status < 400 else f"HTTP {status}",
        }
    except Exception as e:
        elapsed = time.perf_counter() - t0
        return "", {
            "url": url,
            "ok": False,
            "status_code": 0,
            "fetch_seconds": round(elapsed, 3),
            "bytes": 0,
            "error": str(e),
        }


# -------------------------
# Extractors: emails
# -------------------------
def _extract_emails(html: str) -> list[str]:
    """
    Stratégie anti-faux-positifs:
    - mailto: dans HTML (fiable)
    - regex email dans le TEXTE VISIBLE seulement
    - obfuscation dans TEXTE VISIBLE seulement
    - filtre TLD images/assets
    """
    if not html:
        return []

    html_clean = _strip_scripts_and_styles(html)

    # 1) mailto: (fiable)
    emails: list[str] = []
    for m in MAILTO_RE.findall(html_clean):
        e = _sanitize_email_candidate(m)
        if e and e not in emails:
            emails.append(e)

    # 2) texte visible (évite src/href d'assets)
    text = _html_to_visible_text(html_clean)

    for e in EMAIL_RE.findall(text):
        e2 = _sanitize_email_candidate(e)
        if e2 and e2 not in emails:
            emails.append(e2)

    # 3) obfusqués (texte visible)
    for user, domain, tld in OBF_EMAIL_RE.findall(text):
        e = f"{user}@{domain}.{tld}".replace(" ", "")
        e2 = _sanitize_email_candidate(e)
        if e2 and e2 not in emails:
            emails.append(e2)

    return emails


# -------------------------
# Phones: stratégie "fiable sans région"
# -------------------------
def _is_plausible_candidate_phone(raw: str) -> bool:
    if not raw:
        return False
    s = (raw or "").strip()
    if not s:
        return False

    # coords type 48.8630243
    if re.search(r"\b\d{1,3}\.\d+\b", s):
        return False

    digits = re.sub(r"\D", "", s)

    # trop long => timestamp / ID
    if len(digits) > 18:
        return False

    # trop court
    if len(digits) < 7:
        return False

    return True


def keep_only_international_phones(candidates: list[str]) -> list[str]:
    out = []
    seen = set()

    for raw in candidates or []:
        s = (raw or "").strip()
        if not s:
            continue

        # Convertir 00... en +...
        if s.startswith("00"):
            s = "+" + s[2:].strip()

        # Garder uniquement ceux qui commencent par +
        if not s.startswith("+"):
            continue

        cleaned = "+" + re.sub(r"\D", "", s[1:])
        digits = cleaned[1:]

        # Taille plausible E.164
        if len(digits) < 9 or len(digits) > 15:
            continue

        # Validation réelle si possible (sans région si +...)
        if HAS_PHONENUMBERS:
            try:
                num = phonenumbers.parse(cleaned, None)
                if not phonenumbers.is_possible_number(num):
                    continue
                if not phonenumbers.is_valid_number(num):
                    continue
            except Exception:
                continue

        if cleaned not in seen:
            seen.add(cleaned)
            out.append(cleaned)

    return out


def _extract_phones(html: str) -> list[str]:
    if not html:
        return []

    html_clean = _strip_scripts_and_styles(html)
    if not html_clean:
        return []

    candidates: list[str] = []

    def add_candidate(p: str):
        p = re.sub(r"\s+", " ", (p or "").strip())
        if p and _is_plausible_candidate_phone(p):
            candidates.append(p)

    # 1) tel: (priorité)
    for m in TEL_LINK_RE.findall(html_clean):
        add_candidate(m)

    # 2) texte visible
    text = _html_to_visible_text(html_clean)

    # 2a) numéros en contexte tel/phone/电话/문의...
    for m in PHONE_CTX_RE.findall(text):
        add_candidate(m)
    for m in PHONE_CTX_RE2.findall(text):
        add_candidate(m)

    # 2b) fallback global (sur texte visible)
    for m in PHONE_RE.findall(text):
        add_candidate(m)

    # 3) Normalisation + filtrage strict (internationaux seulement)
    return keep_only_international_phones(candidates)


# -------------------------
# WhatsApp
# -------------------------
def _extract_whatsapp(html: str) -> list[str]:
    if not html:
        return []
    html = _strip_scripts_and_styles(html)
    return list(dict.fromkeys(WHATSAPP_RE.findall(html)))


# -------------------------
# Find contact URLs
# -------------------------
def _find_contact_urls(base_url: str, html: str, limit: int = 3) -> list[str]:
    if not html:
        return []

    anchors = re.findall(
        r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )

    candidates = []

    for href, text in anchors:
        h = (href or "").strip()
        if not h or h.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue

        text_clean = re.sub(r"<[^>]+>", " ", text or "")
        text_clean = re.sub(r"\s+", " ", text_clean).strip().lower()
        href_lower = h.lower()

        if any(k.lower() in href_lower for k in CONTACT_KEYWORDS) or any(
            k.lower() in text_clean for k in CONTACT_KEYWORDS
        ):
            full = urljoin(base_url, h)
            if _same_domain(base_url, full):
                candidates.append(full)

    out = []
    for u in candidates:
        if u not in out:
            out.append(u)

    return out[:limit]


# -------------------------
# Cache: fonctions de lecture/écriture
# -------------------------
def _get_cached_enrichment(website: str) -> Optional[Dict[str, Any]]:
    """
    Récupère les données d'enrichissement en cache si elles existent et sont récentes.
    - Si contacts présents : cache valide si < 30 jours
    - Si pas de contacts : cache valide si < 10 jours
    Retourne None si pas de cache ou si les données sont trop anciennes.
    """
    if not HAS_DB:
        return None
    
    website = _normalize_url(website)
    if not website:
        return None
    
    try:
        row = fetch_one(
            """
            SELECT
              emails,
              telephones,
              whatsapp,
              scraped_urls,
              is_empty,
              updated_at
            FROM openstreetmap_enrichi
            WHERE website = %s
            LIMIT 1;
            """,
            (website,),
        )
        if not row:
            return None

        emails = row.get("emails") or []
        telephones = row.get("telephones") or []
        whatsapp = row.get("whatsapp") or []
        visited_urls = row.get("scraped_urls") or []

        max_age_days = 10 if bool(row.get("is_empty")) else 30
        updated_at = row.get("updated_at")
        if not updated_at:
            return None

        now = datetime.now(timezone.utc) if getattr(updated_at, "tzinfo", None) else datetime.now()
        age = now - updated_at
        if age.days >= max_age_days:
            return None

        return {
            "emails": emails,
            "telephones": telephones,
            "whatsapp": whatsapp,
            "visited_urls": visited_urls,
            "from_cache": True,
        }
    except Exception:
        # En cas d'erreur DB, on continue sans cache
        return None


def _save_enrichment_to_cache(
    website: str,
    emails: list[str],
    telephones: list[str],
    whatsapp: list[str],
    scraped_urls: list[str],
) -> None:
    """
    Enregistre les données d'enrichissement dans le cache.
    Calcule automatiquement is_empty selon la présence de contacts.
    """
    if not HAS_DB:
        return
    
    website = _normalize_url(website)
    if not website:
        return
    
    # Calculer is_empty : True si aucun contact trouvé
    is_empty = not bool(emails or telephones or whatsapp)
    
    try:
        execute(
            """
            INSERT INTO openstreetmap_enrichi
              (website, emails, telephones, whatsapp, scraped_urls, is_empty, updated_at)
            VALUES
              (%s, %s, %s, %s, %s, %s, now())
            ON CONFLICT (website)
            DO UPDATE SET
              emails = EXCLUDED.emails,
              telephones = EXCLUDED.telephones,
              whatsapp = EXCLUDED.whatsapp,
              scraped_urls = EXCLUDED.scraped_urls,
              is_empty = EXCLUDED.is_empty,
              updated_at = now();
            """,
            (
                website,
                Json(emails or []),
                Json(telephones or []),
                Json(whatsapp or []),
                Json(scraped_urls or []),
                bool(is_empty),
            ),
        )
    except Exception:
        # En cas d'erreur DB, on continue sans sauvegarder
        pass


# -------------------------
# Public API: enrichissement d'un site + détails timing
# -------------------------
def enrich_contacts_from_website(
    website: str,
    session: requests.Session | None = None,
    max_pages: int = 3,
    timeout: int = 15,
    delay_seconds: float = 0.7,
) -> dict:
    """
    Retourne:
      - emails, telephones, whatsapp, visited_urls
      - timing: détails par page (fetch + extract) + sleep + discovery
    """
    t0_total = time.perf_counter()

    website = _normalize_url(website)
    if not website:
        return {
            "emails": [],
            "telephones": [],
            "whatsapp": [],
            "visited_urls": [],
            "timing": {
                "total_seconds": 0.0,
                "sleep_seconds": 0.0,
                "find_contact_urls_seconds": 0.0,
                "pages": [],
            },
        }

    s = session or requests.Session()

    visited: list[str] = []
    emails: list[str] = []
    phones: list[str] = []
    whatsapp: list[str] = []

    timing_pages: list[dict] = []
    sleep_seconds_total = 0.0

    def merge_unique(target: list[str], items: list[str]):
        for it in items:
            if it and it not in target:
                target.append(it)

    def extract_all(html: str) -> tuple[list[str], list[str], list[str], float]:
        t_ex0 = time.perf_counter()
        e = _extract_emails(html)
        p = _extract_phones(html)
        w = _extract_whatsapp(html)
        ex_sec = time.perf_counter() - t_ex0
        return e, p, w, ex_sec

    # 1) homepage
    html, info = _fetch_html(s, website, timeout=timeout)
    visited.append(website)

    e, p, w, ex_sec = extract_all(html)
    merge_unique(emails, e)
    merge_unique(phones, p)
    merge_unique(whatsapp, w)

    timing_pages.append(
        {
            "url": website,
            "fetch_seconds": info["fetch_seconds"],
            "status_code": info["status_code"],
            "ok": info["ok"],
            "bytes": info["bytes"],
            "extract_seconds": round(ex_sec, 3),
            "emails_found": len(e),
            "phones_found": len(p),
            "whatsapp_found": len(w),
            "error": info["error"],
        }
    )

    # 2) pages "contact"
    t_find0 = time.perf_counter()
    contact_urls = _find_contact_urls(website, html, limit=max_pages - 1)
    find_contact_urls_seconds = time.perf_counter() - t_find0

    # fallback: chemins connus
    if not contact_urls:
        for path in CONTACT_PATH_GUESSES:
            contact_urls.append(urljoin(website, path))
            if len(contact_urls) >= (max_pages - 1):
                break

    for u in contact_urls:
        t_sleep0 = time.perf_counter()
        time.sleep(delay_seconds)
        sleep_seconds_total += time.perf_counter() - t_sleep0

        html2, info2 = _fetch_html(s, u, timeout=timeout)
        visited.append(u)

        e2, p2, w2, ex2_sec = extract_all(html2)
        merge_unique(emails, e2)
        merge_unique(phones, p2)
        merge_unique(whatsapp, w2)

        timing_pages.append(
            {
                "url": u,
                "fetch_seconds": info2["fetch_seconds"],
                "status_code": info2["status_code"],
                "ok": info2["ok"],
                "bytes": info2["bytes"],
                "extract_seconds": round(ex2_sec, 3),
                "emails_found": len(e2),
                "phones_found": len(p2),
                "whatsapp_found": len(w2),
                "error": info2["error"],
            }
        )

        # stop tôt si on a déjà trouvé email + tel
        if emails and phones:
            break

    # dédup final
    emails = list(dict.fromkeys(emails))
    phones = list(dict.fromkeys(phones))
    whatsapp = list(dict.fromkeys(whatsapp))

    total_seconds = time.perf_counter() - t0_total

    return {
        "emails": emails,
        "telephones": phones,  # uniquement +... (ou 00... converti)
        "whatsapp": whatsapp,
        "visited_urls": visited,
        "timing": {
            "total_seconds": round(total_seconds, 3),
            "sleep_seconds": round(sleep_seconds_total, 3),
            "find_contact_urls_seconds": round(find_contact_urls_seconds, 3),
            "pages": timing_pages,
        },
    }


# -------------------------
# Public API: enrichissement de prospects + timings détaillés par item
# -------------------------
def enrich_prospects(
    prospects: list[dict],
    max_enrich: int = 10,
    delay_seconds: float = 0.7,
    timeout: int = 15,
    return_meta: bool = False,
    mode: str = "missing",  # missing|always|never
) -> list[dict] | tuple[list[dict], dict]:
    """
    Ajouts:
      - dans chaque item:
        enrich_attempted (bool)
        enrich_seconds (float|None)
        enrich_error (str|None)
        enrich_details (dict)  <-- détails timing + pages
      - meta global
    """
    t_total0 = time.perf_counter()

    s = requests.Session()
    enriched = 0

    for p in prospects:
        p.setdefault("enrich_attempted", False)
        p.setdefault("enrich_seconds", None)
        p.setdefault("enrich_error", None)
        p.setdefault("enrich_details", None)

    mode = (mode or "missing").lower().strip()

    if mode == "never" or max_enrich <= 0:
        meta = {
            "mode": mode,
            "enriched_count": 0,
            "total_seconds": 0.0,
            "avg_seconds": 0.0,
            "max_enrich": max_enrich,
        }
        return (prospects, meta) if return_meta else prospects

    for p in prospects:
        if enriched >= max_enrich:
            break

        site = p.get("site")
        if not site:
            continue

        # mode=missing => skip si déjà email + phone
        if mode == "missing" and (p.get("emails") or []) and (p.get("telephones") or []):
            continue

        p["enrich_attempted"] = True
        t_item0 = time.perf_counter()

        before_emails = set(p.get("emails") or [])
        before_phones = set(p.get("telephones") or [])
        before_whatsapp = set(p.get("whatsapp") or [])

        details = None

        try:
            # Vérifier le cache d'abord
            cached_data = _get_cached_enrichment(site)
            
            if cached_data:
                # Utiliser les données du cache
                extra = {
                    "emails": cached_data.get("emails", []),
                    "telephones": cached_data.get("telephones", []),
                    "whatsapp": cached_data.get("whatsapp", []),
                    "visited_urls": cached_data.get("visited_urls", []),
                    "timing": {
                        "total_seconds": 0.0,
                        "sleep_seconds": 0.0,
                        "find_contact_urls_seconds": 0.0,
                        "pages": [],
                    },
                }
                details = extra.get("timing") or {}
            else:
                # Scraper le site
                extra = enrich_contacts_from_website(
                    site,
                    session=s,
                    max_pages=3,
                    timeout=timeout,
                    delay_seconds=delay_seconds,
                )

                details = extra.get("timing") or {}

                # Sauvegarder dans le cache (même si pas de contacts trouvés)
                _save_enrichment_to_cache(
                    website=site,
                    emails=extra.get("emails", []),
                    telephones=extra.get("telephones", []),
                    whatsapp=extra.get("whatsapp", []),
                    scraped_urls=extra.get("visited_urls", []),
                )

            # merge
            p["emails"] = list(dict.fromkeys((p.get("emails") or []) + (extra.get("emails") or [])))
            merged_phones = (p.get("telephones") or []) + (extra.get("telephones") or [])
            p["telephones"] = keep_only_international_phones(merged_phones)
            p["whatsapp"] = list(dict.fromkeys((p.get("whatsapp") or []) + (extra.get("whatsapp") or [])))
            p["scraped_urls"] = extra.get("visited_urls", [])

        except Exception as e:
            p["enrich_error"] = str(e)

        elapsed = time.perf_counter() - t_item0
        p["enrich_seconds"] = round(elapsed, 3)

        # enrich_details dans le résultat (par item)
        after_emails = set(p.get("emails") or [])
        after_phones = set(p.get("telephones") or [])
        after_whatsapp = set(p.get("whatsapp") or [])

        p["enrich_details"] = {
            "total_seconds": p["enrich_seconds"],
            "sleep_seconds": float((details or {}).get("sleep_seconds") or 0.0),
            "find_contact_urls_seconds": float((details or {}).get("find_contact_urls_seconds") or 0.0),
            "pages": (details or {}).get("pages") or [],
            "added": {
                "emails": len(after_emails - before_emails),
                "telephones": len(after_phones - before_phones),
                "whatsapp": len(after_whatsapp - before_whatsapp),
            },
        }

        enriched += 1

    total_elapsed = time.perf_counter() - t_total0
    meta = {
        "mode": mode,
        "enriched_count": enriched,
        "total_seconds": round(total_elapsed, 3),
        "avg_seconds": round((total_elapsed / enriched), 3) if enriched > 0 else 0.0,
        "max_enrich": max_enrich,
    }

    if return_meta:
        return prospects, meta
    return prospects
