"""
utils.py — Helper Functions for Fake Internship Detector
=========================================================

This module contains all the business logic for detecting fake/scam internships:
  • Suspicious keyword detection with severity levels
  • Stipend realism checking
  • Company legitimacy verification (website + LinkedIn)
  • URL safety scanning (SSL, domain patterns, TLD analysis)
  • Message scanning with platform-specific scam pattern detection
  • Composite scam score calculation
  • Text highlighting for UI display
  • Contextual safety tips generation
"""

import re
import urllib.parse
import socket
import statistics
import html
from urllib.parse import urlparse

import requests

# ─────────────────────────────────────────────────────────────
#  CONSTANTS
# ─────────────────────────────────────────────────────────────

# Scam keywords organized by severity level.
# 'high'   → strong indicators of financial fraud
# 'medium' → unrealistic promises & urgency tactics
# 'low'    → suspicious communication patterns
SCAM_KEYWORDS = {
    'high': [
        'registration fee', 'pay now', 'urgent payment', 'security deposit',
        'processing fee', 'refundable amount', 'immediate joining fee',
        'pay ₹', 'send money', 'bank transfer required'
    ],
    'medium': [
        'guaranteed job', 'no interview required', 'guaranteed placement',
        '100% placement', 'earn from home', 'work from mobile',
        'no experience needed', 'direct selection', 'spot offer',
        'limited seats', 'last date today', 'only 2 slots left'
    ],
    'low': [
        'whatsapp only', 'telegram only', 'dm for details',
        'share this message', 'forward to friends', 'join our channel',
        'respond within 24 hours'
    ]
}

# Severity weights used when calculating keyword-based risk score.
SEVERITY_WEIGHTS = {
    'high': 30,
    'medium': 15,
    'low': 5
}

# TLDs frequently associated with spam / throwaway domains.
SUSPICIOUS_TLDS = {
    '.xyz', '.tk', '.ml', '.ga', '.cf', '.gq', '.top', '.buzz',
    '.club', '.work', '.click', '.link', '.info', '.icu', '.rest'
}

# Well-known domains that scammers often misspell (typo-squatting).
KNOWN_DOMAINS = [
    'google.com', 'linkedin.com', 'indeed.com', 'internshala.com',
    'naukri.com', 'glassdoor.com', 'microsoft.com', 'amazon.com',
    'flipkart.com', 'tcs.com', 'infosys.com', 'wipro.com'
]

# Platform-specific scam indicators.
PLATFORM_PATTERNS = {
    'whatsapp': {
        'forwarded': [
            r'forwarded', r'forwarded many times', r'⏩', r'➡️'
        ],
        'chain_message': [
            r'share with \d+ (people|friends|groups)',
            r'forward (this|to)',
            r'send to \d+ contacts'
        ],
        'urgency': [
            r'last chance', r'expires (today|tonight|soon)',
            r'hurry', r'act now', r"don't miss"
        ]
    },
    'telegram': {
        'bot_formatting': [
            r'/start', r'/apply', r'/register', r'@\w+bot'
        ],
        'channel_links': [
            r't\.me/', r'telegram\.me/', r'join (our|the) channel'
        ],
        'broadcast': [
            r'broadcast', r'announcement', r'subscribe'
        ]
    },
    'instagram': {
        'dm_patterns': [
            r'dm (me|us|for)', r'send (a )?dm', r'inbox (me|us)',
            r'check (my|our) bio', r'link in bio'
        ],
        'profile_links': [
            r'@\w+', r'follow (me|us)'
        ]
    },
    'sms': {
        'short_links': [
            r'bit\.ly/', r'tinyurl\.com/', r'goo\.gl/',
            r'rb\.gy/', r'cutt\.ly/', r't\.co/'
        ],
        'urgency': [
            r'reply (yes|y|1)', r'call now', r'missed call',
            r'your OTP', r'verify now'
        ]
    }
}


# ─────────────────────────────────────────────────────────────
#  KEYWORD DETECTION
# ─────────────────────────────────────────────────────────────

def detect_suspicious_keywords(text: str) -> list:
    """
    Scan *text* for known scam keywords across all severity levels.

    Returns a list of dicts:
        [{ 'keyword': str, 'severity': str, 'position': int }, ...]
    where *position* is the character index of the first occurrence.
    """
    if not text:
        return []

    text_lower = text.lower()
    found = []

    for severity, keywords in SCAM_KEYWORDS.items():
        for kw in keywords:
            pos = text_lower.find(kw.lower())
            if pos != -1:
                found.append({
                    'keyword': kw,
                    'severity': severity,
                    'position': pos
                })

    # Sort by position so the caller can process matches in order.
    found.sort(key=lambda x: x['position'])
    return found


