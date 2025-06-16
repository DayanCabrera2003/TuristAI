import os
import hashlib
import json

def url_to_filename(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest() + ".html"

def save_html(content: str, filename: str):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)

def save_json(data: dict, filename: str):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
