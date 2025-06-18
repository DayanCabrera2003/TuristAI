"""
Scrapper de pestañas y destinos para cubatravel.cu.

Este script automatiza la extracción de información de diferentes pestañas (Hoteles, Casas, Tours, etc.)
y sus destinos en el sitio web cubatravel.cu, usando Selenium para interactuar con la interfaz dinámica.
Guarda los resultados en archivos JSON y HTML de depuración para análisis posterior.

Características:
- Navega por cada pestaña y destino, seleccionando opciones en menús desplegables.
- Extrae tarjetas de resultados y sus detalles.
- Guarda HTML de depuración para facilitar troubleshooting.
- Enriquecer la descripción de cada resultado accediendo a su enlace.
"""
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

URL = "https://www.cubatravel.cu/"
PESTANAS = [
     "Hoteles", "Casas", "Tours", "Traslados", "Eventos", "Campismo", "Salud", "Seguros"
]
DATA_FORMULARIO_DIR = os.path.join(os.path.dirname(__file__), "data_formulario")
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
    """
    Hace scroll hasta el elemento y realiza un click robusto usando Selenium.
    Si el click normal falla, intenta con JavaScript.
    """
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
    time.sleep(0.2)
    try:
        element.click()
    except Exception:
        driver.execute_script("arguments[0].click();", element)

def create_driver():
    """
    Crea y configura una instancia de Selenium WebDriver en modo headless.
    """
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-gpu")
    return webdriver.Chrome(options=options)

def save_debug_html(html, pestaña, destino):
    """
    Guarda el HTML de la página actual para depuración, incluyendo pestaña y destino en el nombre.
    """
    os.makedirs(HTML_DEBUG_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(
        HTML_DEBUG_DIR, f"{pestaña}_{destino}_{timestamp}.html".replace(" ", "_")
    )
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)
    logging.info(f"HTML de depuración guardado en: {filename}")

def extract_result_cards(soup):
    """
    Extrae las tarjetas de resultados de la página usando varios selectores posibles.
    Devuelve una lista de elementos BeautifulSoup.
    """
    selectors = [
        ".row.pb15",
        ".card-hotel, .card-house, .card-tour, .card-campismo",
        ".hotel-card", ".house-card", ".tour-card", ".campismo-card"
    ]
    for selector in selectors:
        cards = soup.select(selector)
        if cards:
            return cards
    return []

def extract_card_data(card):
    """
    Extrae los datos relevantes de una tarjeta de resultado:
    nombre, descripción, dirección, tarifa, precio, estrellas y enlace.
    """
    def safe_text(selector):
        elem = card.select_one(selector)
        return elem.text.strip() if elem else ""
    def safe_link(selector):
        elem = card.select_one(selector)
        return elem['href'] if elem and elem.has_attr('href') else ""
    nombre_elem = card.select_one(".htl-card-body h3.media-heading a") or \
                  card.select_one(".card-title a") or \
                  card.select_one("a")
    nombre = nombre_elem.text.strip() if nombre_elem else \
             safe_text(".card-title") or safe_text(".nombre") or safe_text("h5") or safe_text("h3")
    enlace = nombre_elem['href'] if nombre_elem and nombre_elem.has_attr('href') else ""
    descripcion = safe_text(".description .truncateDescription span") or \
                  safe_text(".card-text") or safe_text(".descripcion") or safe_text("p")
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
        "estrellas": estrellas,
        "enlace": enlace
    }

