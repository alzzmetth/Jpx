"""
JPX Color Module
Menyediakan warna ANSI untuk typewriter/print
"""

class Colors:
    RESET = '\033[0m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    @classmethod
    def all(cls):
        return cls

# Module initialization - akan dipanggil interpreter
def __init__(interp):
    """Inisialisasi module dengan akses ke interpreter"""
    interp.modules['color'] = {
        'Colors': Colors,
        'RED': Colors.RED,
        'GREEN': Colors.GREEN,
        'BLUE': Colors.BLUE,
        # dll
    }
    return interp.modules['color']
