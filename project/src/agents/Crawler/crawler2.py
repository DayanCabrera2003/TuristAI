"""
Modulo principal del crawler de turismo.
Este crawler te permite:
-Realizar crawling sobre sitios turisticos definidos.
-Usar crawling dinamico o crawling tradicional (Selenium).
-Guardar los resultados en archivos JSON.

El modo dinamico esta optimizaado para velocidad y no usa Selenium.
"""
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import queue
import threading
import time
import requests
import logging
from urllib.parse import urlparse, urljoin
from collections import defaultdict
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from Crawler.utils.utils import save_json, url_to_filename
from Crawler.utils.extractor import extract_links, extract_info
from Crawler.utils.config import START_URLS as CONFIG_START_URLS, MAX_DEPTH, SAVE_PATH, HEADLESS

import argparse

try:
    from duckduckgo_search import DDGS
except ImportError:
    DDGS = None

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

class CrawlerState:
    """
    Clase que maniente el estado del Crawling: 
    -URLs visitadas
    -Limites por semilla
    -Conteo de descargas por semilla
    -Sicronizacion entre hilos
    """
    def __init__(self, seeds, per_seed_limit):
        self.visited = set()
        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        self.seed_counts = defaultdict(int)
        self.seed_limits = {seed: per_seed_limit for seed in seeds}
        self.seed_map = {}
        self.seeds = seeds

    def already_visited(self, url):
        """Verifica si una URL ya fue visitada."""
        with self.lock:
            return url in self.visited

    def add_visited(self, url):
        """Marca una URL como visitada."""
        with self.lock:
            self.visited.add(url)

    def assign_seed(self, url):
        """
        Asigna una semilla a una URLcoincidencia de prefijo o dominio.
        Esto permite controlar los limites de descarga por grupo de URLs
        """
        for seed in sorted(self.seeds, key=len, reverse=True):
            if url.startswith(seed):
                self.seed_map[url] = seed
                return seed
        domain = urlparse(url).netloc
        for seed in self.seeds:
            if domain in seed:
                self.seed_map[url] = seed
                return seed
        self.seed_map[url] = self.seeds[0]
        return self.seeds[0]

    def can_download(self, url):
        """Verifica si aun se puede descargar mas contenido para la semilla de la URL"""
        seed = self.seed_map.get(url)
        if seed is None:
            return False
        with self.lock:
            return self.seed_counts[seed] < self.seed_limits[seed]

    def increment_seed(self, url):
        """Incrementa el contador de descargas para la semilla de la URL."""
        seed = self.seed_map.get(url)
        if seed:
            with self.lock:
                self.seed_counts[seed] += 1

    def all_seeds_completed(self):
        """Verifica si todas las semillas alcanzaron su límite de descargas."""
        with self.lock:
            return all(self.seed_counts[seed] >= self.seed_limits[seed] for seed in self.seeds)

    def redistribute_limits(self):
        """
        Redistribuye los límites de descarga entre semillas si alguna terminó antes,
        para aprovechar el máximo de descargas permitido.
        """
        with self.lock:
            total_expected = sum(self.seed_limits.values())
            total_downloaded = sum(self.seed_counts.values())
            leftover = total_expected - total_downloaded
            if leftover > 0:
                incomplete = [seed for seed in self.seeds if self.seed_counts[seed] < self.seed_limits[seed]]
                if incomplete:
                    extra = leftover // len(incomplete)
                    for seed in incomplete:
                        self.seed_limits[seed] += extra

def create_driver():
    """
    Crea una instancia de Selenium WebDriver con opciones configuradas para crawling.
    Solo se usa en crawling tradicional (no en modo dinámico).
    """
    options = Options()
    if HEADLESS:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    ua = UserAgent().random
    options.add_argument(f"user-agent={ua}")
    return webdriver.Chrome(options=options)

def normalize_url(base_url, link):
    """Normaliza un enlace relativo a absoluto usando la URL base."""
    return urljoin(base_url, link)

def is_valid_url(url):
    """Verifica si una URL es válida (http/https y con dominio)."""
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)

def filter_links(links, base_url, allowed_domains):
    """
    Filtra los enlaces extraídos para quedarse solo con los que pertenecen a los dominios permitidos.
    """
    filtered = set()
    for link in links:
        norm = normalize_url(base_url, link)
        if is_valid_url(norm):
            domain = urlparse(norm).netloc
            if domain.endswith("varaderoguide.net") or domain.endswith("solwayscuba.com"):
                filtered.add(norm)
            elif any(domain.endswith(ad) for ad in allowed_domains):
                filtered.add(norm)
    return filtered

