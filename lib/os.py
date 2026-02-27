"""
JPX OS Module
Fungsi-fungsi sistem operasi
"""

import subprocess
import os as _os

def run(interp, command):
    """Jalankan perintah shell"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.stdout.strip()
    except Exception as e:
        return f"Error: {e}"

def get(interp, name):
    """Get environment variable"""
    return _os.environ.get(name, "")

def write(interp, path, text):
    """Write to file"""
    # text bisa berisi $variable dari JPX
    # Interpolasi dilakukan sebelum sampai sini
    with open(path, 'w') as f:
        f.write(text)
    return f"Written to {path}"

def __init__(interp):
    """Inisialisasi module"""
    interp.modules['os'] = {
        'run': run,
        'get': get,
        'write': write,
    }
    return interp.modules['os']
