import os
from dotenv import load_dotenv
import paramiko
import requests
from scp import SCPClient
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.http import require_POST


load_dotenv()
VM_HOST = os.getenv("VM_HOST")
VM_USER = os.getenv("VM_USER")
VM_KEY = os.getenv("VM_KEY")
VM_REMOTE_PATH = os.getenv("VM_REMOTE_PATH")


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
        # Handle URL case
        if request.POST.get("url"):
            url = request.POST["url"]
            result = download_crx(url)  # Now properly defined below
            return JsonResponse(result)
        
        # Handle file upload case
        if 'crx_file' in request.FILES:
            file = request.FILES['crx_file']
            extension_id = request.POST.get('extension_id', 'uploaded')
            
            # Save locally
            local_path = os.path.join(SANDBOX_DIR, f"{extension_id}.crx")
            with open(local_path, 'wb+') as destination:
                for chunk in file.chunks():
                    destination.write(chunk)
            
            # Transfer to VM
            remote_path = os.path.join(VM_REMOTE_PATH, f"{extension_id}.crx")
            transfer_success = transfer_to_vm(local_path, remote_path)
            
            if not transfer_success:
                raise Exception("VM transfer failed")
            
            return JsonResponse({
                "status": "success",
                "message": "File processed",
                "remote_path": remote_path,
                "size": os.path.getsize(local_path)
            })
            
        return JsonResponse({"status": "error", "message": "No file or URL provided"})
    
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

# CRX Download Function (now properly defined)
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

# Helper Functions
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
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        }, timeout=30)
        response.raise_for_status()
        
        with open(file_path, 'wb') as f:
            f.write(response.content)
            
        if os.path.getsize(file_path) == 0:
            raise ValueError("Downloaded empty file")
        
        # Transfer to VM
        remote_path = os.path.join(VM_REMOTE_PATH, f"{extension_id}.crx")
        transfer_success = transfer_to_vm(file_path, remote_path)
        
        if not transfer_success:
            raise ValueError("Failed to transfer file to VM")
            
        return {
            "status": "success",
            "file_path": file_path,
            "remote_path": remote_path,
            "size": os.path.getsize(file_path)
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

# VM Transfer Function
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
        
        # Create remote directory if needed
        ssh.exec_command(f"mkdir -p {os.path.dirname(remote_path)}")
        
        with SCPClient(ssh.get_transport()) as scp:
            scp.put(local_path, remote_path)
        
        # Verify transfer
        stdin, stdout, stderr = ssh.exec_command(f"ls {remote_path}")
        if not stdout.read().decode().strip():
            raise Exception("File not found on VM after transfer")
            
        return True
    except Exception as e:
        print(f"VM Transfer Error: {str(e)}")
        return False
    finally:
        ssh.close()