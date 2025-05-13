import sys
import json
import joblib
from dataProcess import extract_single

# Paths to trained model and vectorizer
MODEL_PATH = "path to model.pkl"
VECTORIZER_PATH = "path to vectorizer.pkl"

print("[DEBUG] Script started") # troubleshooting

def extract_malicious_signals(features):
    suspicious_keys = [
        "uses_eval", "uses_function_constructor", "obfuscated_js",
        "has_eval", "has_Function", "has_atob", "has_fetch", "has_XMLHttpRequest",
        "has_chrome_cookies", "has_chrome_webRequest", "has_bitcoin", "has_crypto", "has_keylogger"
    ]
    return {k: v for k, v in features.items() if k in suspicious_keys and v}

def generate_behavioral_hints(features):
    hints = []
    if features.get("entropy", 0) > 4.5 and features.get("length", 0) < 500:
        hints.append("Short script with high entropy")
    if features.get("permissions_count", 0) <= 1:
        hints.append("Minimal permission usage")
    if features.get("manifest_version") == 3 and not features.get("uses_background") and not features.get("uses_content_scripts"):
        hints.append("Sparse manifest behavior (v3 with no background or scripts)")
    return hints if hints else ["Structural similarity to known obfuscated or loader behavior"]

def predict(folder_path):
    model = joblib.load(MODEL_PATH)
    vec = joblib.load(VECTORIZER_PATH)

    features_list = extract_single(folder_path)

    if not features_list:
        print(json.dumps({
            "status": "error",
            "message": "No features extracted from folder."
        }))
        sys.exit(1)

    try:
        vectors = vec.transform(features_list)
    except Exception as e:
        print(json.dumps({
            "status": "error",
            "message": f"Vectorization failed: {str(e)}"
        }))
        sys.exit(1)

    probabilities = model.predict_proba(vectors)
    malicious_probs = probabilities[:, 1]
    threshold = 0.7
    predictions = (malicious_probs >= threshold).astype(int)

    malicious_count = sum(predictions)
    benign_count = len(predictions) - malicious_count
    verdict = "malicious" if malicious_count > benign_count else "benign"


    if verdict == "malicious":
        avg_confidence = round(malicious_probs.mean(), 2)
    else:
        avg_confidence = round((1 - malicious_probs).mean(), 2)

    features = features_list[0]
    malicious_signals = extract_malicious_signals(features)

    if verdict == "malicious":
        if malicious_signals:
            displayed_features = malicious_signals
        else:
            displayed_features = {
                "note": "No specific red flags found, but behavior matches known malicious patterns.",
                "likely_indicators": generate_behavioral_hints(features)
            }
    else:
        displayed_features = {
            "note": "No malicious behavior detected."
        }

    result = {
        "verdict": verdict,
        "confidence": float(avg_confidence),
        "samples_analyzed": len(features_list),
        "features": displayed_features
    }

    print(json.dumps(result, indent=2))


#  MAIN ENTRY POINT 
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 predictCRX.py <folder_path>")
        sys.exit(1)

    folder_path = sys.argv[1]
    predict(folder_path)