# ─────────────────────────────────────────────────────────────
#  STIPEND REALISM CHECK
# ─────────────────────────────────────────────────────────────

def check_stipend_realism(stipend_amount) -> dict:
    """
    Evaluate whether a stipend amount is realistic for an internship.

    Heuristics (monthly, INR):
        • 0           → unpaid, common but worth noting
        • 1 – 999     → suspiciously low
        • 1 000 – 50 000  → realistic range
        • 50 001 – 100 000 → unusually high
        • > 100 000   → almost certainly fake / bait

    Returns: { is_suspicious: bool, reason: str, risk_score: int (0-100) }
    """
    try:
        amount = float(stipend_amount)
    except (TypeError, ValueError):
        return {
            'is_suspicious': False,
            'reason': 'No stipend information provided.',
            'risk_score': 0
        }

    if amount == 0:
        return {
            'is_suspicious': False,
            'reason': 'Unpaid internship — common in many industries.',
            'risk_score': 10
        }
    elif 1 <= amount < 1000:
        return {
            'is_suspicious': True,
            'reason': f'Stipend of ₹{amount:,.0f}/month is suspiciously low and may indicate an exploitative offer.',
            'risk_score': 40
        }
    elif 1000 <= amount <= 50000:
        return {
            'is_suspicious': False,
            'reason': f'Stipend of ₹{amount:,.0f}/month is within the realistic range for internships.',
            'risk_score': 0
        }
    elif 50000 < amount <= 100000:
        return {
            'is_suspicious': True,
            'reason': f'Stipend of ₹{amount:,.0f}/month is unusually high for an internship. Verify the offer carefully.',
            'risk_score': 50
        }
    else:  # > 100 000
        return {
            'is_suspicious': True,
            'reason': f'Stipend of ₹{amount:,.0f}/month is unrealistically high and is a common scam tactic.',
            'risk_score': 85
        }


# ─────────────────────────────────────────────────────────────
#  SCAM SCORE CALCULATION
# ─────────────────────────────────────────────────────────────

def calculate_scam_score(
    ml_score: float,
    keyword_score: float,
    stipend_score: float,
    company_score: float = None,
    url_score: float = None
) -> float:
    """
    Compute a weighted composite scam score on a 0–100 scale.

    Weights (when all signals are available):
        ML model prediction : 40 %
        Keyword analysis    : 25 %
        Stipend realism     : 15 %
        Company legitimacy  : 10 %
        URL safety          : 10 %

    When optional scores are *None*, their weight is redistributed
    proportionally among the remaining signals.
    """
    components = {
        'ml':      (ml_score,      40),
        'keyword': (keyword_score, 25),
        'stipend': (stipend_score, 15),
    }

    if company_score is not None:
        components['company'] = (company_score, 10)
    if url_score is not None:
        components['url'] = (url_score, 10)

    # Redistribute weights so they sum to 100.
    total_weight = sum(w for _, w in components.values())
    if total_weight == 0:
        return 0.0

    score = sum((s * w) for s, w in components.values()) / total_weight * 100

    # Clamp to [0, 100].
    return round(max(0.0, min(100.0, score)), 2)


# ─────────────────────────────────────────────────────────────
#  COMPANY LEGITIMACY CHECK
# ─────────────────────────────────────────────────────────────

