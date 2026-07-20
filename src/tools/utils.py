"""
Utility tools — password generator, file encryption/decryption, system monitor.
Uses only Python standard library.
"""

import secrets
import string
import os
import platform
import subprocess
import hashlib
import base64
import struct
import time
from pathlib import Path


# ── Password generator ────────────────────────────────────────────────────────

PASSWORD_DEFINITION = {
    "type": "function",
    "function": {
        "name": "generate_password",
        "description": "Generate a cryptographically secure random password.",
        "parameters": {
            "type": "object",
            "properties": {
                "length": {
                    "type": "integer",
                    "description": "Password length. Default 20.",
                },
                "include_symbols": {
                    "type": "boolean",
                    "description": "Include special symbols. Default true.",
                },
                "count": {
                    "type": "integer",
                    "description": "Number of passwords to generate. Default 1.",
                },
            },
            "required": [],
        },
    },
}


def generate_password(
    length: int = 20,
    include_symbols: bool = True,
    count: int = 1,
) -> str:
    chars = string.ascii_letters + string.digits
    if include_symbols:
        chars += "!@#$%^&*()-_=+[]{}|;:,.<>?"

    passwords = []
    for _ in range(min(count, 20)):
        pwd = "".join(secrets.choice(chars) for _ in range(length))
        passwords.append(pwd)

    if count == 1:
        return f"Password: {passwords[0]}"
    return "Passwords:\n" + "\n".join(f"  {i+1}. {p}" for i, p in enumerate(passwords))


# ── File encryption ───────────────────────────────────────────────────────────
# Simple XOR + PBKDF2 encryption — no external deps required.

ENCRYPT_DEFINITION = {
    "type": "function",
    "function": {
        "name": "encrypt_file",
        "description": "Encrypt a file with a password. Saves encrypted file as <filename>.enc",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Path to the file to encrypt."},
                "password": {"type": "string", "description": "Encryption password."},
            },
            "required": ["file_path", "password"],
        },
    },
}

DECRYPT_DEFINITION = {
    "type": "function",
    "function": {
        "name": "decrypt_file",
        "description": "Decrypt a file that was encrypted with encrypt_file.",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Path to the .enc file to decrypt."},
                "password": {"type": "string", "description": "Decryption password."},
                "output_path": {
                    "type": "string",
                    "description": "Where to save the decrypted file. Defaults to removing .enc extension.",
                },
            },
            "required": ["file_path", "password"],
        },
    },
}

_MAGIC = b"OON1"  # file format magic bytes


def _derive_key(password: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000, dklen=32)


def _xor_crypt(data: bytes, key: bytes) -> bytes:
    key_len = len(key)
    return bytes(b ^ key[i % key_len] for i, b in enumerate(data))


def encrypt_file(file_path: str, password: str) -> str:
    try:
        src = Path(file_path)
        if not src.exists():
            return f"Error: file not found: {file_path}"

        data = src.read_bytes()
        salt = secrets.token_bytes(16)
        key = _derive_key(password, salt)
        encrypted = _xor_crypt(data, key)

        # Format: magic(4) + salt(16) + encrypted_data
        out_path = src.with_suffix(src.suffix + ".enc")
        with open(out_path, "wb") as f:
            f.write(_MAGIC + salt + encrypted)

        return f"Encrypted: {out_path}  ({len(data):,} bytes → {out_path.stat().st_size:,} bytes)"
    except Exception as e:
        return f"Error encrypting: {e}"


def decrypt_file(file_path: str, password: str, output_path: str | None = None) -> str:
    try:
        src = Path(file_path)
        if not src.exists():
            return f"Error: file not found: {file_path}"

        raw = src.read_bytes()
        if not raw.startswith(_MAGIC):
            return "Error: file does not appear to be encrypted by OPE-OPA-NATION."

        salt = raw[4:20]
        encrypted = raw[20:]
        key = _derive_key(password, salt)
        decrypted = _xor_crypt(encrypted, key)

        if output_path is None:
            # Remove last .enc extension
            name = src.name
            if name.endswith(".enc"):
                name = name[:-4]
            out_path = src.parent / name
        else:
            out_path = Path(output_path)

        out_path.write_bytes(decrypted)
        return f"Decrypted: {out_path}  ({len(decrypted):,} bytes)"
    except Exception as e:
        return f"Error decrypting: {e}"


