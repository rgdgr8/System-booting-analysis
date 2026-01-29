import paramiko  # to connect via ssh connection to the host system
from typing import Any


def _load_private_key(key_path: str) -> paramiko.PKey:
    """
    Attempt to load the private key using supported formats.
    """
    loaders = [
        paramiko.Ed25519Key.from_private_key_file,
        paramiko.RSAKey.from_private_key_file,
        paramiko.ECDSAKey.from_private_key_file,
    ]

    for loader in loaders:
        try:
            return loader(key_path)
        except Exception:
            continue

    raise ValueError("Unsupported or invalid private key format.")


def create_ssh_client(
    hostname: str,
    key_path: str,
    username: str | None = None,
) -> paramiko.SSHClient:
    """
    Create and return a connected SSH client.
    """
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    private_key = _load_private_key(key_path)

    client.connect(
        hostname=hostname,
        username=username,
        pkey=private_key,
        timeout=10,
    )

    return client


def run_command(client: paramiko.SSHClient, command: str) -> str:
    """
    Execute a command on the remote system and return stdout.
    Raises RuntimeError if stderr contains output.
    """
    stdin, stdout, stderr = client.exec_command(command)

    output = stdout.read().decode("utf-8")
    error = stderr.read().decode("utf-8")

    if error.strip():
        raise RuntimeError(f"Remote command failed: {error.strip()}")

    return output