def get_allowed_domains(urls):
    """Obtiene el conjunto de dominios permitidos a partir de las URLs semilla."""
    return {urlparse(url).netloc for url in urls}

def interact_with_dynamic_content(driver):
    """
    Interactúa con la página usando Selenium para cargar contenido dinámico:
    - Hace scroll hasta el fondo varias veces.
    - Intenta hacer click en botones de 'ver más', 'cargar más', etc.
    Solo se usa en crawling tradicional.
    """
    import selenium.common.exceptions
    import time
    from selenium.webdriver.common.by import By

    last_height = driver.execute_script("return document.body.scrollHeight")
    for _ in range(5):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1.5)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    button_texts = ["ver más", "cargar más", "load more", "mostrar más", "más resultados", "show more"]
    for _ in range(5):
        clicked = False
        for text in button_texts:
            try:
                buttons = driver.find_elements(By.XPATH, f"//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÜ', 'abcdefghijklmnopqrstuvwxyzáéíóúü'), '{text}')]")
                for btn in buttons:
                    if btn.is_displayed() and btn.is_enabled():
                        btn.click()
                        time.sleep(1.5)
                        clicked = True
            except selenium.common.exceptions.StaleElementReferenceException:
                continue
            except Exception:
                continue
        if not clicked:
            break
    time.sleep(1.5)

def process_page(url, depth, state, allowed_domains, seed, driver=None):
    """
    Descarga y procesa una página:
    - Usa requests en modo dinámico (rápido, sin Selenium).
    - Usa requests o Selenium en modo tradicional.
    - Extrae información y enlaces, guarda resultados en JSON.
    """
    if state.stop_event.is_set():
        return None, []

    try:
        # SOLO usar requests en modo dinámico (sin Selenium)
        if hasattr(state, "dynamic_mode") and state.dynamic_mode:
            session = requests.Session()
            headers = {'User-Agent': UserAgent().random}
            response = session.get(url, headers=headers, timeout=5)
            response.raise_for_status()
            html = response.text
            logging.info(f"[S] [{state.seed_counts[seed]+1}/{state.seed_limits[seed]}] {url}")
        else:
            if ("alamesacuba" in url or "la-habana" in url) and driver:
                driver.get(url)
                time.sleep(2)
                interact_with_dynamic_content(driver)
                html = driver.page_source
                logging.info(f"[D] [{state.seed_counts[seed]+1}/{state.seed_limits[seed]}] {url}")
            else:
                session = requests.Session()
                headers = {'User-Agent': UserAgent().random}
                response = session.get(url, headers=headers, timeout=15)
                response.raise_for_status()
                html = response.text
                logging.info(f"[S] [{state.seed_counts[seed]+1}/{state.seed_limits[seed]}] {url}")

        info = extract_info(html, url)
        base_dir = os.path.dirname(os.path.abspath(__file__))
        if hasattr(state, "dynamic_mode") and state.dynamic_mode:
            agents_dir = os.path.abspath(os.path.join(base_dir, ".."))
            save_dir = os.path.join(agents_dir, "data_dynamic")
        else:
            save_dir = os.path.join(agents_dir, "data", urlparse(seed).netloc.replace('.', '_'))
        os.makedirs(save_dir, exist_ok=True)
        filename = os.path.join(save_dir, url_to_filename(url).replace('.html', '.json'))
        save_json(info, filename)

        raw_links = extract_links(html, url)
        new_links = filter_links(raw_links, url, allowed_domains)
        return info, new_links

    except Exception as e:
        logging.error(f"Error en {url}: {str(e)[:100]}...")
        return None, []
    finally:
        if 'session' in locals():
            session.close()

