"""WSGI configuration for the ROCKS store on PythonAnywhere.

Copy this file's contents into the WSGI configuration file shown on the
PythonAnywhere Web tab.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path("/home/rocksev/rocks-store")

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# PythonAnywhere web workers do not inherit variables exported in a Bash
# console, so load the private production environment before importing Django.
load_dotenv(PROJECT_ROOT / ".env")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
os.environ["DEBUG"] = "False"
os.environ.setdefault("ALLOWED_HOSTS", "rocksev.pythonanywhere.com")
os.environ.setdefault("CSRF_TRUSTED_ORIGINS", "https://rocksev.pythonanywhere.com")

from django.core.wsgi import get_wsgi_application


application = get_wsgi_application()
