"""WSGI configuration for the ROCKS store on PythonAnywhere.

Copy this file's contents into the WSGI configuration file shown on the
PythonAnywhere Web tab.
"""

import os
import sys


PROJECT_ROOT = "/home/rocksev/rocks-store"

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
os.environ["DEBUG"] = "False"
os.environ.setdefault("ALLOWED_HOSTS", "rocksev.pythonanywhere.com")

from django.core.wsgi import get_wsgi_application


application = get_wsgi_application()
