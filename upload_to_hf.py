"""Upload SQLOps project to Hugging Face Space."""
import os
from huggingface_hub import HfApi

api = HfApi()
SPACE_ID = "JOHNMAMBA990/sqlops-hackmeta"
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

# All files to upload (relative paths)
files_to_upload = []
skip_dirs = {'.git', '__pycache__', '.venv', 'venv', '.idea', '.vscode'}
skip_exts = {'.pyc', '.pyo', '.db', '.sqlite3'}

for root, dirs, files in os.walk(PROJECT_DIR):
    # Skip hidden/build dirs
    dirs[:] = [d for d in dirs if d not in skip_dirs]
    for f in files:
        if f == 'upload_to_hf.py':
            continue
        ext = os.path.splitext(f)[1]
        if ext in skip_exts:
            continue
        full_path = os.path.join(root, f)
        rel_path = os.path.relpath(full_path, PROJECT_DIR).replace('\\', '/')
        files_to_upload.append((full_path, rel_path))

print(f"Uploading {len(files_to_upload)} files to {SPACE_ID}...")
for full_path, rel_path in files_to_upload:
    print(f"  -> {rel_path}")

# Upload all at once
api.upload_folder(
    folder_path=PROJECT_DIR,
    repo_id=SPACE_ID,
    repo_type="space",
    ignore_patterns=[
        ".git/*", "__pycache__/*", "*.pyc", "*.db",
        "*.sqlite3", "upload_to_hf.py"
    ],
)
print(f"\n✅ Done! Space URL: https://huggingface.co/spaces/{SPACE_ID}")
