import os
import time
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

from utils.utils import save_json

URL = "https://www.cubatravel.cu/sobre-cuba/geografia-de-cuba"
PESTANAS = ["Hoteles", "Casas", "Tours", "Campismo"]
SAVE_DIR = "./data/raw/booking/"
HTML_DEBUG_DIR = "./data/debug_html/"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("scraper.log"),
        logging.StreamHandler()
    ]
)

def scroll_and_click(driver, element):
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
    time.sleep(0.2)
    try:
        element.click()
    except Exception:
        driver.execute_script("arguments[0].click();", element)

def create_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-gpu")
    # Puedes añadir más opciones si lo necesitas
    return webdriver.Chrome(options=options)

def save_debug_html(html, pestaña, destino):
    os.makedirs(HTML_DEBUG_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(
        HTML_DEBUG_DIR, f"{pestaña}_{destino}_{timestamp}.html".replace(" ", "_")
    )
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)
    logging.info(f"HTML de depuración guardado en: {filename}")

def extract_result_cards(soup):
    # Intenta varios selectores para máxima robustez
    selectors = [
        ".row.pb15",  # Selector más común en CubaTravel
        ".card-hotel, .card-house, .card-tour, .card-campismo",
        ".hotel-card", ".house-card", ".tour-card", ".campismo-card"
    ]
    for selector in selectors:
        cards = soup.select(selector)
        if cards:
            return cards
    return []

def extract_card_data(card):
    # Intenta extraer los campos más relevantes de cada tarjeta
    def safe_text(selector):
        elem = card.select_one(selector)
        return elem.text.strip() if elem else ""
    nombre = safe_text(".htl-card-body h3.media-heading a") or \
             safe_text(".card-title") or \
             safe_text(".nombre") or \
             safe_text("h5") or \
             safe_text("h3")
    descripcion = safe_text(".description .truncateDescription span") or \
                  safe_text(".card-text") or \
                  safe_text(".descripcion") or \
                  safe_text("p")
    direccion = safe_text(".address") or safe_text(".direccion")
    tarifa = safe_text(".tarifa") or safe_text(".rate")
    precio = safe_text(".price") or safe_text(".media-price p")
    estrellas = len(card.select(".glyphicon-star"))
    return {
        "nombre": nombre,
        "descripcion": descripcion,
        "direccion": direccion,
        "tarifa": tarifa,
        "precio": precio,
        "estrellas": estrellas
    }

