# Upgrading the risk classifier

The current classifier is TF-IDF + Logistic Regression, trained in
`train_risk_classifier.py`. It's fast and fully inspectable, which is
useful while you're still tuning detection rules.

To move to a transformer:

1. Swap `TfidfVectorizer` + `LogisticRegression` for a Hugging Face
   `AutoModelForSequenceClassification` (DistilBERT is a reasonable size to
   start with).
2. Keep the same train/test split and label columns (`category`,
   `risk_level`) in `data/prompts.csv` - only the model and tokenizer
   change, not the data pipeline.
3. `RiskClassifier.predict()` is the only place `risk_engine.py` talks to
   the model, so the rest of the codebase doesn't need to change.
4. You'll want a GPU for training at any real dataset size - CPU inference
   is fine, CPU fine-tuning is not.
