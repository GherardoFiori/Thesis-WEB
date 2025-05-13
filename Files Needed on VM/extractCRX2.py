import os
import sys
import shutil
import subprocess
import json
import zipfile

os.makedirs("PLACE PATH TO WHERE CRX IS STORED HERE", exist_ok=True)


# Ensure a CRX path is passed
if len(sys.argv) != 2:
    print(json.dumps({"status": "error", "message": "Usage: python3 extractCRX2.py <path_to_crx>"}))
    sys.exit(1)

CRX_PATH = sys.argv[1]

# Ensure .crx file exists
if not os.path.isfile(CRX_PATH):
    print(json.dumps({"status": "error", "message": f"CRX file not found: {CRX_PATH}"}))
    sys.exit(1)

# Set up extraction path
base_name = os.path.splitext(os.path.basename(CRX_PATH))[0]
extract_dir = f"PLACE PATH TO WHERE CRX IS STORED HERE/{base_name}"
os.makedirs(extract_dir, exist_ok=True)

# Extract using 7z
try:
    with zipfile.ZipFile(CRX_PATH, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
except zipfile.BadZipFile:
    # If standard extraction fails, try ignoring trailing data
    with open(CRX_PATH, 'rb') as f:
        data = f.read()
    # CRX files have a 16-byte header before the ZIP data
    zip_data = data[16:]
    with zipfile.ZipFile(io.BytesIO(zip_data), 'r') as zip_ref:
        zip_ref.extractall(extract_dir)


try:
    result = subprocess.run(
        ["python3", "/home/sanboxuser/predictCRX.py", extract_dir],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )


    stderr_clean = result.stderr.strip()
    harmless_warning_keywords = ["glibc", "FutureWarning", "xgboost"]
    is_critical = stderr_clean and not any(k in stderr_clean for k in harmless_warning_keywords)

    if is_critical:
        print(json.dumps({"status": "error", "message": f"Prediction stderr: {stderr_clean}"}))
        sys.exit(1)

    lines = result.stdout.strip().splitlines()
    if not lines:
        print(json.dumps({"status": "error", "message": "Prediction returned no output"}))
        sys.exit(1)

    # Join the multiline JSON starting from the first line that looks like JSON
    try:
        json_start = next(i for i, line in enumerate(lines) if line.strip().startswith("{"))
        json_block = "\n".join(lines[json_start:])
        verdict_json = json.loads(json_block)
    except Exception as e:
        print(json.dumps({
            "status": "error",
            "message": f"Failed to parse model output: {str(e)}",
            "raw_output": lines
        }))
        sys.exit(1)

except Exception as e:
    print(json.dumps({"status": "error", "message": f"Prediction failed: {str(e)}"}))
    sys.exit(1)


# Step 3: Cleanup
try:
    os.remove(CRX_PATH)
    shutil.rmtree(extract_dir)
except Exception as e:
    verdict_json["cleanup_warning"] = f"Cleanup failed: {str(e)}"

# Step 4: Output the result
print(json.dumps(verdict_json, indent=2))