def scrape():
    os.makedirs(SAVE_DIR, exist_ok=True)
    driver = create_driver()
    wait = WebDriverWait(driver, 20)
    logging.info("Abriendo página principal...")
    driver.get(URL)
    time.sleep(3)

    # Cierra el banner de cookies si aparece
    try:
        cookie_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".cc-window .cc-btn, .cc-window button"))
        )
        cookie_btn.click()
        time.sleep(1)
        logging.info("Banner de cookies cerrado.")
    except Exception:
        logging.info("No se encontró banner de cookies o ya está cerrado.")

    for pestaña in PESTANAS:
        logging.info(f"Procesando pestaña: {pestaña}")
        try:
            tab_btn = wait.until(EC.element_to_be_clickable(
                (By.XPATH, f"//span[contains(text(), '{pestaña}')]/ancestor::a")))
            scroll_and_click(driver, tab_btn)
            time.sleep(2)
        except Exception as e:
            logging.error(f"No se pudo hacer clic en la pestaña {pestaña}: {e}")
            continue

        # Abre el selector de destinos
        try:
            flecha = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".multiselect__select")))
            scroll_and_click(driver, flecha)
            wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".multiselect__option")))
            time.sleep(1)
        except Exception as e:
            logging.error(f"No se pudo abrir el selector en {pestaña}: {e}")
            continue

        # Obtén todas las opciones de destino
        opciones = driver.find_elements(By.CSS_SELECTOR, ".multiselect__option:not(.multiselect__option--group):not(.multiselect__option--disabled)")
        destinos = [op.text.strip() for op in opciones if op.text.strip()]
        logging.info(f"Destinos encontrados en {pestaña}: {destinos}")

        for destino in destinos:
            logging.info(f"Procesando destino: {destino}")

            # Vuelve a la página principal antes de cada destino
            driver.get(URL)
            time.sleep(2)
            # Reabrir la pestaña correspondiente
            try:
                tab_btn = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, f"//span[contains(text(), '{pestaña}')]/ancestor::a")))
                scroll_and_click(driver, tab_btn)
                time.sleep(1)
            except Exception as e:
                logging.error(f"No se pudo volver a la pestaña {pestaña}: {e}")
                continue

            try:
                # Selecciona el destino
                flecha = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".multiselect__select")))
                scroll_and_click(driver, flecha)
                wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".multiselect__option")))
                xpath = f"//span[contains(@class, 'multiselect__option') and span[normalize-space(text())='{destino}']]"
                try:
                    opcion_span = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
                    scroll_and_click(driver, opcion_span)
                    time.sleep(0.5)
                except Exception as e:
                    logging.warning(f"No se encontró/clickeó la opción '{destino}': {e}")
                    continue
            except Exception as e:
                logging.error(f"No se pudo seleccionar destino {destino} en {pestaña}: {e}")
                continue

            # Haz clic en el botón Buscar
            try:
                buscar_btn = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(@class, 'btn-primary') and contains(., 'Buscar')]")))
                scroll_and_click(driver, buscar_btn)
                logging.info("Botón Buscar pulsado, esperando resultados...")
            except Exception as e:
                logging.error(f"No se pudo hacer clic en Buscar en {pestaña} - {destino}: {e}")
                continue

            # Espera a que la URL cambie y luego a que cargue la zona de resultados
            try:
                wait.until(lambda d: "/Hotel/Search" in d.current_url)
                logging.info("Redirección detectada, esperando resultados...")
                wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".row.pb15, .card-hotel, .card-house, .card-tour, .card-campismo"))
                )
                time.sleep(2)
            except Exception as e:
                logging.warning(f"No se detectaron resultados visibles para {pestaña} - {destino}: {e}")

            # NUEVO: Mostrar la URL después de buscar
            current_url = driver.current_url
            logging.info(f"URL después de buscar: {current_url}")
            print(f"[DEBUG] URL después de buscar: {current_url}")

            html = driver.page_source
            save_debug_html(html, pestaña, destino)
            soup = BeautifulSoup(html, "html.parser")
            resultados = []

            # DEBUG: imprime cuántos elementos encuentra cada selector
            selectors = [
                ".row.pb15",
                ".card-hotel, .card-house, .card-tour, .card-campismo",
                ".hotel-card", ".house-card", ".tour-card", ".campismo-card"
            ]
            for selector in selectors:
                found = soup.select(selector)
                print(f"[DEBUG] Selector '{selector}' encontró {len(found)} elementos.")

            cards = extract_result_cards(soup)
            logging.info(f"Se encontraron {len(cards)} tarjetas de resultados para {pestaña} - {destino}")
            if len(cards) == 0:
                print("[DEBUG] No se encontraron tarjetas de resultados. Revisa el HTML guardado para ver la estructura real.")

            for i, card in enumerate(cards):
                data = extract_card_data(card)
                print(f"[DEBUG] Card {i}: {data}")
                if data["nombre"]:  # Solo guarda si hay nombre
                    resultados.append(data)

            # Guarda en JSON
            filename = os.path.join(SAVE_DIR, f"{pestaña}_{destino}.json".replace(" ", "_"))
            save_json(resultados, filename)
            logging.info(f"Guardado: {filename} ({len(resultados)} resultados)")

    driver.quit()
    logging.info("Scraping de pestañas y destinos completado.")

if __name__ == "__main__":
    scrape()