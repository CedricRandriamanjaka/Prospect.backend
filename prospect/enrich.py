import re
import time
from urllib.parse import urljoin, urlparse

import requests

# --- Optionnel: validation très fiable des numéros au format international (+...)
# pip install phonenumbers
try:
    import phonenumbers
    HAS_PHONENUMBERS = True
except Exception:
    HAS_PHONENUMBERS = False


# -------------------------
# Regex: Emails
# -------------------------
EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
OBF_EMAIL_RE = re.compile(
    r"([a-zA-Z0-9._%+-]+)\s*(?:@|\(at\)|\[at\]| at )\s*([a-zA-Z0-9.-]+)\s*(?:\.|\(dot\)|\[dot\]| dot )\s*([a-zA-Z]{2,})",
    re.IGNORECASE,
)
MAILTO_RE = re.compile(r"mailto:([^\"\'\?\s>]+)", re.IGNORECASE)


# -------------------------
# Regex: Phones
# -------------------------
# Fallback global (sur texte visible)
PHONE_RE = re.compile(r"(?<!\d)(?:\+?\d[\d\s().-]{7,}\d)(?!\d)")

# tel: liens (le plus fiable)
TEL_LINK_RE = re.compile(r"tel:([+0-9][0-9\s().-]{5,})", re.IGNORECASE)

# Extraction "dans un contexte téléphone"
PHONE_CTX_RE = re.compile(
    r"(?:\b(?:tel|tél|téléphone|telephone|phone|mobile|call|hotline|whatsapp|support)\b\s*[:：]?\s*)"
    r"(\+?\d[\d\s().-]{7,}\d)",
    re.IGNORECASE,
)

# Contexte non-latin (ZH/JA/KO) courant
PHONE_CTX_RE2 = re.compile(
    r"(?:电话|電話|联系我们|聯絡|聯絡我們|客服|客户服务|문의|고객센터|연락처|お問い合わせ|お問合せ)\s*[:：]?\s*(\+?\d[\d\s().-]{7,}\d)",
    re.IGNORECASE,
)


# -------------------------
# WhatsApp
# -------------------------
WHATSAPP_RE = re.compile(
    r"(https?://(?:wa\.me/|api\.whatsapp\.com/|web\.whatsapp\.com/)[^\s\"\'<>]+)",
    re.IGNORECASE
)


# -------------------------
# Contact discovery (multilingue)
# -------------------------
CONTACT_KEYWORDS = [
    # EN / FR
    "contact", "contact-us", "contacts", "contactez", "contactez-nous",
    "nous-contacter", "support", "help", "customer-service",
    "about", "about-us", "a-propos", "apropos", "company",
    "legal", "impressum", "mentions-legales", "privacy", "terms",

    # ES / PT / IT
    "contacto", "contato", "contatti", "assistenza", "chi-siamo", "acerca", "sobre",

    # DE / NL
    "kontakt", "kundenservice", "hilfe", "over-ons", "klantenservice",

    # RU / UA
    "контакты", "контакт", "поддержка", "о-нас",

    # AR
    "اتصل", "اتصل-بنا", "تواصل", "الدعم", "من-نحن",

    # ZH
    "联系", "联系我们", "聯絡", "聯絡我們", "客服", "客户服务", "關於", "关于我们",

    # JA
    "お問い合わせ", "お問合せ", "会社概要", "サポート",

    # KO
    "문의", "고객센터", "연락처", "회사소개",
]

CONTACT_PATH_GUESSES = [
    "/contact", "/contact-us", "/contacts", "/support", "/help",
    "/a-propos", "/about", "/about-us",
    "/mentions-legales", "/legal", "/impressum",
    "/privacy", "/terms",

    # ZH common
    "/联系", "/联系我们", "/聯絡", "/聯絡我們",
    # JA / KO (rare)
    "/お問い合わせ", "/문의",
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
        flags=re.IGNORECASE
    )
    html = re.sub(
        r"<style\b[^<]*(?:(?!<\/style>)<[^<]*)*<\/style>",
        " ",
        html,
        flags=re.IGNORECASE
    )
    return html


def _html_to_visible_text(html: str) -> str:
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
# HTTP fetch
# -------------------------
def _fetch_html(session: requests.Session, url: str, timeout: int = 15) -> str:
    headers = {
        "User-Agent": "prospect-com/0.1 (+contact: randriamanjakacedric@gmail.com)",
        "Accept": "text/html,application/xhtml+xml",
    }
    try:
        r = session.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        if r.status_code >= 400:
            return ""
        return r.text or ""
    except Exception:
        return ""


# -------------------------
# Extractors: emails
# -------------------------
def _extract_emails(html: str) -> list[str]:
    if not html:
        return []

    html = _strip_scripts_and_styles(html)
    emails = set()

    for m in MAILTO_RE.findall(html):
        e = (m or "").strip()
        if e:
            emails.add(e)

    for e in EMAIL_RE.findall(html):
        emails.add(e)

    for user, domain, tld in OBF_EMAIL_RE.findall(html):
        emails.add(f"{user}@{domain}.{tld}".replace(" ", ""))

    out = []
    for e in emails:
        e2 = e.strip().strip(".;,")
        if e2 and e2 not in out:
            out.append(e2)
    return out


