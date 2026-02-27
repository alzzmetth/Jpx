"""
JPX Print Module
Fungsi print biasa + akses ke typewriter interpreter
"""

def normal(interp, text):
    """Print biasa"""
    # Bisa panggil print Python langsung
    print(text)

def slow(interp, text):
    """Print dengan typewriter lambat"""
    # Panggil typewriter dari interpreter dengan speed kustom
    interp.typewriter(text, speed=0.1)

def fast(interp, text):
    """Print dengan typewriter cepat"""
    interp.typewriter(text, speed=0.02)

def with_color(interp, text, color):
    """Print dengan warna (color dari color module)"""
    # color bisa diakses dari interp.modules['color']
    colors = interp.modules.get('color', {})
    color_code = colors.get(color, '')
    reset = colors.get('RESET', '')
    print(f"{color_code}{text}{reset}")

def __init__(interp):
    """Inisialisasi module print"""
    interp.modules['print'] = {
        'normal': normal,
        'slow': slow,
        'fast': fast,
        'with_color': with_color,
    }
    return interp.modules['print']
