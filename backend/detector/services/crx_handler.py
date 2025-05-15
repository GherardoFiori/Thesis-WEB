import os
import requests
from detector.services.vm_transfer import transfer_to_vm
from detector.services.vm_analysis import run_analysis_on_vm
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv()
CHROME_VERSION = "134.0.6998.178"
VM_REMOTE_PATH = os.getenv("VM_REMOTE_PATH")
SANDBOX_DIR = os.path.join(os.path.dirname(__file__), "..", "sandbox")
os.makedirs(SANDBOX_DIR, exist_ok=True)

def extract_extension_id(url):
    parsed_url = urlparse(url)
    path_parts = parsed_url.path.strip("/").split("/")

    # Handle new and old Chrome Web Store URLs
    if "chrome.google.com" in url or "chromewebstore.google.com" in url:
        if "detail" in path_parts and len(path_parts) >= 3:
            return path_parts[-1], "chrome"  
        else:
            raise ValueError("Invalid Chrome Web Store URL structure.")
    
    elif "addons.mozilla.org" in url:
        if 'addon' in path_parts:
            return path_parts[path_parts.index('addon') + 1], "firefox"
    
    elif "microsoftedge.microsoft.com/addons" in url:
        raise ValueError("Edge Add-ons not supported.")
    
    return None, None

def download_crx(url):
    try:
        extension_id, browser = extract_extension_id(url)
        if not extension_id:
            raise ValueError("Could not extract extension ID")

        return download_with_requests(extension_id, browser)

    except Exception as e:
        return {"status": "error", "message": str(e)}

def download_with_requests(extension_id, browser):
    if browser == "chrome":
        crx_url = (
            f"https://clients2.google.com/service/update2/crx?"
            f"response=redirect&prodversion={CHROME_VERSION}&"
            f"acceptformat=crx3&x=id%3D{extension_id}%26uc"
        )
    elif browser == "firefox":
        crx_url = f"https://addons.mozilla.org/firefox/downloads/latest/{extension_id}/addon-latest.xpi"
    else:
        return {"status": "error", "message": "Unsupported browser"}

    file_ext = "crx" if browser == "chrome" else "xpi"
    file_path = os.path.join(SANDBOX_DIR, f"{extension_id}.{file_ext}")
    remote_path = os.path.join(VM_REMOTE_PATH, f"{extension_id}.{file_ext}")

    try:
        response = requests.get(crx_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
        response.raise_for_status()

        print("Final URL:", response.url)
        print("Content-Type:", response.headers.get("Content-Type"))
        print("First 200 chars:", response.text[:200] if "text" in response.headers.get("Content-Type", "") else "Binary")

        # Check Content-Type  if HTML it means something went wrong
        if "text/html" in response.headers.get("Content-Type", ""):
             raise ValueError("Received HTML instead of a CRX file. Extension may not be available for direct download.")

         # Save the CRX or XPI file
        with open(file_path, 'wb') as f:
            f.write(response.content)

        if os.path.getsize(file_path) == 0:
            raise ValueError("Downloaded file is empty")

        if not transfer_to_vm(file_path, remote_path):
            raise Exception("Transfer failed")

        result = run_analysis_on_vm(remote_path)
        if result["status"] != "success":
            return result

        return {
            "status": "success",
            "message": "Extension analyzed",
            "verdict": result["result"].get("verdict"),
            "confidence": result["result"].get("confidence"),
            "features": result["result"].get("features", {})
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}
