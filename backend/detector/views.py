import os
import subprocess
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

SANDBOX_DIR = os.path.join(os.path.dirname(__file__), "sandbox")
CHROME_VERSION = "134.0.6998.178"  
USE_REQUESTS = True  

os.makedirs(SANDBOX_DIR, exist_ok=True)

@csrf_exempt
@require_POST
def analyze_extension(request):
    try:
        # This is where the url is handled
        if request.POST.get("url"):
            url = request.POST["url"]
            result = download_crx(url)
            return JsonResponse(result)
        
        # This is where the file is handled
        if request.ILES.get('crx_file'):
            return handleFileUpload(request)
        
        return JsonResponse({"status": "error", "message": "No URL or file provided"})
    
    except Exception as e:
        return JsonResponse({"status": "error", "message": f"Server error: {str(e)}"})

def handleFileUpload(request):
    file = request.FILES['crx_file']
    extension_id = request.POST.get('extension_id', 'uploaded')
    
    try:
        file_path = os.path.join(SANDBOX_DIR, f"{extension_id}.crx")
        with open(file_path, 'wb') as f:
            for chunk in file.chunks():
                f.write(chunk)
        
        return JsonResponse({
            "status": "success", 
            "file_path": file_path,
            "size": os.path.getsize(file_path)
        })
    except Exception as e:
        return JsonResponse({"status": "error", "message": f"File upload failed: {str(e)}"})

def download_crx(url):
    try:
        # Extract extension ID
        if not ("chrome.google.com" in url or "chromewebstore.google.com" in url):
            raise ValueError("Invalid Chrome Web Store URL")
            
        extension_id = extract_extension_id(url)
        if not extension_id:
            raise ValueError("Could not extract extension ID")
        
        if USE_REQUESTS:
            result = downloadWithRequests(extension_id)
        else:
            result = downloadWithWget(extension_id)

        # just needed during trouble shooting
        file_path = os.path.join(SANDBOX_DIR, f"{extension_id}.crx")
        print(f"\nDEBUG INFO:")
        print(f"Extension ID: {extension_id}")
        print(f"Target path: {file_path}")
        print(f"File exists: {os.path.exists(file_path)}")
        print(f"File size: {os.path.getsize(file_path) if os.path.exists(file_path) else 0} bytes")
        
        return result
            
    except Exception as e:
        return {
            "status": "error", 
            "message": str(e),
            "debug": {"url": url, "extension_id": extension_id}
        }

def downloadWithRequests(extension_id):
    """Download using Python requests library."""
    crx_url = (
        f"https://clients2.google.com/service/update2/crx?"
        f"response=redirect&prodversion={CHROME_VERSION}&"
        f"acceptformat=crx3&x=id%3D{extension_id}%26uc"
    )
    
    file_path = os.path.join(SANDBOX_DIR, f"{extension_id}.crx")
    
    try:
        response = requests.get(
            crx_url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-User": "?1",
                "Sec-Fetch-Dest": "document"
            },
            timeout=30
        )
        response.raise_for_status()
        
        with open(file_path, 'wb') as f:
            f.write(response.content)
            
        if os.path.getsize(file_path) == 0:
            raise ValueError("Downloaded empty file")
            
        return {
            "status": "success",
            "file_path": file_path,
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

def downloadWithWget(extension_id):
    """Download using wget (fallback method)."""
    crx_url = (
        f"https://clients2.google.com/service/update2/crx?"
        f"response=redirect&prodversion={CHROME_VERSION}&"
        f"acceptformat=crx3&x=id%3D{extension_id}%26uc"
    )
    
    file_path = os.path.join(SANDBOX_DIR, f"{extension_id}.crx")
    
    try:
        result = subprocess.run(
            ['wget', '--tries=3', '--timeout=30', crx_url, '-O', file_path],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if not os.path.exists(file_path):
            raise ValueError("File not created")
            
        return {
            "status": "success",
            "file_path": file_path,
            "size": os.path.getsize(file_path),
            "debug": {
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        }
        
    except subprocess.CalledProcessError as e:
        return {
            "status": "error",
            "message": "wget download failed",
            "debug": {
                "stdout": e.stdout,
                "stderr": e.stderr,
                "returncode": e.returncode
            }
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