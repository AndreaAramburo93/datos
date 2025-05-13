from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
import time


from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Configurar ChromeOptions
chrome_options = Options()
chrome_options.add_argument("--headless")  # Puedes quitar esto si quieres ver el navegador
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# Usar webdriver-manager para instalar automáticamente el driver correcto
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)



# Configurar Selenium
chrome_options = Options()
chrome_options.add_argument("--headless")  # Quitar esta línea si quieres ver el navegador
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# Ruta a tu ChromeDriver
driver_path = "/ruta/al/chromedriver"  # ⚠️ Cambia esto por tu ruta
service = Service(driver_path)
driver = webdriver.Chrome(service=service, options=chrome_options)

# Base URL con paginación
base_url = "https://www.metacritic.com/game/the-midnight-walk/user-reviews?page={}"

# Listas para almacenar los datos
usernames = []
dates = []
ratings = []
reviews = []

# Cuántas páginas deseas scrapear
total_pages = 5

for page in range(total_pages):
    print(f"Scrapeando página {page + 1}...")
    url = base_url.format(page)
    driver.get(url)

    # Esperar a que cargue el contenedor principal de reseñas
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "c-pageProductReviews-wrapper"))
        )
    except Exception as e:
        print("No se cargó la página correctamente:", e)
        continue

    # Parsear contenido con BeautifulSoup
    soup = BeautifulSoup(driver.page_source, "html.parser")
    reviews_wrapper = soup.find("div", class_="c-pageProductReviews-wrapper")
    if not reviews_wrapper:
        print("No se encontró el contenedor de reseñas.")
        continue

    review_blocks = reviews_wrapper.find_all("div", class_="c-siteReview")

    for block in review_blocks:
        # Usuario
        username_tag = block.find("span", class_="c-siteReviewHeader_username")
        username = username_tag.text.strip() if username_tag else None

        # Comentario
        review_tag = block.find("div", class_="c-siteReview_quote")
        review_text = review_tag.text.strip() if review_tag else None

        # Puntuación
        score_tag = block.find("div", attrs={"title": lambda t: t and "User score" in t})
        rating = score_tag["title"] if score_tag and score_tag.has_attr("title") else None

        # Fecha (si está disponible)
        date_tag = block.find("div", class_="c-siteReviewHeader_date")
        date = date_tag.text.strip() if date_tag else None

        usernames.append(username)
        reviews.append(review_text)
        ratings.append(rating)
        dates.append(date)

    time.sleep(2)  # Espera para evitar bloqueo

driver.quit()

# Crear DataFrame
df = pd.DataFrame({
    'username': usernames,
    'date': dates,
    'rating': ratings,
    'review': reviews
})

# Mostrar resumen
print(df.info())
print(df.head())