def save_json_with_destino(data, filepath, destino):
    """
    Guarda los resultados en un archivo JSON, precedido por el nombre del destino.
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"Destino: {destino}\n")
        import json
        json.dump(data, f, ensure_ascii=False, indent=2)

def click_tab(driver, wait, pestaña):
    """
    Hace clic en la pestaña especificada usando su nombre visible.
    Espera a que el elemento esté presente y visible.
    """
    span_xpath = f"//li[contains(@class, 'buttons-tabs-booking')]/a/span[normalize-space(.)='{pestaña}']"
    span_elem = wait.until(EC.presence_of_element_located((By.XPATH, span_xpath)))
    tab_btn = span_elem.find_element(By.XPATH, "..")
    scroll_and_click(driver, tab_btn)
    time.sleep(2)

def limpiar_selector_destino(driver):
    """
    Limpia la selección previa en el menú de destinos, si existe.
    """
    try:
        clear_btn = driver.find_element(By.CSS_SELECTOR, ".multiselect__clear")
        clear_btn.click()
        time.sleep(0.5)
        print("[DEBUG] Selección previa de destino limpiada.")
    except Exception:
        pass

def wait_for_multiselect(driver, timeout=120, poll_frequency=1):
    """
    Espera a que el formulario de selección de destinos (.multiselect) esté presente y visible.
    Muestra mensajes de depuración cada 30 segundos.
    """
    waited = 0
    while waited < timeout:
        try:
            elem = driver.find_element(By.CSS_SELECTOR, ".multiselect")
            if elem.is_displayed():
                return elem
        except Exception:
            pass
        if waited > 0 and waited % 30 == 0:
            print(f"[DEBUG] Esperando a que aparezca el formulario de destinos... ({waited}s)")
        time.sleep(poll_frequency)
        waited += poll_frequency
    raise TimeoutError("No apareció el formulario de destinos (.multiselect) en el tiempo esperado.")

def abrir_selector_destinos(driver, wait, pestaña):
    """
    Abre el menú de destinos en la pestaña activa.
    Si hay una selección previa, la limpia.
    Devuelve True si el menú se abrió correctamente, False si hubo error.
    """
    try:
        wait.until(lambda d: d.find_element(By.CSS_SELECTOR, "div.tab-pane.active .multiselect").is_displayed())
        print("[DEBUG] .multiselect ahora visible tras cambio de pestaña.")
        multiselect = driver.find_element(By.CSS_SELECTOR, "div.tab-pane.active .multiselect")
        # Si hay selección previa, límpiala
        try:
            single = multiselect.find_element(By.CSS_SELECTOR, ".multiselect__single")
            print("[DEBUG] Hay selección previa, limpiando...")
            clear_btn = multiselect.find_element(By.CSS_SELECTOR, ".multiselect__clear")
            driver.execute_script("arguments[0].click();", clear_btn)
            time.sleep(0.3)
        except Exception:
            pass
        # Haz clic en el contenedor para abrir el menú
        try:
            multiselect.click()
        except Exception:
            driver.execute_script("arguments[0].click();", multiselect)
        time.sleep(0.2)
        # También intenta hacer clic en el input si existe y está visible
        try:
            input_elem = multiselect.find_element(By.CSS_SELECTOR, ".multiselect__input")
            if input_elem.is_displayed():
                try:
                    input_elem.click()
                except Exception:
                    driver.execute_script("arguments[0].click();", input_elem)
        except Exception:
            pass
        # Espera a que el menú de opciones esté visible (display != none)
        wait.until(
            lambda d: d.find_element(By.CSS_SELECTOR, "div.tab-pane.active .multiselect__content-wrapper").value_of_css_property("display") != "none"
        )
        print("[DEBUG] Selector de destinos abierto correctamente.")
        time.sleep(0.5)
        return True
    except Exception as e:
        print(f"[DEBUG] Error al abrir el selector en {pestaña}: {e}")
        debug_html = driver.page_source
        debug_path = os.path.join(HTML_DEBUG_DIR, f"ERROR_{pestaña}_selector.html")
        with open(debug_path, "w", encoding="utf-8") as f:
            f.write(debug_html)
        print(f"[DEBUG] HTML guardado en {debug_path} para inspección manual.")
        logging.error(f"No se pudo abrir el selector en {pestaña}: {e}")
        return False

def scrape():
    """
    Función principal del scrapper.
    - Abre la página principal.
    - Itera por cada pestaña y destino, seleccionando y extrayendo resultados.
    - Guarda los resultados en archivos JSON y HTML de depuración.
    """
    os.makedirs(DATA_FORMULARIO_DIR, exist_ok=True)
    driver = create_driver()
    wait = WebDriverWait(driver, 40)
    logging.info("Abriendo página principal...")
    driver.get(URL)
    time.sleep(3)

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
        print(f"[DEBUG] --- Procesando pestaña: {pestaña} ---")
        driver.get(URL)
        time.sleep(2)
        try:
            wait_for_multiselect(driver)
            print("[DEBUG] Formulario de destinos presente.")
            print("[DEBUG] Intentando hacer clic en la pestaña...")
            click_tab(driver, wait, pestaña)
            print("[DEBUG] Pestaña clickeada correctamente.")
            time.sleep(1)
        except Exception as e:
            print(f"[DEBUG] Error al hacer clic en la pestaña {pestaña}: {e}")
            logging.error(f"No se pudo hacer clic en la pestaña {pestaña}: {e}")
            continue

        # Espera a que la pestaña esté activa y el multiselect sea visible y abre el selector de destinos
        if not abrir_selector_destinos(driver, wait, pestaña):
            continue

        limpiar_selector_destino(driver)

        print("[DEBUG] Buscando opciones de destino...")
        opciones = driver.find_elements(By.CSS_SELECTOR, "div.tab-pane.active .multiselect__option:not(.multiselect__option--group):not(.multiselect__option--disabled)")
        print(f"[DEBUG] Se encontraron {len(opciones)} opciones de destino.")
        destinos = [op.text.strip() for op in opciones if op.text.strip()]
        print(f"[DEBUG] Destinos: {destinos}")
        logging.info(f"Destinos encontrados en {pestaña}: {destinos}")

        subfolder = pestaña.lower()
        subfolder_path = os.path.join(DATA_FORMULARIO_DIR, subfolder)
        os.makedirs(subfolder_path, exist_ok=True)

        for destino in destinos:
            logging.info(f"Procesando destino: {destino}")

            driver.get(URL)
            time.sleep(2)
            try:
                print(f"[DEBUG] Reabriendo pestaña {pestaña} para destino {destino}...")
                wait_for_multiselect(driver)
                click_tab(driver, wait, pestaña)
                print(f"[DEBUG] Pestaña {pestaña} reabierta correctamente.")
                time.sleep(1)
            except Exception as e:
                print(f"[DEBUG] Error al volver a la pestaña {pestaña}: {e}")
                logging.error(f"No se pudo volver a la pestaña {pestaña}: {e}")
                continue

            # Abre el selector de destinos de forma robusta
            if not abrir_selector_destinos(driver, wait, pestaña):
                continue

            limpiar_selector_destino(driver)
            time.sleep(0.3)
            if not abrir_selector_destinos(driver, wait, pestaña):
                continue

            # Selecciona el destino (bloque robusto)
            try:
                print(f"[DEBUG] Buscando opción de destino '{destino}'...")
                opciones = driver.find_elements(By.CSS_SELECTOR, "div.tab-pane.active .multiselect__option")
                opcion_span = None
                for op in opciones:
                    hijo = None
                    try:
                        hijo = op.find_element(By.XPATH, "./span")
                    except Exception:
                        pass
                    texto = hijo.text.strip() if hijo else op.text.strip()
                    if texto.lower() == destino.strip().lower():
                        opcion_span = op
                        break
                if opcion_span:
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", opcion_span)
                    time.sleep(0.2)
                    driver.execute_script("arguments[0].click();", opcion_span)
                    print(f"[DEBUG] Opción '{destino}' seleccionada correctamente.")
                    time.sleep(0.5)
                else:
                    raise Exception(f"No se encontró la opción '{destino}' en el menú desplegable.")
            except Exception as e:
                print(f"[DEBUG] No se encontró/clickeó la opción '{destino}': {e}")
                logging.warning(f"No se encontró/clickeó la opción '{destino}': {e}")
                continue

            try:
                print("[DEBUG] Buscando botón Buscar...")
                # Busca el botón Buscar en el contenedor principal, si no existe busca en la pestaña activa
                try:
                    form_container = driver.find_element(By.CSS_SELECTOR, "div.tab-pane.active .form-inline.container-booking-responsive")
                    buscar_btn = form_container.find_element(By.CSS_SELECTOR, "button.btn.btn-block.btn-primary")
                except Exception:
                    print("[DEBUG] No se encontró el contenedor esperado, buscando botón Buscar directamente en la pestaña activa...")
                    tab_active = driver.find_element(By.CSS_SELECTOR, "div.tab-pane.active")
                    buscar_btn = tab_active.find_element(By.CSS_SELECTOR, "button.btn.btn-block.btn-primary")
                print(f"[DEBUG] HTML del botón Buscar: {buscar_btn.get_attribute('outerHTML')}")
                wait.until(lambda d: buscar_btn.is_displayed() and buscar_btn.is_enabled())
                try:
                    buscar_btn.click()
                except Exception:
                    driver.execute_script("arguments[0].click();", buscar_btn)
                print("[DEBUG] Botón Buscar pulsado, esperando resultados...")
                logging.info("Botón Buscar pulsado, esperando resultados...")
            except Exception as e:
                print(f"[DEBUG] No se pudo hacer clic en Buscar en {pestaña} - {destino}: {e}")
                debug_html = driver.page_source
                debug_path = os.path.join(HTML_DEBUG_DIR, f"ERROR_{pestaña}_{destino}_buscar.html")
                with open(debug_path, "w", encoding="utf-8") as f:
                    f.write(debug_html)
                print(f"[DEBUG] HTML guardado en {debug_path} para inspección manual.")
                logging.error(f"No se pudo hacer clic en Buscar en {pestaña} - {destino}: {e}")
                continue

            try:
                wait.until(lambda d: "/Hotel/Search" in d.current_url)
                print("[DEBUG] Redirección detectada, esperando resultados...")
                logging.info("Redirección detectada, esperando resultados...")
                wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".row.pb15, .card-hotel, .card-house, .card-tour, .card-campismo"))
                )
                WebDriverWait(driver, 30).until(
                    lambda d: len(d.find_elements(By.CSS_SELECTOR, ".card-hotel, .card-house, .card-tour, .card-campismo")) > 0
                )
                time.sleep(2)
            except Exception as e:
                print(f"[DEBUG] No se detectaron resultados visibles para {pestaña} - {destino}: {e}")
                logging.warning(f"No se detectaron resultados visibles para {pestaña} - {destino}: {e}")

            current_url = driver.current_url
            logging.info(f"URL después de buscar: {current_url}")
            print(f"[DEBUG] URL después de buscar: {current_url}")

            html = driver.page_source
            save_debug_html(html, pestaña, destino)
            soup = BeautifulSoup(html, "html.parser")
            resultados = []

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
                if data["nombre"]:
                    resultados.append(data)


            for data in resultados:
                enlace = data.get("enlace")
                if enlace:
                    # Si el enlace es relativo, hazlo absoluto
                    if enlace.startswith("/"):
                        enlace = URL.rstrip("/") + enlace
                    try:
                        driver.get(enlace)
                        time.sleep(2)
                        detalle_html = driver.page_source
                        detalle_soup = BeautifulSoup(detalle_html, "html.parser")
                        # Ajusta el selector según la estructura real de la página de detalle
                        desc_elem = detalle_soup.select_one(".description, .detalle, .descripcion, .content, p")
                        descripcion = desc_elem.text.strip() if desc_elem else ""
                        data["descripcion"] = descripcion
                    except Exception as e:
                        print(f"[DEBUG] No se pudo extraer descripción de {enlace}: {e}")
                # Si no hay enlace, deja la descripción como está
            # Elimina el campo 'enlace' antes de guardar si no lo quieres en el JSON final
            for data in resultados:
                data.pop("enlace", None)
            

            filename = os.path.join(subfolder_path, f"{destino}.json".replace(" ", "_"))
            save_json_with_destino(resultados, filename, destino)
            logging.info(f"Guardado: {filename} ({len(resultados)} resultados)")

    driver.quit()
    logging.info("Scraping de pestañas y destinos completado.")

if __name__ == "__main__":
    """
    Permite ejecutar el scrapper directamente desde la línea de comandos.
    """
    scrape()