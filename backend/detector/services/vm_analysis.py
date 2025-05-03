import os
import json
import paramiko
from dotenv import load_dotenv

load_dotenv()
VM_HOST = os.getenv("VM_HOST")
VM_USER = os.getenv("VM_USER")
VM_KEY = os.getenv("VM_KEY")
VM_SCRIPT = os.getenv("VM_SCRIPT")

def run_analysis_on_vm(remote_path):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=VM_HOST, username=VM_USER, key_filename=VM_KEY, timeout=10)

        cmd = f"python3 {os.path.join(VM_SCRIPT, 'extractCRX2.py')} {remote_path}"
        stdin, stdout, stderr = ssh.exec_command(cmd)

        raw_output = stdout.read().decode()
        error_output = stderr.read().decode()

        if error_output:
            return {"status": "error", "message": f"VM Error: {error_output}"}

        json_start = raw_output.find('{')
        json_end = raw_output.rfind('}') + 1

        if json_start == -1 or json_end == -1:
            return {"status": "error", "message": "Invalid JSON output"}

        result = json.loads(raw_output[json_start:json_end])
        return {"status": "success", "result": result}

    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        ssh.close()
