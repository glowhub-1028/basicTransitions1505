import hashlib
import os

def get_file_hash(filepath):
    with open(filepath, "rb") as f:
        file_bytes = f.read()
    return hashlib.md5(file_bytes).hexdigest()

def compute_version_hash(files_to_check):
    combined = ""
    for path in files_to_check:
        if os.path.exists(path):
            combined += get_file_hash(path)
    return hashlib.md5(combined.encode()).hexdigest()[:10]  # Short signature