# -------------------------
# Phones: stratégie "fiable sans région"
# -> On extrait des candidats, puis on garde UNIQUEMENT les numéros internationaux:
#    +XXXXXXXX ou 00XXXXXXXX (converti en +)
# -> Optionnel: validation avec phonenumbers (sans région si +...).
# -------------------------
def _is_plausible_candidate_phone(raw: str) -> bool:
    """
    Filtre anti faux positifs AVANT normalisation.
    Ici on ne valide pas le pays (pas possible sans + / région),
    on retire surtout les timestamps/coords.
    """
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
    """
    Garde uniquement:
    - +XXXXXXXX
    - 00XXXXXXXX -> +XXXXXXXX
    Puis nettoie et valide longueur (E.164: 9..15 digits après +).
    Si phonenumbers est installé: validation réelle.
    """
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

        # Nettoyage minimal: + et chiffres uniquement
        cleaned = "+" + re.sub(r"\D", "", s[1:])
        digits = cleaned[1:]

        # Taille plausible E.164
        if len(digits) < 9 or len(digits) > 15:
            continue

        # Validation réelle si possible (sans région si +...)
        if HAS_PHONENUMBERS:
            try:
                num = phonenumbers.parse(cleaned, None)  # région non nécessaire car +...
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
        flags=re.IGNORECASE | re.DOTALL
    )

    candidates = []

    for href, text in anchors:
        h = (href or "").strip()
        if not h or h.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue

        text_clean = re.sub(r"<[^>]+>", " ", text or "")
        text_clean = re.sub(r"\s+", " ", text_clean).strip().lower()
        href_lower = h.lower()

        if any(k.lower() in href_lower for k in CONTACT_KEYWORDS) or any(k.lower() in text_clean for k in CONTACT_KEYWORDS):
            full = urljoin(base_url, h)
            if _same_domain(base_url, full):
                candidates.append(full)

    out = []
    for u in candidates:
        if u not in out:
            out.append(u)

    return out[:limit]


# -------------------------
# Public API
# -------------------------
def enrich_contacts_from_website(
    website: str,
    session: requests.Session | None = None,
    max_pages: int = 3,
    timeout: int = 15,
    delay_seconds: float = 0.7,
) -> dict:
    """
    Scraping light:
    - page d'accueil
    - + pages contact (si trouvées)
    Retourne: emails, telephones, whatsapp, visited_urls
    """
    website = _normalize_url(website)
    if not website:
        return {"emails": [], "telephones": [], "whatsapp": [], "visited_urls": []}

    s = session or requests.Session()
    visited: list[str] = []
    emails: list[str] = []
    phones: list[str] = []
    whatsapp: list[str] = []

    def merge_unique(target: list[str], items: list[str]):
        for it in items:
            if it and it not in target:
                target.append(it)

    # 1) homepage
    html = _fetch_html(s, website, timeout=timeout)
    visited.append(website)
    merge_unique(emails, _extract_emails(html))
    merge_unique(phones, _extract_phones(html))
    merge_unique(whatsapp, _extract_whatsapp(html))

    # 2) pages "contact"
    contact_urls = _find_contact_urls(website, html, limit=max_pages - 1)

    # fallback: chemins connus
    if not contact_urls:
        for path in CONTACT_PATH_GUESSES:
            contact_urls.append(urljoin(website, path))
            if len(contact_urls) >= (max_pages - 1):
                break

    for u in contact_urls:
        time.sleep(delay_seconds)
        html2 = _fetch_html(s, u, timeout=timeout)
        visited.append(u)
        merge_unique(emails, _extract_emails(html2))
        merge_unique(phones, _extract_phones(html2))
        merge_unique(whatsapp, _extract_whatsapp(html2))

        # stop tôt si on a déjà trouvé email + tel
        if emails and phones:
            break

    # dédup final
    emails = list(dict.fromkeys(emails))
    phones = list(dict.fromkeys(phones))
    whatsapp = list(dict.fromkeys(whatsapp))

    return {
        "emails": emails,
        "telephones": phones,   # <-- uniquement +... (ou 00... converti)
        "whatsapp": whatsapp,
        "visited_urls": visited,
    }


def enrich_prospects(
    prospects: list[dict],
    max_enrich: int = 10,
    delay_seconds: float = 0.7,
    timeout: int = 15,
) -> list[dict]:
    """
    Enrichit seulement une partie des prospects pour éviter les timeouts.
    """
    s = requests.Session()
    enriched = 0

    for p in prospects:
        if enriched >= max_enrich:
            break

        site = p.get("site")
        if not site:
            continue

        # enrichir si manque email/tel
        if (p.get("emails") or []) and (p.get("telephones") or []):
            continue

        time.sleep(delay_seconds)
        extra = enrich_contacts_from_website(
            site,
            session=s,
            max_pages=3,
            timeout=timeout,
            delay_seconds=delay_seconds,
        )

        # merge
        p["emails"] = list(dict.fromkeys((p.get("emails") or []) + (extra.get("emails") or [])))
        merged_phones = (p.get("telephones") or []) + (extra.get("telephones") or [])
        p["telephones"] = keep_only_international_phones(merged_phones)
        p["whatsapp"] = list(dict.fromkeys((p.get("whatsapp") or []) + (extra.get("whatsapp") or [])))
        p["scraped_urls"] = extra.get("visited_urls", [])

        enriched += 1

    return prospects
