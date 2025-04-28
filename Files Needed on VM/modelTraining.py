import os
import json
import joblib
from collections import Counter
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction import DictVectorizer
from sklearn.metrics import accuracy_score
from dataProcess import extract_features_from_folder 


MALWARE_DIR = "/home/sanboxuser/malware_extracted"
FEATURES_PATH = "/home/sanboxuser/features.json"
MODEL_PATH = "/home/sanboxuser/model.pkl"
VECTORIZER_PATH = "/home/sanboxuser/vectorizer.pkl"


dataset = []
for root, dirs, files in os.walk(MALWARE_DIR):
    if "manifest.json" in files:
        feats = extract_features_from_folder(root)
       
        if "benign_extracted" in root:
            feats["label"] = 0
        else:
            feats["label"] = 1
        feats["path"] = root
        dataset.append(feats)

with open(FEATURES_PATH, "w") as f:
    json.dump(dataset, f, indent=2)
print(f"[✓] Features written to {FEATURES_PATH}")


X_raw = []
y = []
for d in dataset:
    label = d.get("label", None)
    if label is not None:
        y.append(label)
        X_raw.append({k: v for k, v in d.items() if k != "label"})

print(f"[DEBUG] Label counts: {Counter(y)}")


vec = DictVectorizer(sparse=False)
X = vec.fit_transform(X_raw)


if len(set(y)) < 2:
    raise ValueError("Need at least two classes")

X_train, y_train = X, y
model = LogisticRegression(max_iter=1000)
model.fit(X_train, y_train)

y_pred = model.predict(X_train)
accuracy = accuracy_score(y_train, y_pred)
print(f"[✓] Training Accuracy: {accuracy * 100:.2f}%")


joblib.dump(model, MODEL_PATH)
joblib.dump(vec, VECTORIZER_PATH)
print(f"[✓] Model saved to {MODEL_PATH}")