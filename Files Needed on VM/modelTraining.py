import json
import joblib
from collections import Counter
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction import DictVectorizer
from sklearn.metrics import accuracy_score
from dataProcess import extract_bulk

# Paths
TRAIN_DIR = "/home/sanboxuser/malware_extracted"
FEATURES_PATH = "/home/sanboxuser/features.json"
MODEL_PATH = "/home/sanboxuser/model.pkl"
VECTORIZER_PATH = "/home/sanboxuser/vectorizer.pkl"

# SExtract features
extract_bulk(TRAIN_DIR, FEATURES_PATH)

# Load and prepare data
with open(FEATURES_PATH, "r") as f:
    data = json.load(f)

X_raw = []
y = []
for d in data:
    label = d.get("label", None)
    if label is not None:
        y.append(label)
        X_raw.append({k: v for k, v in d.items() if k != "label"})

print(f"[DEBUG] Label counts: {Counter(y)}")

# Vectorize features
vec = DictVectorizer(sparse=False)
X = vec.fit_transform(X_raw)

# Train model
if len(set(y)) < 2:
    raise ValueError("Need at least two classes (e.g., malicious and benign) to train the model.")

X_train, y_train = X, y
model = LogisticRegression(max_iter=1000)
model.fit(X_train, y_train)

# Save model and vectorizer
joblib.dump(model, MODEL_PATH)
joblib.dump(vec, VECTORIZER_PATH)
print(f"[✓] Model saved to {MODEL_PATH}")