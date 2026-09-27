# setup_project.py (Runs on Linux, Windows 7, macOS identically)
import os

folders = [".streamlit", "src", "src/views"]
files = [
    ".streamlit/secrets.toml",
    "requirements.txt",
    "src/__init__.py",
    "src/db.py",
    "src/components.py",
    "src/views/__init__.py",
    "src/views/live_station.py",
    "src/views/daily_archive.py",
    "src/views/worker_audit.py",
    "src/views/roster_manager.py",
    "app.py"
]

for folder in folders:
    os.makedirs(folder, exist_ok=True)

for file in files:
    with open(file, "a") as f:
        pass

print("Project files created successfully!")
