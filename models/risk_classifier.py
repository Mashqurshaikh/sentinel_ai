"""
Risk classifier.

TF-IDF + Logistic Regression models that predict:
    - risk_level: low / medium / high
    - category:   benign / source_code / secret_leak / pii_leak / prompt_injection

Chosen over a transformer fine-tune because it trains in seconds on CPU and
stays fully inspectable (you can see which terms drove a decision, which
matters for a security tool where false positives need to be explainable).

Used as a second opinion alongside the rule-based detectors: rules give
high recall on known patterns, the model generalizes to paraphrased or
novel prompts the rules would miss. See models/upgrade_notes.md for the
transformer upgrade path.
"""

import os
import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from sklearn.pipeline import Pipeline


MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "checkpoints")


def train_classifiers(data_path: str, model_dir: str = MODEL_DIR):
    os.makedirs(model_dir, exist_ok=True)
    df = pd.read_csv(data_path)

    X_train, X_test, y_cat_train, y_cat_test, y_risk_train, y_risk_test = train_test_split(
        df["prompt"], df["category"], df["risk_level"], test_size=0.2, random_state=42, stratify=df["category"]
    )

    category_pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(max_features=3000, ngram_range=(1, 2), stop_words="english")),
        ("clf", LogisticRegression(max_iter=1000, class_weight="balanced")),
    ])
    category_pipeline.fit(X_train, y_cat_train)
    cat_report = classification_report(y_cat_test, category_pipeline.predict(X_test), output_dict=True)

    risk_pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(max_features=3000, ngram_range=(1, 2), stop_words="english")),
        ("clf", LogisticRegression(max_iter=1000, class_weight="balanced")),
    ])
    risk_pipeline.fit(X_train, y_risk_train)
    risk_report = classification_report(y_risk_test, risk_pipeline.predict(X_test), output_dict=True)

    joblib.dump(category_pipeline, os.path.join(model_dir, "category_classifier.joblib"))
    joblib.dump(risk_pipeline, os.path.join(model_dir, "risk_classifier.joblib"))

    print("=== Category classifier ===")
    print(classification_report(y_cat_test, category_pipeline.predict(X_test)))
    print("=== Risk level classifier ===")
    print(classification_report(y_risk_test, risk_pipeline.predict(X_test)))

    return category_pipeline, risk_pipeline, cat_report, risk_report


class RiskClassifier:
    """Loads trained pipelines and exposes a simple .predict(text) API."""

    def __init__(self, model_dir: str = MODEL_DIR):
        cat_path = os.path.join(model_dir, "category_classifier.joblib")
        risk_path = os.path.join(model_dir, "risk_classifier.joblib")
        if not os.path.exists(cat_path) or not os.path.exists(risk_path):
            raise FileNotFoundError(
                "Classifier not trained yet. Run `python models/train_risk_classifier.py` first."
            )
        self.category_pipeline = joblib.load(cat_path)
        self.risk_pipeline = joblib.load(risk_path)

    def predict(self, text: str) -> dict:
        category = self.category_pipeline.predict([text])[0]
        category_proba = max(self.category_pipeline.predict_proba([text])[0])
        risk_level = self.risk_pipeline.predict([text])[0]
        risk_proba = max(self.risk_pipeline.predict_proba([text])[0])
        return {
            "ml_category": category,
            "ml_category_confidence": round(float(category_proba), 3),
            "ml_risk_level": risk_level,
            "ml_risk_confidence": round(float(risk_proba), 3),
        }
