import os
import sys
import shutil
import subprocess
import json

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
    subprocess.run(["7z", "x", CRX_PATH, f"-o{extract_dir}", "-y"], check=True)
except subprocess.CalledProcessError as e:
    print(json.dumps({"status": "error", "message": f"Extraction failed: {str(e)}"}))
    sys.exit(1)


try:
    result = subprocess.run(
        ["python3", "PATH TO /predictCRX.py", extract_dir],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if result.stderr:
        print(json.dumps({"status": "error", "message": f"Prediction stderr: {result.stderr.strip()}"}))
        sys.exit(1)

    lines = result.stdout.strip().splitlines()
    if not lines:
        print(json.dumps({"status": "error", "message": "Prediction returned no output"}))
        sys.exit(1)


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