from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd

# Configurar opciones del navegador
options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36"
)

# Ruta a tu ChromeDriver
driver = webdriver.Chrome(options=options)

# URL del producto
url = "https://www.aliexpress.us/item/3256806920332825.html?spm=a2g0o.tm1000009216.d2.1.4a40474cRerD7p&sourceType=561&pvid=5fa4df67-47b2-4126-ae38-6e7b9210e947&pdp_ext_f=%7B%22ship_from%22%3A%22CN%22%2C%22sku_id%22%3A%2212000039425681308%22%7D&scm=1007.28480.425796.0&scm-url=1007.28480.425796.0&scm_id=1007.28480.425796.0&pdp_npi=4%40dis%21COP%21COP%2061%2C462.09%21COP%2023%2C029.18%21%21%21102.61%2138.45%21%402103245417470114809672886e4acf%2112000039425681308%21gsd%21CO%21%21X&channel=sd&aecmd=true&gatewayAdapt=glo2usa4itemAdapt#nav-reviewl"
driver.get(url)

# Esperar que carguen los comentarios (puede tardar unos segundos)
wait = WebDriverWait(driver, 20)

# Lista para almacenar las reseñas
reviews = []

# Esperar hasta que aparezcan los comentarios
try:
    wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "review--wrap--U5X0TgT")))
except:
    print("⚠️ No se encontraron comentarios en la primera carga.")
    driver.quit()
    exit()

# Loop por las 10 primeras páginas
for page in range(10):
    print(f"🔎 Scraping página {page+1}...")

    # Esperar que carguen las reseñas en esta página
    try:
        wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "review--wrap--U5X0TgT")))
    except:
        print("❌ No se pudo cargar la página.")
        break

    # Obtener las reseñas
    review_elements = driver.find_elements(By.CLASS_NAME, "review--wrap--U5X0TgT")
    for elem in review_elements:
        try:
            text = elem.text.strip()
            if text:
                reviews.append(text)
        except:
            continue

    # Intentar hacer clic en el botón "Siguiente"
    try:
        next_button = driver.find_element(By.CSS_SELECTOR, ".comet-v2-btn.comet-v2-btn-slim.comet-v2-btn-large.v3--btn--KaygomA.comet-v2-btn-important")
        if "disabled" in next_button.get_attribute("class"):
            print("🔚 No hay más páginas.")
            break
        next_button.click()
        time.sleep(2)
    except:
        print("⚠️ No se encontró el botón para avanzar.")
        break

# Cerrar navegador
driver.quit()

# Guardar en CSV
df = pd.DataFrame({"review": reviews})
df.to_csv("aliexpress_reviews.csv", index=False, encoding="utf-8-sig")
print(f"✅ Se extrajeron {len(reviews)} reseñas.")
