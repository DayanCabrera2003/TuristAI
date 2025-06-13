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
from .utils.utils import save_json, url_to_filename
from .utils.extractor import extract_links, extract_info
from .utils.config import START_URLS as CONFIG_START_URLS, MAX_DEPTH, SAVE_PATH, HEADLESS

import argparse

# Cambia aquí para usar DuckDuckGo en vez de Google
try:
    from duckduckgo_search import DDGS
except ImportError:
    DDGS = None

# ========== CONFIGURACIÓN DE LOGGING ==========
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# ========== GESTIÓN DE ESTADO COMPARTIDO ==========
class CrawlerState:
    def __init__(self, seeds, per_seed_limit):
        self.visited = set()
        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        self.seed_counts = defaultdict(int)  # archivos descargados por semilla
        self.seed_limits = {seed: per_seed_limit for seed in seeds}
        self.seed_map = {}  # url -> semilla original
        self.seeds = seeds

    def already_visited(self, url):
        with self.lock:
            return url in self.visited

    def add_visited(self, url):
        with self.lock:
            self.visited.add(url)

    def assign_seed(self, url):
        # Asigna la semilla original a cada url (por prefijo más largo)
        for seed in sorted(self.seeds, key=len, reverse=True):
            if url.startswith(seed):
                self.seed_map[url] = seed
                return seed
        # fallback: por dominio
        domain = urlparse(url).netloc
        for seed in self.seeds:
            if domain in seed:
                self.seed_map[url] = seed
                return seed
        self.seed_map[url] = self.seeds[0]
        return self.seeds[0]

    def can_download(self, url):
        seed = self.seed_map.get(url)
        if seed is None:
            return False
        with self.lock:
            return self.seed_counts[seed] < self.seed_limits[seed]

    def increment_seed(self, url):
        seed = self.seed_map.get(url)
        if seed:
            with self.lock:
                self.seed_counts[seed] += 1

    def all_seeds_completed(self):
        with self.lock:
            return all(self.seed_counts[seed] >= self.seed_limits[seed] for seed in self.seeds)

    def redistribute_limits(self):
        # Si alguna semilla no llegó a su límite, reparte el sobrante entre las demás
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

# ========== CONFIGURACIÓN DE DRIVERS ==========
def create_driver():
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

# ========== VALIDACIÓN Y NORMALIZACIÓN DE URLS ==========
def normalize_url(base_url, link):
    return urljoin(base_url, link)

def is_valid_url(url):
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)

def filter_links(links, base_url, allowed_domains):
    filtered = set()
    for link in links:
        norm = normalize_url(base_url, link)
        if is_valid_url(norm):
            domain = urlparse(norm).netloc
            if any(domain.endswith(ad) for ad in allowed_domains):
                filtered.add(norm)
    return filtered

def get_allowed_domains(urls):
    return {urlparse(url).netloc for url in urls}

# ========== NÚCLEO DE CRAWLEO ==========
def interact_with_dynamic_content(driver):
    import selenium.common.exceptions
    import time
    from selenium.webdriver.common.by import By

    # Scroll hasta el fondo varias veces para lazy-load
    last_height = driver.execute_script("return document.body.scrollHeight")
    for _ in range(5):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1.5)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    # Haz clic en botones de "ver más", "cargar más", etc.
    button_texts = ["ver más", "cargar más", "load more", "mostrar más", "más resultados", "show more"]
    for _ in range(5):  # Intenta varias veces por si aparecen más botones
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

    # Espera un poco más por si hay contenido dinámico
    time.sleep(1.5)

