import os
import sys

def get_resource_path(relative_path):
    """
    Get the absolute path to a resource. 
    Works for standard development and PyInstaller _MEIPASS temp directories.
    """
    if not relative_path:
        return ""
    try:
        # PyInstaller extracts bundled files to a temporary folder stored in sys._MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # Standard execution falls back to the local directory
        base_path = os.path.abspath(".")
        
    return os.path.join(base_path, relative_path)