import os
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST
from django.middleware.csrf import get_token
from .services.crx_handler import download_crx
from .services.vm_transfer import transfer_to_vm
from .services.vm_analysis import run_analysis_on_vm

# Constants
SANDBOX_DIR = os.path.join(os.path.dirname(__file__), "sandbox")
os.makedirs(SANDBOX_DIR, exist_ok=True)

@ensure_csrf_cookie
def get_csrf_token(request):
    token = get_token(request)
    response = JsonResponse({"csrfToken": token})
    response["Access-Control-Allow-Credentials"] = "true"
    return response


@require_POST
def analyze_extension(request):
    try:
        # Handle URL submission
        if request.POST.get("url"):
            url = request.POST["url"]
            result = download_crx(url)
            return JsonResponse(result)

        # Handle file upload
        if 'crx_file' in request.FILES:
            file = request.FILES['crx_file']
            extension_id = request.POST.get('extension_id', 'uploaded')
            local_path = os.path.join(SANDBOX_DIR, f"{extension_id}.crx")

            with open(local_path, 'wb+') as destination:
                for chunk in file.chunks():
                    destination.write(chunk)

            remote_path = f"/tmp/{extension_id}.crx"
            if not transfer_to_vm(local_path, remote_path):
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
    
    
