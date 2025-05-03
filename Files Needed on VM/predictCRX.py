import sys
import json
import joblib
from dataProcess import extract_single

MODEL_PATH = "/home/sanboxuser/model.pkl"
VECTORIZER_PATH = "/home/sanboxuser/vectorizer.pkl"

def predict(folder_path):
    model = joblib.load(MODEL_PATH)
    vec = joblib.load(VECTORIZER_PATH)

    features = extract_single(folder_path)
    vector = vec.transform([features])
    prediction = model.predict(vector)[0]
    proba = model.predict_proba(vector)[0]

    result = {
        "verdict": "malicious" if prediction == 1 else "benign",
        "confidence": round(max(proba), 2),
        "features": features
    }

    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 predict_crx.py <folder_path>")
        sys.exit(1)

    folder_path = sys.argv[1]
    predict(folder_path)