"""
Utilidades para manejo de archivos y nombres de archivo en el crawler.

Incluye funciones para:
- Convertir URLs a nombres de archivo únicos.
- Guardar HTML y JSON en disco.
"""
import os
import hashlib
import json

def url_to_filename(url: str) -> str:
    """
    Convierte una URL en un nombre de archivo único usando hash MD5.
    """
    return hashlib.md5(url.encode()).hexdigest() + ".html"

def save_html(content: str, filename: str):
    """
    Guarda el contenido HTML en un archivo.
    """
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)

def save_json(data: dict, filename: str):
    """
    Guarda un diccionario como archivo JSON.
    """
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
