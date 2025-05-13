from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time

# Configuración de navegador
options = Options()
# options.add_argument("--headless")  # Desactiva para pruebas visuales
options.add_argument("--start-maximized")

# Inicializa el navegador
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# URL del hotel
url = "https://www.booking.com/hotel/br/flat-no-marulhos-b302.es.html"
driver.get(url)

# Esperar carga inicial
time.sleep(5)

# Intentar hacer scroll hasta el botón y hacer clic
try:
    # Scroll para asegurar visibilidad del botón
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
    time.sleep(2)

    # Esperar a que el botón esté presente Y hacer clic justo después de encontrarlo
    boton = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="fr-read-all-reviews"]'))
    )
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="fr-read-all-reviews"]'))
    )
    boton.click()
    print("✅ Botón de reseñas clickeado.")
except Exception as e:
    print("❌ No se pudo hacer clic en el botón de reseñas:", e)
    driver.quit()
    exit()

# Esperar a que carguen las reseñas
time.sleep(5)

# Scroll para cargar más reseñas si es necesario
for _ in range(5):
    driver.execute_script("window.scrollBy(0, 1000);")
    time.sleep(1)

# Extraer HTML y parsear
soup = BeautifulSoup(driver.page_source, "html.parser")
titulos = soup.select('[data-testid="review-title"]')
positivos = soup.select('[data-testid="review-positive-text"]')

print("\n📋 Reseñas encontradas:\n")
if titulos and positivos:
    for titulo, comentario in zip(titulos, positivos):
        print("🟦 Título:", titulo.text.strip())
        print("🟩 Comentario positivo:", comentario.text.strip())
        print("-" * 60)
else:
    print("⚠️ No se encontraron reseñas visibles.")

driver.quit()