def process_page(url, depth, state, allowed_domains, seed, driver=None):
    if state.stop_event.is_set():
        return None, []

    try:
        # Sitios dinámicos (Selenium)
        if ("alamesacuba" in url or "la-habana" in url) and driver:
            driver.get(url)
            time.sleep(2)
            interact_with_dynamic_content(driver)
            html = driver.page_source
            logging.info(f"[D] [{state.seed_counts[seed]+1}/{state.seed_limits[seed]}] {url}")
        # Sitios estáticos (Requests)
        else:
            session = requests.Session()
            headers = {'User-Agent': UserAgent().random}
            response = session.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            html = response.text
            logging.info(f"[S] [{state.seed_counts[seed]+1}/{state.seed_limits[seed]}] {url}")

        # Procesamiento común
        info = extract_info(html, url)
        # --- MODIFICACIÓN PARA GUARDAR EN CRAWLEO DINAMICO ---
        if hasattr(state, "dynamic_mode") and state.dynamic_mode:
            folder_name = "crawleo_dinamico"
        else:
            folder_name = urlparse(seed).netloc.replace('.', '_')
        save_dir = os.path.join(SAVE_PATH, folder_name)
        os.makedirs(save_dir, exist_ok=True)
        filename = os.path.join(save_dir, url_to_filename(url).replace('.html', '.json'))
        save_json(info, filename)

        # Extraer y filtrar enlaces SOLO del HTML extraído
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
    seeds = start_urls if start_urls is not None else CONFIG_START_URLS
    per_seed_limit = 2000
    state = CrawlerState(seeds, per_seed_limit)
    state.dynamic_mode = dynamic_mode  # <--- NUEVO
    task_queue = queue.Queue()
    allowed_domains = get_allowed_domains(seeds)
    # Permitir sobreescribir la profundidad máxima
    depth_limit = max_depth if max_depth is not None else MAX_DEPTH

    # Inicializar cola con URLs semilla
    for seed in seeds:
        task_queue.put((seed, 0, seed))
        state.seed_map[seed] = seed

    def worker():
        thread_id = threading.get_ident()
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

                # Solo crea el driver si es necesario
                if ("alamesacuba" in url or "la-habana" in url) and driver is None:
                    driver = create_driver()

                _, new_links = process_page(url, depth, state, allowed_domains, seed, driver)

                state.increment_seed(url)

                # Solo sigue enlaces si la profundidad lo permite
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
    try:
        for _ in range(min(12, len(seeds)*2)):
            t = threading.Thread(target=worker)
            t.start()
            threads.append(t)

        task_queue.join()
    except KeyboardInterrupt:
        logging.warning("Interrupción manual recibida. Deteniendo crawler...")
        state.stop_event.set()
    finally:
        for t in threads:
            t.join(timeout=2)

    # Redistribuir si alguna semilla no llegó a su límite
    state.redistribute_limits()

    return state

# ========== EJECUCIÓN ==========
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Crawler de turismo")
    parser.add_argument("--query", type=str, help="Consulta para buscar en la web")
    args = parser.parse_args()

    if args.query:
        if DDGS is None:
            logging.error("El paquete duckduckgo-search no está instalado. Instálalo con: pip install duckduckgo-search")
            sys.exit(1)
        logging.info(f"Realizando búsqueda web para: {args.query}")
        dynamic_start_urls = []
        with DDGS() as ddgs:
            for r in ddgs.text(args.query, region='wt-wt', safesearch='Moderate', max_results=10):
                dynamic_start_urls.append(r['href'])
        if not dynamic_start_urls:
            logging.error("No se encontraron resultados para la consulta.")
            sys.exit(1)
        # Solo profundidad 0 para búsquedas rápidas
        start_time = time.time()
        state = parallel_crawler(start_urls=dynamic_start_urls, dynamic_mode=True, max_depth=0)
        elapsed = time.time() - start_time
        for seed in dynamic_start_urls:
            logging.info(f"Semilla: {seed} - Archivos descargados: {state.seed_counts[seed]}/{state.seed_limits[seed]}")
        logging.info(f"Crawleo completado en {elapsed:.2f} segundos")
    else:
        start_time = time.time()
        logging.info("Iniciando crawler por semillas...")
        state = parallel_crawler()
        elapsed = time.time() - start_time
        for seed in CONFIG_START_URLS:
            logging.info(f"Semilla: {seed} - Archivos descargados: {state.seed_counts[seed]}/{state.seed_limits[seed]}")
        logging.info(f"Crawleo completado en {elapsed:.2f} segundos")