def parallel_crawler(start_urls=None, dynamic_mode=False, max_depth=None):
    """
    Ejecuta el crawling en paralelo usando múltiples hilos.
    - Si dynamic_mode=True, solo usa requests y timeout global de 5 segundos.
    - Si dynamic_mode=False, puede usar Selenium para ciertos dominios.
    """
    seeds = start_urls if start_urls is not None else CONFIG_START_URLS
    per_seed_limit = 2000
    state = CrawlerState(seeds, per_seed_limit)
    state.dynamic_mode = dynamic_mode
    task_queue = queue.Queue()
    allowed_domains = get_allowed_domains(seeds)
    depth_limit = max_depth if max_depth is not None else MAX_DEPTH

    for seed in seeds:
        task_queue.put((seed, 0, seed))
        state.seed_map[seed] = seed

    def worker():
        """
        Función de cada hilo de crawling.
        Descarga páginas, extrae info y nuevos enlaces, respeta límites y profundidad.
        """
        driver = None
        try:
            while not state.stop_event.is_set():
                try:
                    url, depth, seed = task_queue.get(timeout=1)
                except queue.Empty:
                    break

                if depth > depth_limit or state.assign_seed(url) != seed or state.already_visited(url):
                    task_queue.task_done()
                    continue

                if not state.can_download(url):
                    task_queue.task_done()
                    continue

                state.add_visited(url)

                # Solo usar Selenium si NO es modo dinámico
                if not (hasattr(state, "dynamic_mode") and state.dynamic_mode):
                    if ("alamesacuba" in url or "la-habana" in url) and driver is None:
                        driver = create_driver()

                _, new_links = process_page(url, depth, state, allowed_domains, seed, driver)

                state.increment_seed(url)

                if new_links and depth < depth_limit:
                    for link in new_links:
                        if not state.already_visited(link):
                            task_queue.put((link, depth + 1, seed))

                task_queue.task_done()

                if state.seed_counts[seed] >= state.seed_limits[seed]:
                    continue

                if state.all_seeds_completed():
                    state.stop_event.set()
        finally:
            if driver:
                driver.quit()

    threads = []
    crawl_timeout = 5 if dynamic_mode else None
    stop_timer = None
    try:
        if crawl_timeout:
            stop_timer = threading.Timer(crawl_timeout, state.stop_event.set)
            stop_timer.start()
        for _ in range(min(12, len(seeds)*2)):
            t = threading.Thread(target=worker)
            t.start()
            threads.append(t)

        if crawl_timeout:
            # Espera hasta que el timeout expire o la cola esté vacía
            start = time.time()
            while time.time() - start < crawl_timeout + 1:
                if task_queue.unfinished_tasks == 0:
                    break
                time.sleep(0.1)
        else:
            task_queue.join()
    except KeyboardInterrupt:
        logging.warning("Interrupción manual recibida. Deteniendo crawler...")
        state.stop_event.set()
    finally:
        for t in threads:
            t.join(timeout=2)
        if stop_timer:
            stop_timer.cancel()

    state.redistribute_limits()
    return state

def run_crawler(query=None, start_urls=None, max_depth=None, dynamic_mode=False):
    """
    Ejecuta el crawler de forma programática.
    - query: consulta de búsqueda (usa DuckDuckGo si se provee)
    - start_urls: lista de URLs semilla (ignorado si query está presente)
    - max_depth: profundidad máxima de crawleo
    - dynamic_mode: si True, guarda en carpeta 'dinamic-crawler'
    """
    if query:
        if DDGS is None:
            logging.error("El paquete duckduckgo-search no está instalado. Instálalo con: pip install duckduckgo-search")
            return None
        logging.info(f"Realizando búsqueda web para: {query}")
        dynamic_start_urls = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, region='wt-wt', safesearch='Moderate', max_results=2):  # Limita a 2 resultados
                dynamic_start_urls.append(r['href'])
        if not dynamic_start_urls:
            logging.error("No se encontraron resultados para la consulta.")
            return None
        start_time = time.time()
        # Profundidad 0: solo la página principal
        state = parallel_crawler(start_urls=dynamic_start_urls, dynamic_mode=True, max_depth=0)
        elapsed = time.time() - start_time
        for seed in dynamic_start_urls:
            logging.info(f"Semilla: {seed} - Archivos descargados: {state.seed_counts[seed]}/{state.seed_limits[seed]}")
        logging.info(f"Crawleo completado en {elapsed:.2f} segundos")
        return state
    else:
        start_time = time.time()
        logging.info("Iniciando crawler por semillas...")
        state = parallel_crawler(start_urls=start_urls, dynamic_mode=dynamic_mode, max_depth=max_depth)
        elapsed = time.time() - start_time
        seeds = start_urls if start_urls is not None else CONFIG_START_URLS
        for seed in seeds:
            logging.info(f"Semilla: {seed} - Archivos descargados: {state.seed_counts[seed]}/{state.seed_limits[seed]}")
        logging.info(f"Crawleo completado en {elapsed:.2f} segundos")
        return state

if __name__ == "__main__":
    """
    Permite ejecutar el crawler desde línea de comandos.
    Ejemplo:
        python crawler2.py --query "lugares turísticos en La Habana" --max_depth 2
    """
    parser = argparse.ArgumentParser(description="Crawler de turismo")
    parser.add_argument("--query", type=str, help="Consulta para buscar en la web")
    parser.add_argument("--max_depth", type=int, help="Profundidad máxima de crawleo")
    args = parser.parse_args()

    run_crawler(query=args.query, max_depth=args.max_depth)