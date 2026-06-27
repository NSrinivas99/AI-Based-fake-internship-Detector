"""
train_model.py
Loads the internship dataset, preprocesses text, trains classifiers,
selects the best model by F1-score, and saves it to model/
"""

import os
import re
import string
import warnings

import joblib
import nltk
import numpy as np
import pandas as pd
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import train_test_split

warnings.filterwarnings("ignore")

# ── Download required NLTK data ──────────────────────────────────
nltk.download("punkt", quiet=True)
nltk.download("punkt_tab", quiet=True)
nltk.download("stopwords", quiet=True)

# ── 1. Load dataset ──────────────────────────────────────────────
DATASET_PATH = os.path.join("dataset", "internship_dataset.csv")
print(f"Loading dataset from {DATASET_PATH} ...")
df = pd.read_csv(DATASET_PATH)
print(f"  Loaded {len(df)} rows  (Fake={( df['label']==1).sum()}, Genuine={(df['label']==0).sum()})")

# ── 2. Combine text columns into a single feature ────────────────
# Merging title + description + requirements + contact_method gives the
# classifier richer signal (e.g., "WhatsApp only" in contact is a red flag).
df["text"] = (
    df["title"].astype(str) + " " +
    df["description"].astype(str) + " " +
    df["requirements"].astype(str) + " " +
    df["contact_method"].astype(str) + " " +
    df["stipend"].astype(str)
)

# ── 3. Text preprocessing ────────────────────────────────────────
stop_words = set(stopwords.words("english"))

def preprocess(text: str) -> str:
    """Lowercase, remove punctuation/digits, tokenize, remove stopwords."""
    text = text.lower()
    # Remove special characters, keep only letters and spaces
    text = re.sub(r"[^a-zA-Z\s]", " ", text)
    # Tokenize
    tokens = word_tokenize(text)
    # Remove stopwords and very short tokens
    tokens = [t for t in tokens if t not in stop_words and len(t) > 2]
    return " ".join(tokens)

print("Preprocessing text ...")
df["clean_text"] = df["text"].apply(preprocess)

# ── 4. TF-IDF vectorization ──────────────────────────────────────
print("Building TF-IDF vectors (max_features=5000) ...")
tfidf = TfidfVectorizer(max_features=5000, ngram_range=(1, 2))
X = tfidf.fit_transform(df["clean_text"])
y = df["label"].values

# ── 5. Train-test split ──────────────────────────────────────────
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
print(f"  Train: {X_train.shape[0]}  |  Test: {X_test.shape[0]}")

# ── 6. Train models ──────────────────────────────────────────────
models = {
    "Logistic Regression": LogisticRegression(
        max_iter=1000, C=1.0, random_state=42
    ),
    "Random Forest": RandomForestClassifier(
        n_estimators=200, max_depth=None, random_state=42, n_jobs=-1
    ),
}

results = {}

for name, model in models.items():
    print(f"\nTraining {name} ...")
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    acc = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, average="weighted")

    results[name] = {
        "model": model,
        "accuracy": acc,
        "f1": f1,
        "y_pred": y_pred,
    }

    print(f"  Accuracy : {acc:.4f}")
    print(f"  F1-score : {f1:.4f}")
    print(f"\n  Classification Report – {name}:")
    print(classification_report(y_test, y_pred, target_names=["Genuine", "Fake"]))

# ── 7. Select best model by F1-score ─────────────────────────────
best_name = max(results, key=lambda k: results[k]["f1"])
best_model = results[best_name]["model"]
best_f1 = results[best_name]["f1"]
best_acc = results[best_name]["accuracy"]

print("=" * 55)
print(f"  BEST MODEL : {best_name}")
print(f"  Accuracy   : {best_acc:.4f}")
print(f"  F1-score   : {best_f1:.4f}")
print("=" * 55)

# ── 8. Save model and vectorizer ─────────────────────────────────
MODEL_DIR = "model"
os.makedirs(MODEL_DIR, exist_ok=True)

model_path = os.path.join(MODEL_DIR, "internship_model.pkl")
tfidf_path = os.path.join(MODEL_DIR, "tfidf.pkl")

joblib.dump(best_model, model_path)
joblib.dump(tfidf, tfidf_path)

print(f"\n  Model saved      -> {model_path}")
print(f"  Vectorizer saved -> {tfidf_path}")
print("\nDone!")
