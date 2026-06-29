"""
app.py — Main Flask Application for Fake Internship Detector
============================================================
Provides page routing and REST API endpoints for the ML analyzer,
message scanner, company legitimacy check, URL scanner, and dashboard.
"""

import os
import re
import sqlite3
import nltk
from flask import Flask, render_template, request, jsonify, g
import joblib
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

# Import business logic helpers
import utils

# Add local bundled NLTK data to path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
nltk_data_dir = os.path.join(BASE_DIR, 'nltk_data')
nltk.data.path.append(nltk_data_dir)

app = Flask(__name__)
app.secret_key = os.urandom(24)

DATABASE = '/tmp/database.db'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, 'model')
MODEL_PATH = os.path.join(MODEL_DIR, 'internship_model.pkl')
TFIDF_PATH = os.path.join(MODEL_DIR, 'tfidf.pkl')

# Global variables for ML model and vectorizer
model = None
tfidf = None
stop_words = set(stopwords.words("english"))

def load_ml_model():
    """Load the trained ML model and TF-IDF vectorizer from disk."""
    global model, tfidf
    if os.path.exists(MODEL_PATH) and os.path.exists(TFIDF_PATH):
        try:
            model = joblib.load(MODEL_PATH)
            tfidf = joblib.load(TFIDF_PATH)
            print("Successfully loaded ML model and TF-IDF vectorizer.")
        except Exception as e:
            print(f"Error loading ML model/TF-IDF: {e}")
    else:
        print("ML model files not found. Run train_model.py first.")

# Load models at startup
load_ml_model()

# ─────────────────────────────────────────────────────────────
#  DATABASE INITIALIZATION
# ─────────────────────────────────────────────────────────────

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    """Create SQLite tables if they do not exist."""
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        
        # 1. Checks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT,
                internship_title TEXT,
                stipend REAL,
                description_snippet TEXT,
                result TEXT,
                confidence REAL,
                scam_score REAL,
                date_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 2. Company checks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS company_checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT,
                trust_score REAL,
                website_exists BOOLEAN,
                linkedin_exists BOOLEAN,
                date_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 3. URL scans table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS url_scans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT,
                is_ssl BOOLEAN,
                is_suspicious BOOLEAN,
                verdict TEXT,
                date_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 4. Message scans table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS message_scans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT,
                message_snippet TEXT,
                result TEXT,
                confidence REAL,
                scam_score REAL,
                scam_indicators_found TEXT,
                date_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        db.commit()

init_db()

# ─────────────────────────────────────────────────────────────
#  NLP PREPROCESSING HELPERS
# ─────────────────────────────────────────────────────────────

def preprocess_text(text: str) -> str:
    """Preprocess text identically to train_model.py."""
    if not text:
        return ""
    text = text.lower()
    # Remove special characters, keep only letters and spaces
    text = re.sub(r"[^a-zA-Z\s]", " ", text)
    # Tokenize
    tokens = word_tokenize(text)
    # Remove stopwords and very short tokens
    tokens = [t for t in tokens if t not in stop_words and len(t) > 2]
    return " ".join(tokens)

def get_ml_prediction(title: str, description: str, requirements: str, contact_method: str, stipend: str):
    """Run model prediction on job details."""
    global model, tfidf
    if model is None or tfidf is None:
        # Reload attempt
        load_ml_model()
        if model is None or tfidf is None:
            return 0.5, 0.5  # Fallback to neutral probability

    combined_text = f"{title} {description} {requirements} {contact_method} {stipend}"
    clean_text = preprocess_text(combined_text)
    
    # Vectorize
    vector = tfidf.transform([clean_text])
    probabilities = model.predict_proba(vector)[0]
    # Class index 0 is Genuine, 1 is Fake
    real_prob = float(probabilities[0])
    fake_prob = float(probabilities[1])
    return real_prob, fake_prob

# ─────────────────────────────────────────────────────────────
#  PAGE ROUTES
# ─────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyzer')
def analyzer():
    return render_template('analyzer.html')

