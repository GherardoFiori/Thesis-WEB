import os
import paramiko
from scp import SCPClient
from dotenv import load_dotenv

load_dotenv()
VM_HOST = os.getenv("VM_HOST")
VM_USER = os.getenv("VM_USER")
VM_KEY = os.getenv("VM_KEY")

def transfer_to_vm(local_path, remote_path):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        pkey = paramiko.RSAKey(filename=VM_KEY)

        ssh.connect(hostname=VM_HOST, username=VM_USER, pkey=pkey, timeout=10)

        ssh.exec_command(f"mkdir -p {os.path.dirname(remote_path)}")

        with SCPClient(ssh.get_transport()) as scp:
            scp.put(local_path, remote_path)

        stdin, stdout, stderr = ssh.exec_command(f"ls {remote_path}")
        if not stdout.read().decode().strip():
            raise Exception("File not found on VM")

        return True
    except Exception as e:
        print(f"Transfer error: {e}")
        return False
    finally:
        ssh.close()
