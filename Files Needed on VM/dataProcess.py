import os
import json
import math

KEYWORDS = [
    "eval", "Function", "atob", "fetch(", "XMLHttpRequest",
    "chrome.cookies", "chrome.webRequest", "bitcoin", "crypto", "keylogger"
]
PERMISSIONS = [
    "tabs", "cookies", "webRequest", "history",
    "bookmarks", "clipboardRead", "management"
]

def calculate_entropy(content):
    if not content:
        return 0
    prob = [float(content.count(c)) / len(content) for c in dict.fromkeys(content)]
    entropy = -sum([p * math.log2(p) for p in prob])
    return round(entropy, 2)

def extract_js_features(js_code):
    features = {
        "length": len(js_code),
        "entropy": calculate_entropy(js_code),
        "uses_eval": "eval" in js_code,
        "uses_function_constructor": "Function(" in js_code,
        "obfuscated_js": False
    }

    features["obfuscated_js"] = features["entropy"] > 4.5 and features["length"] > 1000

    for keyword in KEYWORDS:
        key = f"has_{keyword.replace('.', '_').replace('(', '')}"
        features[key] = keyword in js_code

    return features

def extract_manifest_features(manifest_path):
    features = {}
    try:
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        features["permissions_count"] = len(manifest.get("permissions", []))
        for perm in PERMISSIONS:
            features[f"perm_{perm}"] = perm in manifest.get("permissions", [])
        features["uses_background"] = "background" in manifest
        features["uses_content_scripts"] = "content_scripts" in manifest
        features["manifest_version"] = manifest.get("manifest_version", 2)
    except Exception as e:
        features["manifest_failed"] = True
        print(f"[!] Failed to read manifest: {e}")
    return features

def extract_features_from_folder(folder_path):

    print(f"[DEBUG] Scanning folder: {folder_path}")

    feature_set = {
        "js_file_count": 0,
        "total_js_size": 0,
        "avg_entropy": 0.0
    }
    entropies = []

    # Manifest features
    manifest_path = os.path.join(folder_path, "manifest.json")
    if os.path.exists(manifest_path):
        feature_set.update(extract_manifest_features(manifest_path))

    # JS features
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".js"):
                full_path = os.path.join(root, file)
                print(f"[DEBUG] Found JS: {full_path}")
                feature_set["js_file_count"] += 1
                try:
                    with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                        code = f.read()
                        feature_set["total_js_size"] += len(code)
                        js_feats = extract_js_features(code)
                        entropies.append(js_feats["entropy"])
                        feature_set.update(js_feats)
                except Exception as e:
                    print(f"[!] Error reading JS file {full_path}: {e}")
                    continue

    if entropies:
        feature_set["avg_entropy"] = round(sum(entropies) / len(entropies), 2)

    return feature_set

def extract_bulk(training_dir, output_path):
    dataset = []
    for root, dirs, files in os.walk(training_dir):
        if "manifest.json" in files:
            feats = extract_features_from_folder(root)
            if "BenignSample" in root:
                feats["label"] = 0
            else:
                feats["label"] = 1
            feats["path"] = root
            dataset.append(feats)

    with open(output_path, "w") as f:
        json.dump(dataset, f, indent=2)
    print(f"[✓] Features written to {output_path}")

def extract_single(folder_path):
    return extract_features_from_folder(folder_path)