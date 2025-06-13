from bs4 import BeautifulSoup
import re

def clean_text(text):
    return re.sub(r'\s+', ' ', text.strip())

def extract_links(html, base_url):
    from urllib.parse import urljoin
    soup = BeautifulSoup(html, 'lxml')
    links = set()
    for a in soup.find_all('a', href=True):
        href = a['href']
        full_url = urljoin(base_url, href)
        if ("/es/" in full_url or "cuba.travel" in full_url) and not any(lang in full_url for lang in ["/en/", "/de/", "/fr/", "/it/", "/ru/"]):
            links.add(full_url)
    return list(links)

def extract_info(html, url):
    soup = BeautifulSoup(html, 'lxml')

    # Título heurístico
    titulo = None
    for tag in ['h1', 'title', 'h2']:
        t = soup.find(tag)
        if t:
            titulo = clean_text(t.get_text())
            break

    # Evitar duplicados exactos
    fragmentos_vistos = set()
    secciones = []

    for section in soup.find_all(['section', 'article', 'div'], recursive=True):
        textos = []
        for tag in section.find_all(['h2', 'h3', 'p', 'li'], recursive=True):
            contenido = clean_text(tag.get_text())
            if contenido and len(contenido) > 30 and contenido not in fragmentos_vistos:
                textos.append(contenido)
                fragmentos_vistos.add(contenido)
        if textos:
            secciones.append({"fragmentos": textos})

    # Teléfonos y correos
    raw_text = soup.get_text()
    telefonos = re.findall(r'\+53\s?\d{1,2}\s?\d{6,7}', raw_text)
    emails = re.findall(r'\b[\w.-]+?@\w+?\.\w+?\b', raw_text)

    return {
        "url": url,
        "titulo": titulo,
        "secciones": secciones,
        "telefonos": list(set(telefonos)),
        "emails": list(set(emails))
    }