@app.route('/message-scanner')
def message_scanner():
    return render_template('message.html')

@app.route('/company-check')
def company_check():
    return render_template('company.html')

@app.route('/url-scanner')
def url_scanner():
    return render_template('scanner.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/about')
def about():
    return render_template('about.html')

# ─────────────────────────────────────────────────────────────
#  API ENDPOINTS
# ─────────────────────────────────────────────────────────────

@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    data = request.get_json() or {}
    description = data.get('description', '').strip()
    company_name = data.get('company_name', '').strip()
    stipend_raw = data.get('stipend', '')
    
    if not description:
        return jsonify({'error': 'Description text is required.'}), 400

    # Stipend parsing
    stipend_val = 0.0
    try:
        if stipend_raw:
            stipend_val = float(stipend_raw)
    except ValueError:
        pass

    # 1. Run ML Prediction
    real_prob, fake_prob = get_ml_prediction(
        title="", 
        description=description, 
        requirements="", 
        contact_method="", 
        stipend=str(stipend_raw)
    )

    # 2. Heuristics & Keywords
    keyword_matches = utils.detect_suspicious_keywords(description)
    stipend_analysis = utils.check_stipend_realism(stipend_val)
    
    # Calculate keyword-based risk score (0-100)
    keyword_score = sum(utils.SEVERITY_WEIGHTS.get(kw['severity'], 0) for kw in keyword_matches)
    keyword_score = min(keyword_score, 100.0)

    # Company checks contribution
    company_score = None
    if company_name:
        company_res = utils.check_company_legitimacy(company_name)
        # Convert trust score (0-100) to risk score (100 - trust score)
        company_score = 100.0 - company_res['trust_score']

    # 3. Calculate Composite Scam Score
    scam_score = utils.calculate_scam_score(
        ml_score=fake_prob,
        keyword_score=keyword_score / 100.0,
        stipend_score=stipend_analysis['risk_score'] / 100.0,
        company_score=company_score / 100.0 if company_score is not None else None
    )

    # 4. Highlighted Text for UI
    highlighted_html = utils.highlight_text(description, keyword_matches)

    # 5. Determine Final Verdict
    if scam_score >= 70:
        verdict = 'Fake / Scam'
        confidence = fake_prob * 100 if fake_prob > 0.5 else scam_score
    elif scam_score >= 40:
        verdict = 'Suspicious'
        confidence = scam_score
    else:
        verdict = 'Genuine'
        confidence = real_prob * 100 if real_prob > 0.5 else (100 - scam_score)

    confidence = round(min(confidence, 100.0), 2)

    # Save to database
    try:
        db = get_db()
        cursor = db.cursor()
        snippet = description[:100] + ('...' if len(description) > 100 else '')
        cursor.execute('''
            INSERT INTO checks (company_name, internship_title, stipend, description_snippet, result, confidence, scam_score)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (company_name or 'N/A', 'Internship Position', stipend_val, snippet, verdict, confidence, scam_score))
        db.commit()
    except Exception as e:
        print(f"Database insertion failed (checks): {e}")

    return jsonify({
        'result': verdict,
        'fake_probability': round(fake_prob * 100, 2),
        'real_probability': round(real_prob * 100, 2),
        'scam_score': scam_score,
        'suspicious_keywords': keyword_matches,
        'stipend_analysis': stipend_analysis,
        'highlighted_text': highlighted_html
    })

@app.route('/api/scan-message', methods=['POST'])
def api_scan_message():
    data = request.get_json() or {}
    message = data.get('message', '').strip()
    platform = data.get('platform', 'whatsapp').strip().lower()
    
    if not message:
        return jsonify({'error': 'Message text is required.'}), 400
        
    # SECURITY FIX: Prevent ReDoS and memory exhaustion by capping payload size
    if len(message) > 10000:
        return jsonify({'error': 'Payload too large. Message exceeds 10,000 character limit.'}), 413


    # 1. Base Message Scan (Heuristics)
    scan_res = utils.scan_message(message, platform)
    
    # 2. Inject ML Prediction
    real_prob, fake_prob = get_ml_prediction(
        title="", 
        description=message, 
        requirements="", 
        contact_method="", 
        stipend=""
    )
    
    # Recalculate with ML prediction included (weight ML as 35% as per plan)
    # Extract url risk
    urls = utils.extract_urls_from_text(message)
    url_risk = 0.0
    for u in urls[:5]:
        ur_res = utils.scan_url_safety(u)
        if not ur_res['is_safe']:
            url_risk = max(url_risk, 0.7)

    # Keywords contribution
    keyword_matches = scan_res['keyword_matches']
    keyword_risk = sum(utils.SEVERITY_WEIGHTS.get(kw['severity'], 0) for kw in keyword_matches)
    keyword_risk = min(keyword_risk / 100.0, 1.0)

    # Platform pattern risk
    platform_indicators = utils.detect_platform_patterns(message, platform)
    platform_risk = min(len(platform_indicators) * 0.15, 1.0)

    # Stipend mentions risk
    stipend_risk = 0.0
    # Search for money representations e.g., ₹50,000, Rs. 80000, 50k etc.
    if re.search(r'(?:₹|rs\.?|inr)\s?\d+[\d,]*|(?:\d+k)', message, re.IGNORECASE):
        stipend_risk = 0.3 # default suspicious stipend risk if mentioned in messages

    if urls:
        composite = (fake_prob * 0.35) + (keyword_risk * 0.25) + (platform_risk * 0.15) + (url_risk * 0.20) + (stipend_risk * 0.05)
    else:
        # Redistribute URL risk weight
        composite = (fake_prob * 0.45) + (keyword_risk * 0.30) + (platform_risk * 0.20) + (stipend_risk * 0.05)

    scam_score = round(composite * 100, 2)

    # Verdict mapping
    if scam_score >= 70:
        verdict = '🚨 SCAM'
        confidence = round(min(fake_prob * 100 if fake_prob > 0.5 else scam_score + 5, 100), 2)
    elif scam_score >= 40:
        verdict = '⚠️ SUSPICIOUS'
        confidence = scam_score
    else:
        verdict = '✅ LIKELY GENUINE'
        confidence = round(min(real_prob * 100 if real_prob > 0.5 else (100 - scam_score), 100), 2)

    # Generate highlighted HTML for message scanning
    highlighted_message = utils.highlight_text(message, keyword_matches)

    # Save to database
    try:
        db = get_db()
        cursor = db.cursor()
        snippet = message[:100] + ('...' if len(message) > 100 else '')
        indicators_str = ', '.join([ind['detail'] for ind in scan_res['indicators']])
        cursor.execute('''
            INSERT INTO message_scans (platform, message_snippet, result, confidence, scam_score, scam_indicators_found)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (platform, snippet, verdict, confidence, scam_score, indicators_str))
        db.commit()
    except Exception as e:
        print(f"Database insertion failed (message_scans): {e}")

    return jsonify({
        'verdict': verdict,
        'confidence': confidence,
        'scam_score': scam_score,
        'platform_detected': platform,
        'indicators': scan_res['indicators'],
        'highlighted_message': highlighted_message,
        'safety_tips': scan_res['safety_tips'],
        'ml_prediction': {
            'fake_probability': round(fake_prob * 100, 2),
            'real_probability': round(real_prob * 100, 2)
        }
    })


