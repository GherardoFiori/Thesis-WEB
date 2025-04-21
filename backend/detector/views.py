import os
import json
import paramiko
import requests
from scp import SCPClient
from dotenv import load_dotenv
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.http import require_POST

# Load environment variables
load_dotenv()
VM_HOST = os.getenv("VM_HOST")
VM_USER = os.getenv("VM_USER")
VM_KEY = os.getenv("VM_KEY")
VM_REMOTE_PATH = os.getenv("VM_REMOTE_PATH")
VM_SCRIPT = os.getenv("VM_SCRIPT")

# Constants
SANDBOX_DIR = os.path.join(os.path.dirname(__file__), "sandbox")
CHROME_VERSION = "134.0.6998.178"
os.makedirs(SANDBOX_DIR, exist_ok=True)

# CSRF Token Endpoint
@ensure_csrf_cookie
def get_csrf_token(request):
    return JsonResponse({"csrfToken": request.META.get('CSRF_COOKIE')})


@require_POST
def analyze_extension(request):
    try:
        # Handle URL submission
        if request.POST.get("url"):
            url = request.POST["url"]
            result = download_crx(url)
            return JsonResponse(result)

        if 'crx_file' in request.FILES:
            file = request.FILES['crx_file']
            extension_id = request.POST.get('extension_id', 'uploaded')
            local_path = os.path.join(SANDBOX_DIR, f"{extension_id}.crx")

            with open(local_path, 'wb+') as destination:
                for chunk in file.chunks():
                    destination.write(chunk)

            remote_path = os.path.join(VM_REMOTE_PATH, f"{extension_id}.crx")
            transfer_success = transfer_to_vm(local_path, remote_path)

            if not transfer_success:
                raise Exception("VM transfer failed")

           
            analysis_result = run_analysis_on_vm(remote_path)

            if analysis_result["status"] != "success":
                return JsonResponse(analysis_result, status=500)

            return JsonResponse({
                "status": "success",
                "message": "Extension analyzed",
                "verdict": analysis_result["result"].get("verdict"),
                "confidence": analysis_result["result"].get("confidence"),
                "features": analysis_result["result"].get("features", {})
            })

        return JsonResponse({"status": "error", "message": "No file or URL provided"})

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


def download_crx(url):
    try:
        if not ("chrome.google.com" in url or "chromewebstore.google.com" in url):
            raise ValueError("Invalid Chrome Web Store URL")

        extension_id = extract_extension_id(url)
        if not extension_id:
            raise ValueError("Could not extract extension ID")

        return download_with_requests(extension_id)

    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "debug": {"url": url}
        }


def extract_extension_id(url):
    try:
        parts = url.split('/')
        if '/detail/' in url:
            return parts[-1]
        elif '?id=' in url:
            return url.split('?id=')[1].split('&')[0]
        return None
    except Exception:
        return None


def download_with_requests(extension_id):
    crx_url = (
        f"https://clients2.google.com/service/update2/crx?"
        f"response=redirect&prodversion={CHROME_VERSION}&"
        f"acceptformat=crx3&x=id%3D{extension_id}%26uc"
    )

    file_path = os.path.join(SANDBOX_DIR, f"{extension_id}.crx")

    try:
        response = requests.get(crx_url, headers={
            "User-Agent": "Mozilla/5.0"
        }, timeout=30)
        response.raise_for_status()

        with open(file_path, 'wb') as f:
            f.write(response.content)

        if os.path.getsize(file_path) == 0:
            raise ValueError("Downloaded empty file")

        remote_path = os.path.join(VM_REMOTE_PATH, f"{extension_id}.crx")
        transfer_success = transfer_to_vm(file_path, remote_path)

        if not transfer_success:
            raise Exception("VM transfer failed")

        analysis_result = run_analysis_on_vm(remote_path)

        if analysis_result["status"] != "success":
            return analysis_result

        return {
            "status": "success",
            "message": "Extension analyzed",
            "verdict": analysis_result["result"].get("verdict"),
            "confidence": analysis_result["result"].get("confidence"),
            "features": analysis_result["result"].get("features", {})
        }

    except requests.RequestException as e:
        return {
            "status": "error",
            "message": f"Download failed: {str(e)}",
            "debug": {
                "url": crx_url,
                "status_code": getattr(e.response, 'status_code', None)
            }
        }


def transfer_to_vm(local_path, remote_path):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            hostname=VM_HOST,
            username=VM_USER,
            key_filename=VM_KEY,
            timeout=10
        )

        ssh.exec_command(f"mkdir -p {os.path.dirname(remote_path)}")

        with SCPClient(ssh.get_transport()) as scp:
            scp.put(local_path, remote_path)

        stdin, stdout, stderr = ssh.exec_command(f"ls {remote_path}")
        if not stdout.read().decode().strip():
            raise Exception("File not found on VM after transfer")

        return True
    except Exception as e:
        print(f"VM Transfer Error: {str(e)}")
        return False
    finally:
        ssh.close()


def run_analysis_on_vm(remote_path):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            hostname=VM_HOST,
            username=VM_USER,
            key_filename=VM_KEY,
            timeout=10
        )

        cmd = f"python3 {os.path.join(VM_SCRIPT, 'extractCRX2.py')} {remote_path}"
        stdin, stdout, stderr = ssh.exec_command(cmd)

        raw_output = stdout.read().decode()
        error_output = stderr.read().decode()

        ssh.close()

        if error_output:
            return {"status": "error", "message": f"VM stderr: {error_output}"}

        json_start = raw_output.find('{')
        json_end = raw_output.rfind('}') + 1

        if json_start == -1 or json_end == -1:
            return {"status": "error", "message": "Failed to locate JSON in output", "raw_output": raw_output}

        clean_json = raw_output[json_start:json_end]

        result = json.loads(clean_json)

        return {"status": "success", "result": result}

    except Exception as e:
        return {"status": "error", "message": f"Failed to parse model output: {str(e)}"}