def check_company_legitimacy(company_name: str) -> dict:
    """
    Attempt to verify a company's legitimacy by probing for:
        1. A corporate website  (+30 points)
        2. A LinkedIn company page  (+30 points)
        3. Domain age via WHOIS  (+20 points, graceful fallback)
        4. Professional-sounding name  (+20 points)

    Returns:
        { trust_score: int, website_exists: bool,
          linkedin_exists: bool, details: str }
    """
    if not company_name or not company_name.strip():
        return {
            'trust_score': 0,
            'website_exists': False,
            'linkedin_exists': False,
            'details': 'No company name provided.'
        }

    trust_score = 0
    details = []
    slug = company_name.strip().lower().replace(' ', '')

    # --- 1. Website existence check (+30) ---
    website_exists = False
    for url_template in [f'https://www.{slug}.com', f'https://{slug}.com']:
        try:
            resp = requests.head(url_template, timeout=5, allow_redirects=True)
            if resp.status_code < 400:
                website_exists = True
                trust_score += 30
                details.append(f'Website found: {url_template}')
                break
        except requests.RequestException:
            continue

    if not website_exists:
        details.append('No corporate website detected.')

    # --- 2. LinkedIn company page check (+30) ---
    linkedin_exists = False
    linkedin_slug = company_name.strip().lower().replace(' ', '-')
    linkedin_url = f'https://www.linkedin.com/company/{linkedin_slug}'
    try:
        resp = requests.head(
            linkedin_url, timeout=5, allow_redirects=True,
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        if resp.status_code < 400:
            linkedin_exists = True
            trust_score += 30
            details.append(f'LinkedIn page found: {linkedin_url}')
    except requests.RequestException:
        pass

    if not linkedin_exists:
        details.append('No LinkedIn company page detected.')

    # --- 3. Domain age via WHOIS (+20, optional) ---
    domain_checked = False
    try:
        import whois  # python-whois — optional dependency
        domain = f'{slug}.com'
        w = whois.whois(domain)
        if w and w.creation_date:
            from datetime import datetime
            creation = w.creation_date
            # Some WHOIS records return a list.
            if isinstance(creation, list):
                creation = creation[0]
            if isinstance(creation, datetime):
                age_days = (datetime.now() - creation).days
                if age_days > 365:
                    trust_score += 20
                    details.append(f'Domain age: {age_days // 365} year(s) — established domain.')
                    domain_checked = True
                elif age_days > 90:
                    trust_score += 10
                    details.append(f'Domain age: {age_days} days — relatively new domain.')
                    domain_checked = True
                else:
                    details.append(f'Domain age: {age_days} days — very new, exercise caution.')
                    domain_checked = True
    except Exception:
        pass  # WHOIS not available — that's fine, we degrade gracefully.

    if not domain_checked:
        details.append('Domain age check unavailable (WHOIS lookup failed or library not installed).')

    # --- 4. Professional name heuristic (+20) ---
    name = company_name.strip()
    # A professional name typically has >= 2 chars, no excessive special chars,
    # and does not look like random gibberish.
    has_professional_name = (
        len(name) >= 2
        and not re.search(r'[!@#$%^&*()=+\[\]{}<>]', name)
        and not re.fullmatch(r'[a-z]{1,3}\d+', name, re.IGNORECASE)
        and not re.search(r'(.)\1{4,}', name)  # no char repeated 5+ times
    )
    if has_professional_name:
        trust_score += 20
        details.append('Company name appears professional.')
    else:
        details.append('Company name looks unprofessional or suspicious.')

    # --- Build verdict ---
    if trust_score >= 70:
        verdict = 'Likely Legitimate'
    elif trust_score >= 40:
        verdict = 'Partially Verified — proceed with caution'
    else:
        verdict = 'Unverified — high risk'

    return {
        'trust_score': trust_score,
        'website_exists': website_exists,
        'linkedin_exists': linkedin_exists,
        'verdict': verdict,
        'details': ' | '.join(details)
    }


# ─────────────────────────────────────────────────────────────
#  URL SAFETY SCANNING
# ─────────────────────────────────────────────────────────────

def scan_url_safety(url: str) -> dict:
    """
    Evaluate the safety of a URL by checking:
        • SSL / HTTPS usage
        • IP address in hostname
        • Suspicious TLD
        • Excessive subdomain depth
        • Very long URL
        • Typo-squatting of known domains
        • HTTP HEAD reachability

    Returns:
        { is_safe: bool, is_ssl: bool, details: str, risk_factors: list }
    """
    if not url:
        return {
            'is_safe': False,
            'is_ssl': False,
            'details': 'No URL provided.',
            'risk_factors': ['empty_url']
        }

    # Ensure the URL has a scheme so urlparse works correctly.
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url

    parsed = urlparse(url)
    risk_factors = []
    details = []

    # --- SSL check ---
    is_ssl = parsed.scheme == 'https'
    if not is_ssl:
        risk_factors.append('no_ssl')
        details.append('URL does not use HTTPS — data may be transmitted insecurely.')

    hostname = parsed.hostname or ''

    # --- IP address in URL ---
    if re.match(r'^\d{1,3}(\.\d{1,3}){3}$', hostname):
        risk_factors.append('ip_address')
        details.append('URL uses a raw IP address instead of a domain name.')

    # --- Suspicious TLD ---
    for tld in SUSPICIOUS_TLDS:
        if hostname.endswith(tld):
            risk_factors.append('suspicious_tld')
            details.append(f'Domain uses a suspicious TLD ({tld}).')
            break

    # --- Excessive subdomains (> 3 levels) ---
    subdomain_count = hostname.count('.')
    if subdomain_count > 3:
        risk_factors.append('excessive_subdomains')
        details.append(f'URL has {subdomain_count} subdomain levels — unusual for legitimate sites.')

    # --- Very long URL (> 200 chars) ---
    if len(url) > 200:
        risk_factors.append('very_long_url')
        details.append('URL is unusually long, which may indicate obfuscation.')

    # --- Typo-squatting check ---
    for known in KNOWN_DOMAINS:
        known_base = known.split('.')[0]
        # Check for close misspellings (edit distance ≤ 2) but not exact match.
        if known_base != hostname.split('.')[0] and _is_typosquat(hostname, known):
            risk_factors.append('possible_typosquat')
            details.append(f'Domain looks similar to {known} — possible typo-squatting.')
            break

    # --- Reachability check ---
    try:
        resp = requests.head(url, timeout=5, allow_redirects=True)
        if resp.status_code >= 400:
            risk_factors.append('unreachable')
            details.append(f'URL returned HTTP {resp.status_code}.')
    except requests.RequestException:
        risk_factors.append('unreachable')
        details.append('URL could not be reached — it may be offline or blocking automated requests.')

    is_safe = len(risk_factors) == 0

    if is_safe:
        details.append('No risk factors detected. URL appears safe.')

    return {
        'is_safe': is_safe,
        'is_ssl': is_ssl,
        'is_suspicious': not is_safe,
        'verdict': 'Safe' if is_safe else 'Suspicious',
        'details': ' | '.join(details) if details else 'Analysis complete.',
        'risk_factors': risk_factors
    }


def _is_typosquat(hostname: str, known_domain: str) -> bool:
    """
    Simple Levenshtein-distance check to see if *hostname* is a close
    misspelling of *known_domain* (distance ≤ 2).
    """
    a = hostname.lower().split('.')[0]
    b = known_domain.split('.')[0]
    if a == b:
        return False
    return _levenshtein(a, b) <= 2


def _levenshtein(s1: str, s2: str) -> int:
    """Compute the Levenshtein edit distance between two strings."""
    if len(s1) < len(s2):
        return _levenshtein(s2, s1)
    if len(s2) == 0:
        return len(s1)

    prev_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        curr_row = [i + 1]
        for j, c2 in enumerate(s2):
            # Insertions, deletions, substitutions.
            curr_row.append(min(
                prev_row[j + 1] + 1,
                curr_row[j] + 1,
                prev_row[j] + (0 if c1 == c2 else 1)
            ))
        prev_row = curr_row
    return prev_row[-1]


# ─────────────────────────────────────────────────────────────
#  MESSAGE SCANNING  (WhatsApp / Telegram / Instagram / SMS)
# ─────────────────────────────────────────────────────────────

def detect_platform_patterns(text: str, platform: str) -> list:
    """
    Detect platform-specific scam indicators in *text*.

    Returns a list of dicts:
        [{ 'pattern': str, 'category': str, 'matched_text': str }, ...]
    """
    if not text or not platform:
        return []

    text_lower = text.lower()
    platform_lower = platform.lower()
    indicators = []

    patterns = PLATFORM_PATTERNS.get(platform_lower, {})
    for category, regex_list in patterns.items():
        for pattern in regex_list:
            match = re.search(pattern, text_lower)
            if match:
                indicators.append({
                    'pattern': pattern,
                    'category': category,
                    'matched_text': match.group()
                })

    # --- Cross-platform checks ---
    # Excessive emojis (> 10 emoji characters).
    emoji_pattern = re.compile(
        r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF'
        r'\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF'
        r'\U00002702-\U000027B0\U0001F900-\U0001F9FF'
        r'\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF'
        r'\U00002600-\U000026FF]+', re.UNICODE
    )
    emojis = emoji_pattern.findall(text)
    total_emoji_chars = sum(len(e) for e in emojis)
    if total_emoji_chars > 10:
        indicators.append({
            'pattern': 'excessive_emojis',
            'category': 'formatting',
            'matched_text': f'{total_emoji_chars} emoji characters found'
        })

    # ALL CAPS sections (≥ 5 consecutive uppercase words).
    caps_match = re.search(r'(?:\b[A-Z]{2,}\b[\s]*){5,}', text)
    if caps_match:
        indicators.append({
            'pattern': 'all_caps_section',
            'category': 'formatting',
            'matched_text': caps_match.group().strip()[:80]
        })

    return indicators


def extract_urls_from_text(text: str) -> list:
    """
    Extract all URLs from *text* using a broad regex.

    Returns a list of URL strings.
    """
    if not text:
        return []

    url_regex = re.compile(
        r'https?://[^\s<>"\']+|'           # full URLs
        r'www\.[^\s<>"\']+|'                # www. links
        r'[a-zA-Z0-9.-]+\.[a-z]{2,}/\S*',  # bare domain/path
        re.IGNORECASE
    )
    return url_regex.findall(text)


def scan_message(text: str, platform: str) -> dict:
    """
    Comprehensive analysis of a message for scam indicators.

    Steps:
        1. Detect suspicious keywords (same as internship analysis)
        2. Detect platform-specific patterns
        3. Extract and scan any embedded URLs
        4. Combine all signals into a composite score

    Returns a detailed analysis dict suitable for the API response.
    """
    if not text:
        return {
            'verdict': 'No Content',
            'confidence': 0,
            'scam_score': 0,
            'platform_detected': platform or 'unknown',
            'indicators': [],
            'url_results': [],
            'safety_tips': [],
            'keyword_matches': []
        }

    # 1. Keyword detection.
    keyword_matches = detect_suspicious_keywords(text)

    # Calculate a keyword risk score (0–1).
    keyword_risk = 0.0
    for match in keyword_matches:
        keyword_risk += SEVERITY_WEIGHTS.get(match['severity'], 0)
    keyword_risk = min(keyword_risk / 100.0, 1.0)  # normalise to [0, 1]

    # 2. Platform-specific patterns.
    platform_indicators = detect_platform_patterns(text, platform or '')

    # Platform risk contribution (0–1).
    platform_risk = min(len(platform_indicators) * 0.12, 1.0)

    # 3. URL scanning.
    urls = extract_urls_from_text(text)
    url_results = []
    url_risk = 0.0
    for u in urls[:5]:  # limit to first 5 URLs to avoid slowness
        result = scan_url_safety(u)
        url_results.append(result)
        if not result['is_safe']:
            url_risk = max(url_risk, 0.7)

    # 4. Composite score.
    # Weights: keywords 40 %, platform patterns 30 %, URL safety 30 %.
    if urls:
        composite = keyword_risk * 0.40 + platform_risk * 0.30 + url_risk * 0.30
    else:
        # No URLs → redistribute URL weight to keywords and platform.
        composite = keyword_risk * 0.55 + platform_risk * 0.45

    scam_score = round(composite * 100, 2)

    # Determine verdict.
    if scam_score >= 70:
        verdict = 'Highly Suspicious — Likely Scam'
        confidence = min(scam_score + 5, 100)
    elif scam_score >= 40:
        verdict = 'Suspicious — Proceed with Caution'
        confidence = min(scam_score + 10, 100)
    elif scam_score >= 20:
        verdict = 'Mildly Suspicious'
        confidence = 60
    else:
        verdict = 'Appears Legitimate'
        confidence = max(80 - scam_score, 50)

    confidence = round(min(confidence, 100), 2)

    # Aggregate all indicators for the response.
    all_indicators = []
    for kw in keyword_matches:
        all_indicators.append({
            'type': 'keyword',
            'detail': f"Scam keyword detected: \"{kw['keyword']}\" (severity: {kw['severity']})"
        })
    for pi in platform_indicators:
        all_indicators.append({
            'type': 'platform_pattern',
            'detail': f"Platform pattern [{pi['category']}]: \"{pi['matched_text']}\""
        })
    for ur in url_results:
        if not ur['is_safe']:
            all_indicators.append({
                'type': 'url_risk',
                'detail': f"Suspicious URL detected — {', '.join(ur['risk_factors'])}"
            })

    safety_tips = get_safety_tips(all_indicators)

    return {
        'verdict': verdict,
        'confidence': confidence,
        'scam_score': scam_score,
        'platform_detected': platform or 'unknown',
        'indicators': all_indicators,
        'url_results': url_results,
        'safety_tips': safety_tips,
        'keyword_matches': keyword_matches
    }


# ─────────────────────────────────────────────────────────────
#  TEXT HIGHLIGHTING
# ─────────────────────────────────────────────────────────────

def highlight_text(text: str, indicators: list) -> str:
    """
    Return an HTML version of *text* with suspicious keywords wrapped
    in coloured <span> elements for front-end display.

    Colour mapping:
        high   → red
        medium → orange
        low    → yellow
    """
    if not text or not indicators:
        return text or ''

    COLOR_MAP = {
        'high':   '#ff4444',
        'medium': '#ff9800',
        'low':    '#ffeb3b'
    }

    # SECURITY FIX: Escape HTML to prevent Cross-Site Scripting (XSS)
    # If we don't do this, malicious inputs like <script>alert(1)</script> 
    # will be injected into the DOM via innerHTML on the frontend.
    safe_text = html.escape(text)
    highlighted = safe_text

    # Sort indicators by keyword length descending so longer phrases
    # are replaced first and don't get partially mangled.
    sorted_indicators = sorted(indicators, key=lambda x: -len(x.get('keyword', '')))

    for ind in sorted_indicators:
        kw = ind.get('keyword', '')
        severity = ind.get('severity', 'low')
        color = COLOR_MAP.get(severity, '#ffeb3b')

        # Case-insensitive replacement that preserves original casing.
        pattern = re.compile(re.escape(kw), re.IGNORECASE)
        highlighted = pattern.sub(
            lambda m: (
                f'<span style="background-color:{color};padding:2px 4px;'
                f'border-radius:3px;font-weight:bold;" '
                f'title="Suspicious ({severity} risk)">{m.group()}</span>'
            ),
            highlighted
        )

    return highlighted


# ─────────────────────────────────────────────────────────────
#  SAFETY TIPS
# ─────────────────────────────────────────────────────────────

def get_safety_tips(indicators: list) -> list:
    """
    Generate contextual safety advice based on the indicators found
    during analysis.  Returns a list of tip strings.
    """
    tips = []
    seen_types = set()

    for ind in indicators:
        detail = ind.get('detail', '').lower()
        ind_type = ind.get('type', '')

        # Avoid duplicate tip categories.
        if ind_type in seen_types:
            continue

        if 'fee' in detail or 'payment' in detail or 'pay' in detail:
            tips.append(
                '🚫 Legitimate internships NEVER ask for upfront fees. '
                'Do not pay any "registration", "processing", or "security" fee.'
            )
            seen_types.add(ind_type)

        elif 'guaranteed' in detail or 'placement' in detail:
            tips.append(
                '⚠️ No company can guarantee job placement. '
                'Be sceptical of promises that sound too good to be true.'
            )
            seen_types.add(ind_type)

        elif 'url' in ind_type or 'ssl' in detail:
            tips.append(
                '🔗 Always verify URLs before clicking. '
                'Check for HTTPS and make sure the domain matches the official company website.'
            )
            seen_types.add(ind_type)

        elif 'platform_pattern' in ind_type:
            tips.append(
                '📱 Be cautious of forwarded or broadcast messages offering internships. '
                'Verify the sender\'s identity independently.'
            )
            seen_types.add(ind_type)

        elif 'keyword' in ind_type:
            tips.append(
                '🔍 This message contains language commonly used in scams. '
                'Cross-check the internship details on the company\'s official website.'
            )
            seen_types.add(ind_type)

    # Always include these universal tips.
    universal_tips = [
        '✅ Verify the internship on the company\'s official careers page.',
        '📧 Use official email addresses (company domain) for communication, not personal Gmail/Yahoo.',
        '🏢 Research the company on LinkedIn, Glassdoor, and the MCA (Ministry of Corporate Affairs) website.',
    ]

    # Add universal tips that aren't redundant with what we already have.
    for tip in universal_tips:
        if tip not in tips:
            tips.append(tip)

    return tips


# ─────────────────────────────────────────────────────────────
#  DEEP SCAN — WEBSITE SCRAPING
# ─────────────────────────────────────────────────────────────

def scrape_website_job_content(url: str) -> dict:
    """
    Fetch and parse a URL to extract job/internship-related content.

    Uses BeautifulSoup to extract visible text, page title, meta description,
    and any stipend/salary figures mentioned on the page.

    Returns:
        {
          load_success: bool,
          title: str,
          meta_description: str,
          text_snippet: str,        # first 600 chars of cleaned body text
          full_text: str,           # full cleaned body text (for keyword scan)
          extracted_stipend: str,   # e.g. "₹15,000" if found, else ""
          word_count: int,
          keyword_hits: list,       # from detect_suspicious_keywords()
          error: str                # empty if success
        }
    """
    if not url:
        return {
            'load_success': False, 'title': '', 'meta_description': '',
            'text_snippet': '', 'full_text': '', 'extracted_stipend': '',
            'word_count': 0, 'keyword_hits': [], 'error': 'No URL provided'
        }

    # Ensure scheme
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    headers = {
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/120.0.0.0 Safari/537.36'
        ),
        'Accept-Language': 'en-US,en;q=0.9',
    }

    try:
        resp = requests.get(url, timeout=8, headers=headers, allow_redirects=True)
        resp.raise_for_status()
    except requests.RequestException as exc:
        return {
            'load_success': False, 'title': '', 'meta_description': '',
            'text_snippet': '', 'full_text': '', 'extracted_stipend': '',
            'word_count': 0, 'keyword_hits': [], 'error': str(exc)[:120]
        }

    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return {
            'load_success': False, 'title': '', 'meta_description': '',
            'text_snippet': '', 'full_text': '', 'extracted_stipend': '',
            'word_count': 0, 'keyword_hits': [], 'error': 'BeautifulSoup4 not installed'
        }

    soup = BeautifulSoup(resp.text, 'html.parser')

    # Page title
    title_tag = soup.find('title')
    page_title = title_tag.get_text(strip=True) if title_tag else ''

    # Meta description
    meta_desc = ''
    for meta in soup.find_all('meta'):
        if meta.get('name', '').lower() in ('description', 'og:description'):
            meta_desc = meta.get('content', '')
            break

    # Remove non-content tags
    for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'noscript', 'iframe']):
        tag.decompose()

    # Extract all visible text
    raw_text = soup.get_text(separator=' ', strip=True)
    # Collapse whitespace
    clean_text = re.sub(r'\s+', ' ', raw_text).strip()

    word_count = len(clean_text.split())
    text_snippet = clean_text[:600] + ('...' if len(clean_text) > 600 else '')

    # Extract stipend / salary figure
    stipend_match = re.search(
        r'(?:₹|rs\.?|inr|salary|stipend)[:\s]*(\d[\d,\.]+(?:\s?k|\s?lakh)?)',
        clean_text, re.IGNORECASE
    )
    extracted_stipend = stipend_match.group(0).strip() if stipend_match else ''

    # Run keyword detection on the page text
    keyword_hits = detect_suspicious_keywords(clean_text)

    return {
        'load_success': True,
        'title': page_title[:120],
        'meta_description': meta_desc[:200],
        'text_snippet': text_snippet,
        'full_text': clean_text[:3000],   # cap to avoid huge payloads
        'extracted_stipend': extracted_stipend,
        'word_count': word_count,
        'keyword_hits': keyword_hits,
        'error': ''
    }


