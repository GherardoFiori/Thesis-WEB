import os
import json
import joblib
from collections import Counter
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction import DictVectorizer
from sklearn.metrics import accuracy_score, classification_report
from dataProcess import extract_features_from_folder, extract_features_from_js_files

# file paths
MALWARE_DIR = "path to malware_extracted"
FEATURES_PATH = "path to features.json"
MODEL_PATH = "path to model.pkl"
VECTORIZER_PATH = "path to vectorizer.pkl"

# Extract features from all CRX folders
dataset = []

# Load benign (folder-level)
benign_base = os.path.join(MALWARE_DIR, "benign_extracted")
for entry in os.listdir(benign_base):
    folder_path = os.path.join(benign_base, entry)
    if os.path.isdir(folder_path):
        features = extract_features_from_folder(folder_path)
        if isinstance(features, list):
            if not features:
                continue
            features = features[0]
        features["label"] = 0
        features["path"] = folder_path
        dataset.append(features)

# Load malicious (file-level) 
malicious_base = os.path.join(MALWARE_DIR, "malicious_extracted")
malicious_samples = extract_features_from_js_files(malicious_base)
dataset.extend(malicious_samples)

# Save raw features for inspection/debugging
with open(FEATURES_PATH, "w") as f:
    json.dump(dataset, f, indent=2)
print(f"[✓] Features written to {FEATURES_PATH}")

#  Prepare input/output for ML =
X_raw = []
y = []
for d in dataset:
    label = d.get("label")
    if label is not None:
        y.append(label)
        X_raw.append({k: v for k, v in d.items() if k not in ("label", "path")})

print(f"Label distribution: {Counter(y)}")

# Vectorize features 
vec = DictVectorizer(sparse=False)
X = vec.fit_transform(X_raw)

# Train-test split 
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)

# Train model 
model = LogisticRegression(max_iter=1000)
model.fit(X_train, y_train)
print("[Debug] Training labels in y_train:", Counter(y_train))
print("[✓] Model training complete.")

# Evaluate 
probs = model.predict_proba(X_test)[:, 1]
threshold = 0.7
preds = (probs >= threshold).astype(int)
accuracy = accuracy_score(y_test, preds)
print(f" Test Accuracy: {accuracy * 100:.2f}%")

print("Classification Report:")
print(classification_report(y_test, preds, target_names=["Benign", "Malicious"]))


# Save model and vectorizer 
joblib.dump(model, MODEL_PATH)
joblib.dump(vec, VECTORIZER_PATH)
print(f"Model saved to: {MODEL_PATH}")
print(f"Vectorizer saved to: {VECTORIZER_PATH}")