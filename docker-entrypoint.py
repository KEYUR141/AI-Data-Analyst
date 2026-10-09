"""Migrate and collect static files, then replace this process with Gunicorn."""

import os
import subprocess
import sys

for command in ["migrate", "collectstatic"]:
    subprocess.run([sys.executable, "Project/manage.py", command, "--noinput"], check=True)
os.chdir("Project")
os.execvp(
    "gunicorn",
    [
        "gunicorn",
        "Project.wsgi:application",
        "--bind",
        "0.0.0.0:8000",
        "--workers",
        "2",
        "--threads",
        "2",
        "--timeout",
        "180",
        "--access-logfile",
        "-",
        "--error-logfile",
        "-",
    ],
)