# ─────────────────────────────────────────────────────────────
#  DEEP SCAN — LINKEDIN & COMPANY EXTRACTION
# ─────────────────────────────────────────────────────────────

def check_linkedin_from_message(text: str) -> dict:
    """
    Extract LinkedIn URLs and company name mentions from the message,
    then verify each company using check_company_legitimacy().

    Returns:
        {
          linkedin_urls_found: list[str],
          company_names_found: list[str],
          company_checks: list[dict],   # each item = check_company_legitimacy() result + name
        }
    """
    if not text:
        return {'linkedin_urls_found': [], 'company_names_found': [], 'company_checks': []}

    text_str = text if isinstance(text, str) else str(text)

    # 1. Extract explicit LinkedIn URLs
    li_url_pattern = re.compile(
        r'https?://(?:www\.)?linkedin\.com/(?:company|in|jobs)/[^\s<>"\']+',
        re.IGNORECASE
    )
    linkedin_urls = li_url_pattern.findall(text_str)

    # 2. Extract company names from common phrasing patterns
    company_patterns = [
        r'(?:at|from|by|join|hiring at|offered by|company[:\s]+)\s+([A-Z][A-Za-z0-9\s&\.\-]{2,40}?)(?:\s+is|\s+are|\s+will|\.|,|\n|$)',
        r'([A-Z][A-Za-z0-9]+(?:\s+[A-Z][A-Za-z0-9]+){0,3})\s+(?:pvt|ltd|llp|inc|corp|technologies|solutions|services|consultancy)',
        r'(?:company|employer|recruiter)[:\s]+([A-Za-z0-9\s&\.\-]{3,40}?)(?:\.|,|\n|$)',
    ]
    company_names = []
    for pattern in company_patterns:
        for match in re.finditer(pattern, text_str, re.IGNORECASE):
            name = match.group(1).strip()
            if 3 <= len(name) <= 60 and name not in company_names:
                company_names.append(name)

    # Also extract company from LinkedIn URLs
    for url in linkedin_urls:
        slug_match = re.search(r'linkedin\.com/company/([^/\s?]+)', url, re.IGNORECASE)
        if slug_match:
            slug = slug_match.group(1).replace('-', ' ').title()
            if slug not in company_names:
                company_names.append(slug)

    # 3. Verify each company (cap at 3 to stay fast)
    company_checks = []
    for name in company_names[:3]:
        result = check_company_legitimacy(name)
        result['company_name'] = name
        company_checks.append(result)

    return {
        'linkedin_urls_found': linkedin_urls[:5],
        'company_names_found': company_names[:5],
        'company_checks': company_checks
    }


