import sys
import os

def resource_path(relative_path):
    """Return absolute path to resource, works for dev and PyInstaller."""
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, relative_path)

def get_output_folder():
    from pathlib import Path
    output_folder = Path(os.getenv("APPDATA")) / "FragSense" / "assets"
    output_folder.mkdir(parents=True, exist_ok=True)
    return str(output_folder)