@app.route('/api/deep-scan-message', methods=['POST'])
def api_deep_scan_message():
    """
    Deep scan endpoint — visits linked websites, checks LinkedIn/company presence,
    extracts job description from the webpage, and combines all signals.
    """
    data = request.get_json() or {}
    message = data.get('message', '').strip()
    platform = data.get('platform', 'whatsapp').strip().lower()

    if not message:
        return jsonify({'error': 'Message text is required.'}), 400

    # SECURITY FIX: Prevent ReDoS and memory exhaustion by capping payload size
    if len(message) > 10000:
        return jsonify({'error': 'Payload too large. Message exceeds 10,000 character limit.'}), 413

    # Run deep scan orchestrator
    deep_result = utils.deep_scan_message(message, platform)

    # Inject ML prediction on the message itself
    real_prob, fake_prob = get_ml_prediction(
        title="",
        description=message,
        requirements="",
        contact_method="",
        stipend=""
    )

    # Also run ML on each scraped website's text if available
    for site in deep_result.get('website_results', []):
        if site.get('load_success') and site.get('full_text'):
            s_real, s_fake = get_ml_prediction(
                title=site.get('title', ''),
                description=site.get('full_text', ''),
                requirements='',
                contact_method='',
                stipend=site.get('extracted_stipend', '')
            )
            site['ml_fake_prob'] = round(s_fake * 100, 2)
            site['ml_real_prob'] = round(s_real * 100, 2)

    # Save to database
    try:
        db = get_db()
        cursor = db.cursor()
        snippet = message[:100] + ('...' if len(message) > 100 else '')
        indicators = deep_result.get('base_scan', {}).get('indicators', [])
        indicators_str = ', '.join([ind['detail'] for ind in indicators[:5]])
        cursor.execute('''
            INSERT INTO message_scans (platform, message_snippet, result, confidence, scam_score, scam_indicators_found)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            platform, snippet,
            deep_result['deep_verdict'],
            deep_result['deep_scam_score'],
            deep_result['deep_scam_score'],
            'DEEP SCAN: ' + indicators_str
        ))
        db.commit()
    except Exception as e:
        print(f"Database insertion failed (deep_scan): {e}")

    # Serialize website_results — strip full_text to keep response lean
    lean_sites = []
    for s in deep_result.get('website_results', []):
        lean_sites.append({
            'url': s.get('url', ''),
            'load_success': s.get('load_success', False),
            'title': s.get('title', ''),
            'meta_description': s.get('meta_description', ''),
            'text_snippet': s.get('text_snippet', ''),
            'extracted_stipend': s.get('extracted_stipend', ''),
            'word_count': s.get('word_count', 0),
            'keyword_hits': s.get('keyword_hits', []),
            'site_keyword_score': s.get('site_keyword_score', 0),
            'site_verdict': s.get('site_verdict', 'warn'),
            'ml_fake_prob': s.get('ml_fake_prob', None),
            'ml_real_prob': s.get('ml_real_prob', None),
            'error': s.get('error', ''),
        })

    base = deep_result.get('base_scan', {})
    highlighted_message = utils.highlight_text(message, base.get('keyword_matches', []))

    return jsonify({
        'deep_verdict': deep_result['deep_verdict'],
        'deep_scam_score': deep_result['deep_scam_score'],
        'base_verdict': base.get('verdict', ''),
        'base_scam_score': base.get('scam_score', 0),
        'indicators': base.get('indicators', []),
        'safety_tips': base.get('safety_tips', []),
        'highlighted_message': highlighted_message,
        'ml_prediction': {
            'fake_probability': round(fake_prob * 100, 2),
            'real_probability': round(real_prob * 100, 2)
        },
        'website_results': lean_sites,
        'linkedin_check': deep_result.get('linkedin_check', {}),
    })


@app.route('/api/check-company', methods=['POST'])
def api_check_company():
    data = request.get_json() or {}
    company_name = data.get('company_name', '').strip()
    
    if not company_name:
        return jsonify({'error': 'Company name is required.'}), 400

    res = utils.check_company_legitimacy(company_name)
    
    # Save to database
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            INSERT INTO company_checks (company_name, trust_score, website_exists, linkedin_exists)
            VALUES (?, ?, ?, ?)
        ''', (company_name, res['trust_score'], res['website_exists'], res['linkedin_exists']))
        db.commit()
    except Exception as e:
        print(f"Database insertion failed (company_checks): {e}")

    return jsonify({
        'company_name': company_name,
        'trust_score': res['trust_score'],
        'website_exists': res['website_exists'],
        'linkedin_exists': res['linkedin_exists'],
        'verdict': res['verdict'],
        'details': res['details']
    })

