import os
import sys


def get_project_root() -> str:
    """Returns the writable project/application root directory."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


def get_data_dir() -> str:
    """Returns the writable root data/ directory, creating it if needed."""
    data_dir = os.path.join(get_project_root(), "data")
    os.makedirs(data_dir, exist_ok=True)
    return data_dir


def get_db_path() -> str:
    """Returns the absolute path to data/projectbb.db."""
    return os.path.join(get_data_dir(), "projectbb.db")


def get_assets_dir() -> str:
    """Returns the absolute path to the writable assets directory."""
    return os.path.join(get_project_root(), "assets")


def get_resource_path(relative_path: str) -> str:
    """
    Resolves asset paths for both standard execution and PyInstaller bundles.
    Checks the writable application root first so runtime-added images resolve properly.
    """
    if not relative_path:
        return ""

    local_path = os.path.join(get_project_root(), relative_path)
    if os.path.exists(local_path):
        return local_path

    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = get_project_root()

    return os.path.join(base_path, relative_path)