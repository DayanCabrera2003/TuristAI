"""
Configuración global para el crawler de turismo.

Define:
- URLs semilla para crawling.
- Profundidad máxima y cantidad máxima de páginas.
- Ruta de guardado.
- User-Agent y modo headless para Selenium.
"""
START_URLS = [
    "https://www.solwayscuba.com/hoteles/intereses/2/hoteles-para-familia/",
    "https://www.varaderoguide.net/index.html"
]
MAX_DEPTH = 3
MAX_PAGES = 10000
SAVE_PATH = "./data/raw/"
USER_AGENT = "random"  # Usa fake_useragent
HEADLESS = True