# ── System monitor ────────────────────────────────────────────────────────────

SYSMON_DEFINITION = {
    "type": "function",
    "function": {
        "name": "system_monitor",
        "description": "Get system stats: CPU usage, RAM, disk space, uptime, OS info.",
        "parameters": {
            "type": "object",
            "properties": {
                "detail": {
                    "type": "string",
                    "enum": ["all", "cpu", "memory", "disk", "os"],
                    "description": "Which stats to show. Default 'all'.",
                },
            },
            "required": [],
        },
    },
}


def _read_proc(path: str) -> str:
    try:
        with open(path) as f:
            return f.read()
    except Exception:
        return ""


def _cpu_percent() -> str:
    """Read CPU usage from /proc/stat (Linux/Termux)."""
    try:
        s1 = _read_proc("/proc/stat")
        time.sleep(0.2)
        s2 = _read_proc("/proc/stat")

        def parse(s):
            line = [l for l in s.splitlines() if l.startswith("cpu ")][0]
            vals = list(map(int, line.split()[1:]))
            idle = vals[3]
            total = sum(vals)
            return idle, total

        i1, t1 = parse(s1)
        i2, t2 = parse(s2)
        dt = t2 - t1
        di = i2 - i1
        used = 100.0 * (dt - di) / dt if dt else 0
        return f"{used:.1f}%"
    except Exception:
        # Fallback: try top
        result = subprocess.run("top -bn1 | grep 'Cpu'", shell=True,
                                capture_output=True, text=True)
        return result.stdout.strip() or "N/A"


def _memory() -> str:
    try:
        data = _read_proc("/proc/meminfo")
        info = {}
        for line in data.splitlines():
            parts = line.split()
            if len(parts) >= 2:
                info[parts[0].rstrip(":")] = int(parts[1])
        total = info.get("MemTotal", 0)
        free  = info.get("MemAvailable", info.get("MemFree", 0))
        used  = total - free
        pct   = 100 * used / total if total else 0
        return (
            f"Total: {total//1024} MB  |  "
            f"Used: {used//1024} MB  |  "
            f"Free: {free//1024} MB  |  "
            f"{pct:.1f}% used"
        )
    except Exception:
        return "N/A"


def _disk() -> str:
    try:
        st = os.statvfs("/")
        total = st.f_frsize * st.f_blocks
        free  = st.f_frsize * st.f_bavail
        used  = total - free
        pct   = 100 * used / total if total else 0
        return (
            f"Total: {total//1024//1024//1024} GB  |  "
            f"Used: {used//1024//1024//1024} GB  |  "
            f"Free: {free//1024//1024//1024} GB  |  "
            f"{pct:.1f}% used"
        )
    except Exception:
        return "N/A"


def _uptime() -> str:
    try:
        with open("/proc/uptime") as f:
            secs = float(f.read().split()[0])
        h, rem = divmod(int(secs), 3600)
        m, s = divmod(rem, 60)
        return f"{h}h {m}m {s}s"
    except Exception:
        return "N/A"


def system_monitor(detail: str = "all") -> str:
    sections = []

    if detail in ("all", "os"):
        sections.append(
            f"OS:      {platform.system()} {platform.release()} ({platform.machine()})\n"
            f"Python:  {platform.python_version()}\n"
            f"Uptime:  {_uptime()}"
        )

    if detail in ("all", "cpu"):
        sections.append(f"CPU:     {_cpu_percent()}")

    if detail in ("all", "memory"):
        sections.append(f"RAM:     {_memory()}")

    if detail in ("all", "disk"):
        sections.append(f"Disk (/): {_disk()}")

    return "\n".join(sections)


ALL_DEFINITIONS = [
    PASSWORD_DEFINITION,
    ENCRYPT_DEFINITION,
    DECRYPT_DEFINITION,
    SYSMON_DEFINITION,
]
