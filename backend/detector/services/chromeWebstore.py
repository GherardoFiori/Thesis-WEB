import os
import re
import json
from dotenv import load_dotenv
import subprocess
import tempfile
import zipfile
import paramiko
import requests
from urllib.parse import urlparse, parse_qs
from django.http import JsonResponse
from django.views import View


load_dotenv()

VM_HOST = os.getenv("VM_HOST")
VM_USER = os.getenv("VM_USER")
VM_KEY = os.getenv("VM_KEY")
VM_REMOTE_PATH = os.getenv("VM_REMOTE_PATH")
VM_CRX_LOC = os.getenv("VM_CRX_LOC")

def uploadToVM(local_file_path, remote_path, ssh_client):
    try:
        sftp = ssh_client.open_sftp()
        sftp.put(local_file_path, remote_path)
        sftp.close()
        return True
    except Exception as e:
        print(f"Error uploading to VM: {e}")
        return False


def getSSH():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # Automatically adds unknown host keys
    ssh.connect(VM_HOST, username= VM_USER, key_filename= VM_KEY)
    return ssh

class ExtensionAnalyzer(View):
    def getExtensionID(self, url):

        parsed_url = urlparse(url)
        # Google Chrome
        if "chrome.google.com" in parsed_url.netloc:
            match = re.search(r"detail/[^/]+/([a-zA-Z0-9_-]+)", parsed_url.path)
            if match:
                return match.group(1)
        
        elif "microsoftedge.microsoft.com" in parsed_url.netloc:
        # Microsoft Edge Add-ons
            match = re.search(r"detail/[^/]+/([a-zA-Z0-9_-]+)", parsed_url.path)
            if match:
                return match.group(1), "edge"
        
        elif "addons.mozilla.org" in parsed_url.netloc:
        # Firefox Add-ons
            query_params = parse_qs(parsed_url.query)
            addon_id = query_params.get("id", [None])[0]
            return addon_id, "firefox"
        
        elif "addons.opera.com" in parsed_url.netloc:
        # Opera Add-ons
            match = re.search(r"extensions/details/([a-zA-Z0-9_-]+)", parsed_url.path)
            if match:
                return match.group(1), "opera"

        
        return None

def downloadExtension(extension_id, browser="chrome"):
    temp_dir = tempfile.mkdtemp()
    file_extension = {
        "chrome": ".crx",
        "edge": ".crx",
        "firefox": ".xpi",
        "opera": ".crx"
    }.get(browser, ".crx")

    file_path = os.path.join(temp_dir, f"{extension_id}{file_extension}")

    if browser == "chrome":
        download_url = f"https://clients2.google.com/service/update2/crx?response=redirect&prodversion=91.0&acceptformat=crx3&x=id%3D{extension_id}%26uc"
    elif browser == "edge":
        download_url = f"https://edge.microsoft.com/extensionwebstorebase/v1/crx?response=redirect&x=id%3D{extension_id}%26uc"
    elif browser == "firefox":
        download_url = f"https://addons.mozilla.org/firefox/downloads/latest/{extension_id}/addon-latest.xpi"
    elif browser == "opera":
        # Opera just wraps Chrome extensions
        download_url = f"https://addons.opera.com/extensions/download/{extension_id}/"

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

    def get(self, request):
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
        
        
        sshClient = getSSH()
        remoteFilePath = os.path.join(VM_CRX_LOC, f"{extension_id}.crx")
        upload_success = uploadToVM(file_path, remoteFilePath, sshClient)
        
        if not upload_success:
            return JsonResponse({"error": "Failed to upload file to VM."}, status=500)
        
        return JsonResponse({
            "extension_id": extension_id,
            "browser": browser,
            "permissions": permissions,
            "remote_file_path": remoteFilePath, 
        })
