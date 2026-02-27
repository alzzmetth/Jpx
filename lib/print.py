"""
JPX Print Module
Menyediakan fungsi printing tambahan.
"""

# Import color jika tersedia (opsional)
try:
    from .color import Colors
except ImportError:
    # Fallback jika color tidak ada
    class Colors:
        RESET = ''
        RED = ''
        GREEN = ''
        BLUE = ''
        # dll dummy

def print_color(text, color_code):
    """
    Mencetak teks dengan warna tertentu.
    
    Args:
        text (str): Teks yang akan dicetak.
        color_code (str): Kode ANSI warna (misal Colors.RED).
    """
    print(f"{color_code}{text}{Colors.RESET}")

def print_box(text, width=40):
    """
    Mencetak teks dalam kotak.
    """
    line = "┌" + "─" * (width - 2) + "┐"
    print(line)
    print(f"│ {text:<{width-4}} │")
    line = "└" + "─" * (width - 2) + "┘"
    print(line)

# Fungsi lain bisa ditambahkan sesuai kebutuhan