# ─────────────────────────────────────────────────────────────
#  DEEP SCAN — ORCHESTRATOR
# ─────────────────────────────────────────────────────────────

def deep_scan_message(text: str, platform: str) -> dict:
    """
    Full deep-scan pipeline for a message:
      1. Base message scan (keywords, platform patterns)
      2. Extract URLs → scrape each URL for job content
      3. LinkedIn & company extraction from the message text
      4. Combine all signals into a unified deep_scam_score

    Returns an enriched result dict ready for the API response.
    """
    if not text:
        return {
            'base_scan': {},
            'website_results': [],
            'linkedin_check': {},
            'deep_scam_score': 0,
            'deep_verdict': 'No Content',
            'error': 'No message text provided'
        }

    # ── Step 1: Base message scan ──────────────────────────────
    base = scan_message(text, platform or 'other')

    # ── Step 2: URL scraping ──────────────────────────────────
    urls = extract_urls_from_text(text)
    website_results = []
    website_keyword_risk = 0.0

    for url in urls[:3]:   # max 3 URLs
        site_data = scrape_website_job_content(url)
        site_data['url'] = url

        # Compute site-level risk
        if site_data['load_success']:
            kw_risk = sum(
                SEVERITY_WEIGHTS.get(k['severity'], 0)
                for k in site_data['keyword_hits']
            )
            site_data['site_keyword_score'] = min(kw_risk, 100)
            website_keyword_risk = max(website_keyword_risk, kw_risk / 100.0)

            if site_data['site_keyword_score'] >= 60:
                site_data['site_verdict'] = 'danger'
            elif site_data['site_keyword_score'] >= 25:
                site_data['site_verdict'] = 'warn'
            else:
                site_data['site_verdict'] = 'safe'
        else:
            site_data['site_keyword_score'] = 0
            site_data['site_verdict'] = 'warn'   # unreachable = suspicious

        website_results.append(site_data)

    # ── Step 3: LinkedIn / company check ─────────────────────
    linkedin_check = check_linkedin_from_message(text)

    # Company trust signals → risk contribution
    company_risk = 0.0
    for cc in linkedin_check['company_checks']:
        trust = cc.get('trust_score', 50)
        risk = (100 - trust) / 100.0
        company_risk = max(company_risk, risk)

    # ── Step 4: Composite deep score ─────────────────────────
    base_score = base['scam_score'] / 100.0

    if website_results and any(r['load_success'] for r in website_results):
        deep_composite = (
            base_score          * 0.40 +
            website_keyword_risk * 0.35 +
            company_risk         * 0.25
        )
    elif linkedin_check['company_checks']:
        deep_composite = (
            base_score   * 0.55 +
            company_risk * 0.45
        )
    else:
        deep_composite = base_score

    deep_scam_score = round(min(deep_composite * 100, 100), 2)

    if deep_scam_score >= 70:
        deep_verdict = '🚨 HIGH RISK — Likely Scam'
    elif deep_scam_score >= 40:
        deep_verdict = '⚠️ SUSPICIOUS — Verify Carefully'
    else:
        deep_verdict = '✅ APPEARS LEGITIMATE'

    return {
        'base_scan': base,
        'website_results': website_results,
        'linkedin_check': linkedin_check,
        'deep_scam_score': deep_scam_score,
        'deep_verdict': deep_verdict,
        'error': ''
    }
