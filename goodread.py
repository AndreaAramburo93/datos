from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# Configuración de opciones para Selenium
options = Options()
options.add_argument("--headless")  # Ejecutar en modo sin cabeza (sin interfaz gráfica)
options.add_argument("--window-size=1920,1080")  # Establecer tamaño de ventana
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36")
options.add_argument("--ignore-certificate-errors")  # Deshabilitar los errores de certificado SSL
options.add_argument("--disable-extensions")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")

# Desactivar WebGL y rasterización por software
options.add_argument("--disable-webgl")  # Desactivar WebGL
options.add_argument("--disable-software-rasterizer")  # Desactivar rasterización por software

# Inicializar el controlador de Selenium
driver = webdriver.Chrome(options=options)

# URL del libro en Goodreads
url = "https://www.goodreads.com/book/show/142296.The_Anubis_Gates"

# Abrir la página del libro
driver.get(url)

# Aumentar el tiempo de espera para la carga de la página
try:
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CLASS_NAME, "friendReviews"))
    )
except Exception as e:
    print(f"Error al cargar los comentarios: {e}")
    driver.quit()

# Definir un contenedor para los comentarios
comments = []

# Obtener comentarios de las primeras 10 páginas
for page in range(1, 11):
    print(f"Scraping página {page}...")

    # Esperar a que los comentarios se carguen en la página actual
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "friendReviews"))
        )
    except Exception as e:
        print(f"Error al cargar la página {page}: {e}")
        break

    # Extraer los comentarios de la página actual
    review_elements = driver.find_elements(By.CLASS_NAME, "friendReviews")
    for review in review_elements:
        comment_text = review.text
        comments.append(comment_text)

    # Intentar ir a la siguiente página de comentarios
    try:
        next_button = driver.find_element(By.CLASS_NAME, "next_page")
        next_button.click()
        time.sleep(2)  # Esperar para cargar la siguiente página
    except:
        print("No se pudo encontrar el botón de la siguiente página.")
        break

# Imprimir los primeros 5 comentarios obtenidos
for i, comment in enumerate(comments[:5]):
    print(f"{i+1}. {comment}")

# Cerrar el navegador después de obtener los comentarios
driver.quit()