@app.route('/api/scan-url', methods=['POST'])
def api_scan_url():
    data = request.get_json() or {}
    url = data.get('url', '').strip()
    
    if not url:
        return jsonify({'error': 'URL is required.'}), 400

    res = utils.scan_url_safety(url)
    
    # Save to database
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            INSERT INTO url_scans (url, is_ssl, is_suspicious, verdict)
            VALUES (?, ?, ?, ?)
        ''', (url, res['is_ssl'], res['is_suspicious'], res['verdict']))
        db.commit()
    except Exception as e:
        print(f"Database insertion failed (url_scans): {e}")

    return jsonify({
        'url': url,
        'is_ssl': res['is_ssl'],
        'is_suspicious': res['is_suspicious'],
        'verdict': res['verdict'] == 'Safe' and 'Safe Website' or 'Suspicious Website',
        'risk_factors': res['risk_factors'],
        'details': res['details']
    })

@app.route('/api/dashboard-data', methods=['GET'])
def api_dashboard_data():
    db = get_db()
    cursor = db.cursor()
    
    # Total scans count
    cursor.execute('SELECT COUNT(*) FROM checks')
    total_checks = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM message_scans')
    total_messages = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM company_checks')
    total_companies = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM url_scans')
    total_urls = cursor.fetchone()[0]

    grand_total = total_checks + total_messages + total_companies + total_urls

    # Scams detected
    cursor.execute("SELECT COUNT(*) FROM checks WHERE result = 'Fake / Scam' OR result = 'Suspicious'")
    scams_checks = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM message_scans WHERE result LIKE '%SCAM%' OR result LIKE '%Suspicious%'")
    scams_messages = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM url_scans WHERE verdict = 'Suspicious Website' OR verdict = 'Suspicious'")
    scams_urls = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM company_checks WHERE trust_score < 40")
    scams_companies = cursor.fetchone()[0]

    total_scams = scams_checks + scams_messages + scams_urls + scams_companies
    scam_percentage = round((total_scams / (grand_total if grand_total > 0 else 1)) * 100, 2)

    # Average scam score
    cursor.execute('SELECT AVG(scam_score) FROM checks')
    avg_score_checks = cursor.fetchone()[0] or 0
    

    # Platform stats — query ALL distinct platforms actually stored in DB
    # This ensures Email, Internshala, LinkedIn etc. are properly reflected
    ALL_PLATFORMS = [
        'whatsapp', 'telegram', 'instagram', 'sms',
        'email', 'internshala', 'linkedin', 'other'
    ]
    # Friendly display labels for the dashboard chart
    PLATFORM_LABELS = {
        'whatsapp':   'WhatsApp',
        'telegram':   'Telegram',
        'instagram':  'Instagram',
        'sms':        'SMS',
        'email':      'Email',
        'internshala':'Internshala',
        'linkedin':   'LinkedIn',
        'other':      'Other',
    }

    platform_stats = {}
    # First, include counts for all known platforms
    for plat in ALL_PLATFORMS:
        cursor.execute("SELECT COUNT(*) FROM message_scans WHERE platform = ?", (plat,))
        count = cursor.fetchone()[0]
        if count > 0:
            label = PLATFORM_LABELS.get(plat, plat.capitalize())
            platform_stats[label] = count

    # Also catch any unrecognised platform values stored in the DB
    cursor.execute(
        "SELECT platform, COUNT(*) as cnt FROM message_scans "
        "WHERE platform NOT IN ({}) GROUP BY platform".format(
            ','.join('?' * len(ALL_PLATFORMS))
        ),
        ALL_PLATFORMS
    )
    for row in cursor.fetchall():
        if row['platform'] and row['cnt'] > 0:
            label = row['platform'].capitalize()
            platform_stats[label] = platform_stats.get(label, 0) + row['cnt']

    # If no messages scanned yet, show zeros for key platforms
    if not platform_stats:
        platform_stats = {
            'WhatsApp': 0, 'Telegram': 0, 'Instagram': 0,
            'SMS': 0, 'Email': 0, 'Internshala': 0, 'LinkedIn': 0, 'Other': 0
        }



    # Sample trend data (past 10 entries)
    cursor.execute("SELECT date_checked, scam_score FROM checks ORDER BY id DESC LIMIT 10")
    recent_trend = cursor.fetchall()
    trend_data = {
        'labels': [row['date_checked'][:10] for row in reversed(recent_trend)],
        'scores': [row['scam_score'] for row in reversed(recent_trend)]
    }

    # Compute keyword stats dynamically from recent checks
    cursor.execute("SELECT description_snippet FROM checks ORDER BY id DESC LIMIT 50")
    recent_descs = [row['description_snippet'] or '' for row in cursor.fetchall()]
    keyword_stats = {
        'Registration Fee': sum(1 for d in recent_descs if 'fee' in d.lower() or 'pay' in d.lower()),
        'Guaranteed Job': sum(1 for d in recent_descs if 'guaranteed' in d.lower()),
        'No Interview': sum(1 for d in recent_descs if 'interview' in d.lower()),
        'Urgent Joining': sum(1 for d in recent_descs if 'urgent' in d.lower()),
        'Security Deposit': sum(1 for d in recent_descs if 'deposit' in d.lower())
    }
    if sum(keyword_stats.values()) == 0:
        keyword_stats = {
            'Registration Fee': 12,
            'Guaranteed Job': 8,
            'No Interview': 15,
            'Urgent Joining': 10,
            'Security Deposit': 5
        }

    return jsonify({
        'total_checks': grand_total,
        'scams_detected': total_scams,
        'genuine_detected': grand_total - total_scams,
        'scam_percentage': scam_percentage,
        'avg_scam_score': round(avg_score_checks, 2),
        'platform_stats': platform_stats,
        'trend_data': trend_data,
        'keyword_stats': keyword_stats
    })

@app.route('/api/recent-checks', methods=['GET'])
def api_recent_checks():
    db = get_db()
    cursor = db.cursor()
    
    # Fetch from checks
    cursor.execute('''
        SELECT 'Internship' as type, company_name as source, result, IFNULL(confidence, 0) as confidence, IFNULL(scam_score, 0) as score, date_checked 
        FROM checks 
        ORDER BY id DESC LIMIT 10
    ''')
    checks = [dict(row) for row in cursor.fetchall()]

    # Fetch from message scans
    cursor.execute('''
        SELECT 'Message' as type, platform as source, result, IFNULL(confidence, 0) as confidence, IFNULL(scam_score, 0) as score, date_checked 
        FROM message_scans 
        ORDER BY id DESC LIMIT 10
    ''')
    messages = [dict(row) for row in cursor.fetchall()]

    # Fetch from company checks
    cursor.execute('''
        SELECT 'Company' as type, company_name as source, 
               CASE WHEN trust_score < 40 THEN 'Fake / Scam' WHEN trust_score < 70 THEN 'Suspicious' ELSE 'Genuine' END as result,
               100 as confidence, 
               (100 - trust_score) as score, 
               date_checked 
        FROM company_checks 
        ORDER BY id DESC LIMIT 10
    ''')
    companies = [dict(row) for row in cursor.fetchall()]

    # Fetch from url scans
    cursor.execute('''
        SELECT 'URL' as type, url as source, 
               verdict as result, 
               100 as confidence, 
               CASE WHEN verdict LIKE '%Suspicious%' THEN 100 ELSE 0 END as score, 
               date_checked 
        FROM url_scans 
        ORDER BY id DESC LIMIT 10
    ''')
    urls = [dict(row) for row in cursor.fetchall()]

    all_checks = checks + messages + companies + urls
    all_checks.sort(key=lambda x: x['date_checked'], reverse=True)

    return jsonify(all_checks[:20])

if __name__ == '__main__':
    app.run(port=5000, debug=True)
