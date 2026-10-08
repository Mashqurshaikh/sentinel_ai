"""
Train the TF-IDF + Logistic Regression category/risk classifiers.

Usage:
    python models/train_risk_classifier.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from models.risk_classifier import train_classifiers

if __name__ == "__main__":
    data_path = os.path.join(os.path.dirname(__file__), "..", "data", "prompts.csv")
    if not os.path.exists(data_path):
        print("prompts.csv not found. Run `python data/generate_prompts.py` first.")
        sys.exit(1)
    train_classifiers(data_path)
