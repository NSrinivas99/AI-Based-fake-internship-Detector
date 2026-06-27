# 🛡️ Fake Internship Detector

> AI-Powered Protection Against Internship & Job Scams

An intelligent full-stack web application that helps students and job seekers verify whether an internship or job posting is genuine or a scam. It uses **Machine Learning**, **Natural Language Processing**, **Web Scraping**, and **Pattern Analysis** to detect fraudulent offers.

---

## 🌟 Features

### 1. 🔍 Internship Scam Detection (ML-Powered)
- Paste any internship/job description for instant analysis
- Trained on 1,000+ real and fake internship postings
- NLP preprocessing with TF-IDF vectorization
- Logistic Regression & Random Forest classifiers
- Returns fake/real probability with confidence percentage

### 2. 💬 WhatsApp/Telegram Message Scanner
- Scan copied messages from WhatsApp, Telegram, Instagram DMs, or SMS
- Platform-specific scam pattern detection
- Identifies forwarded message indicators, bot formatting, chain messages
- Highlights suspicious phrases, URLs, and payment references
- Provides contextual safety tips

### 3. 🔑 Suspicious Keyword Detection
- Detects dangerous phrases: "registration fee", "guaranteed job", "no interview required", etc.
- Categorized by severity (high/medium/low risk)
- Highlights suspicious keywords directly in the text

### 4. 🏢 Company Legitimacy Checker
- Verifies if the company has an official website
- Checks for LinkedIn company page
- Domain age analysis
- Trust score out of 100

### 5. 🌐 Website URL Scanner
- SSL certificate verification
- Suspicious domain pattern detection
- TLD risk analysis
- Domain resolution check

### 6. 📊 Scam Score Calculator
- Composite risk score combining all signals
- Weighted scoring: ML prediction, keywords, company trust, URL safety, stipend realism
- Clear verdict: SCAM / SUSPICIOUS / LIKELY GENUINE

### 7. 📈 Analytics Dashboard
- Total checks, scams detected, success rate
- Interactive charts (Chart.js): trends, distribution, keywords, platform breakdown
- Recent checks history

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.10+, Flask |
| **Frontend** | HTML5, CSS3, JavaScript (Vanilla) |
| **ML/NLP** | scikit-learn, NLTK, TF-IDF |
| **Web Scraping** | BeautifulSoup4, Requests |
| **Database** | SQLite |
| **Data Processing** | Pandas, NumPy |
| **Charts** | Chart.js |
| **Domain Analysis** | python-whois |

---

## 📁 Project Structure

```
fake_internship_detector/
│
├── app.py                    # Flask application (routes + API)
├── utils.py                  # Helper functions & business logic
├── train_model.py            # ML model training script
├── generate_dataset.py       # Dataset generation script
├── requirements.txt          # Python dependencies
├── README.md                 # Project documentation
├── .gitignore                # Git ignore rules
│
├── model/
│   ├── internship_model.pkl  # Trained ML model
│   └── tfidf.pkl             # TF-IDF vectorizer
│
├── dataset/
│   └── internship_dataset.csv  # Training dataset (1000 entries)
│
├── templates/
│   ├── base.html             # Base template (layout + navigation)
│   ├── index.html            # Home page
│   ├── analyzer.html         # Internship analyzer
│   ├── message.html          # WhatsApp/Telegram message scanner
│   ├── company.html          # Company verification
│   ├── scanner.html          # URL scanner
│   ├── dashboard.html        # Analytics dashboard
│   └── about.html            # About project
│
├── static/
│   ├── style.css             # Cybersecurity-themed dark UI
│   └── script.js             # Client-side JavaScript
│
└── database.db               # SQLite database (auto-created)
```

---

## 🚀 Setup Instructions

### Prerequisites
- Python 3.10 or higher
- pip (Python package manager)
- Git (optional)

### Step 1: Clone the Repository
```bash
git clone https://github.com/yourusername/fake-internship-detector.git
cd fake-internship-detector
```

### Step 2: Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Download NLTK Data
```bash
python -c "import nltk; nltk.download('stopwords'); nltk.download('punkt')"
```

### Step 5: Generate Dataset (if not present)
```bash
python generate_dataset.py
```

### Step 6: Train the ML Model
```bash
python train_model.py
```
This will create `model/internship_model.pkl` and `model/tfidf.pkl`.

### Step 7: Run the Application
```bash
python app.py
```

### Step 8: Open in Browser
Navigate to: **http://localhost:5000**

---

## 📊 Dataset

The training dataset contains **1,000 internship postings**:
- **500 Fake Postings**: Registration fee scams, guaranteed placement fraud, data harvesting, MLM disguises, unrealistic offers
- **500 Genuine Postings**: Real companies (TCS, Infosys, Google, startups), realistic stipends, proper requirements

### Dataset Columns
| Column | Description |
|---|---|
| `title` | Internship/job title |
| `company` | Company name |
| `description` | Full job description text |
| `stipend` | Monthly stipend in ₹ |
| `requirements` | Skills/qualifications required |
| `contact_method` | How to apply (email, portal, WhatsApp, etc.) |
| `label` | 0 = Genuine, 1 = Fake |

---

## 🤖 ML Model Details

### Preprocessing Pipeline
1. Text lowercasing
2. Punctuation removal
3. Tokenization
4. Stopword removal (NLTK English stopwords)
5. TF-IDF Vectorization (max 5,000 features)

### Models Trained
- **Logistic Regression** — Fast, interpretable baseline
- **Random Forest** — Ensemble method for better accuracy

The model with the highest F1-score is automatically selected and saved.

### Scoring Algorithm
| Signal | Weight |
|---|---|
| ML Model Prediction | 35% |
| Suspicious Keywords | 25% |
| Urgency Indicators | 15% |
| Contact Method Red Flags | 10% |
| Platform-Specific Patterns | 10% |
| Unrealistic Promises | 5% |

---

## 📸 Screenshots

> Screenshots will be added after deployment.

---

## 🔮 Future Enhancements
- [ ] Real-time web scraping from job portals
- [ ] Browser extension for instant detection
- [ ] Email integration for scanning offer letters
- [ ] Multi-language support (Hindi, Telugu, Tamil, etc.)
- [ ] Deep learning model (BERT/DistilBERT)
- [ ] API rate limiting and authentication
- [ ] User accounts and saved history

---

## 📝 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

## 👨‍💻 Authors

**Final Year Project**  
Built with ❤️ to protect students from internship scams.

---

## ⚠️ Disclaimer

This tool provides AI-based predictions and should be used as a supplementary verification method. Always perform your own due diligence before accepting any internship or job offer. The developers are not responsible for any decisions made based on this tool's output.
