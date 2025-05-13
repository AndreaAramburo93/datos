from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd

# Configuración de opciones para Selenium
options = Options()
options.add_argument("--headless")  # Ejecutar en modo sin cabeza
options.add_argument("--window-size=1920,1080")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36")

# Inicializar el controlador de Selenium
driver = webdriver.Chrome(options=options)

# URL del libro en Goodreads
url = "https://www.goodreads.com/book/show/142296.The_Anubis_Gates"
driver.get(url)

# Esperar a que se cargue la sección de reseñas
WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.CLASS_NAME, "reviewItem"))
)

# Lista para almacenar las reseñas
reviews = []

# Recorrer las primeras 10 páginas de reseñas
for page in range(10):
    print(f"🔎 Extrayendo reseñas de la página {page + 1}...")

    # Esperar a que se carguen las reseñas
    time.sleep(2)

    # Obtener todas las reseñas visibles en la página
    review_elements = driver.find_elements(By.CLASS_NAME, "reviewItem")

    for el in review_elements:
        try:
            title = el.find_element(By.CLASS_NAME, "reviewTitle").text
        except:
            title = ""
        try:
            body = el.find_element(By.CLASS_NAME, "reviewText").text
        except:
            body = ""
        reviews.append({"Título": title, "Comentario": body})

    # Intentar hacer clic en el botón "Next"
    try:
        next_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a.next_page"))
        )
        next_button.click()
    except:
        print("❌ No se encontró el botón 'Next' o no hay más páginas.")
        break

# Cerrar el navegador
driver.quit()

# Crear un DataFrame con las reseñas
df = pd.DataFrame(reviews)
print(f"\n✅ Se extrajeron {len(df)} reseñas.")
print(df.head())

# Guardar las reseñas en un archivo CSV
df.to_csv("reseñas_the_anubis_gates.csv", index=False, encoding="utf-8")
