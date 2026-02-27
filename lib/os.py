"""
JPX OS Module
Fungsi:
  - run(command)       : menjalankan perintah shell
  - get(name)          : mendapatkan environment variable
  - write(path, text)  : menulis teks ke file
"""

import subprocess
import os as _os

def run(command):
    """
    Menjalankan perintah shell.
    
    Args:
        command (str): Perintah yang akan dijalankan.
    
    Returns:
        str: Output stdout dari perintah.
    
    Example:
        os.run("mkdir folder_baru")
        os.run("ls -la")
    """
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            return f"ERROR: {result.stderr.strip()}"
        return result.stdout.strip()
    except Exception as e:
        return f"EXCEPTION: {str(e)}"

def get(name):
    """
    Mendapatkan nilai environment variable.
    
    Args:
        name (str): Nama variable (misal: "HOME", "PATH").
    
    Returns:
        str: Nilai variable, atau string kosong jika tidak ada.
    """
    return _os.environ.get(name, "")

def write(path, text):
    """
    Menulis teks ke file.
    
    Args:
        path (str): Path file tujuan.
        text (str): Teks yang akan ditulis.
    
    Returns:
        str: Pesan sukses atau error.
    """
    try:
        # Interpolasi $text? Biar JPX yang handle, di sini text sudah string final.
        with open(path, 'w', encoding='utf-8') as f:
            f.write(text)
        return f"Berhasil menulis ke {path}"
    except Exception as e:
        return f"Gagal menulis: {str(e)}"
