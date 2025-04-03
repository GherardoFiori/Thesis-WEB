import os
import re
import json
import subprocess
import tempfile
import zipfile
import requests
from urllib.parse import urlparse, parse_qs
from django.http import JsonResponse
from django.views import View

class ExtensionAnalyzer(View):
    def getExtensionID(self, url):

        parsed_url = urlparse(url)
        
        if "chrome.google.com" in parsed_url.netloc:
            match = re.search(r"detail/[^/]+/([a-zA-Z0-9_-]+)", parsed_url.path)
            if match:
                return match.group(1)
        elif "addons.mozilla.org" in parsed_url.netloc:
            query_params = parse_qs(parsed_url.query)
            return query_params.get("id", [None])[0]
        
        return None

    def downloadExtension(self, extension_id, browser="chrome"):
        temp_dir = tempfile.mkdtemp()
        file_path = os.path.join(temp_dir, f"{extension_id}.crx" if browser == "chrome" else f"{extension_id}.xpi")
        
        if browser == "chrome":
            download_url = f"https://clients2.google.com/service/update2/crx?response=redirect&prodversion=91.0&acceptformat=crx2,crx3&x=id%3D{extension_id}%26installsource%3Dondemand%26uc"
        else:
            download_url = f"https://addons.mozilla.org/firefox/downloads/latest/{extension_id}/addon-latest.xpi"
        
        try:
            response = requests.get(download_url, stream=True, timeout=10)
            response.raise_for_status()
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return file_path
        except requests.RequestException as e:
            return None

    def extractExtension(self, file_path, browser="chrome"):
        extractDir = tempfile.mkdtemp()
        
        if browser == "chrome":
            try:
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall(extractDir)
                return extractDir
            except zipfile.BadZipFile:
                return None
        else:
            return extractDir  

    def analyzePermissions(self, extractDir):
        manifest_path = os.path.join(extractDir, "manifest.json")
        
        if os.path.exists(manifest_path):
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
                return manifest.get("permissions", [])
        
        return []

    def get(self, request): # Just some simple error handling for trouble shooting
        url = request.GET.get("url")
        if not url:
            return JsonResponse({"error": "No URL provided."}, status=400)
        
        extension_id = self.getExtensionID(url)
        if not extension_id:
            return JsonResponse({"error": "Invalid extension URL."}, status=400)
        
        browser = "chrome" if "chrome.google.com" in url else "firefox"
        file_path = self.downloadExtension(extension_id, browser)
        if not file_path:
            return JsonResponse({"error": "Failed to download extension."}, status=500)
        
        extract_dir = self.extractExtension(file_path, browser)
        if not extract_dir:
            return JsonResponse({"error": "Failed to extract extension."}, status=500)
        
        permissions = self.analyzePermissions(extract_dir)
        
        return JsonResponse({
            "extension_id": extension_id,
            "browser": browser,
            "permissions": permissions,
        })
