import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

options = Options()
options.add_argument("--headless")  # Opcional: sin abrir el navegador
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1200")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

mat_productos = []
mat_calificacion = []
mat_enlaces_comentarios = []

# Iterar sobre las primeras 4 páginas
for page_num in range(1, 5):
    print(f"Procesando página {page_num}")
    url = f"https://www.newegg.com/p/pl?N=100167718%20600010968%20600010967%20600010972&PageSize=96&page={page_num}"
    driver.get(url)
    time.sleep(5)  # Deja que cargue el contenido

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    productos = soup.find_all("div", class_="item-info")

    for prod in productos:
        titulo_tag = prod.find("a", class_="item-title")
        if titulo_tag:
            mat_productos.append(titulo_tag.text.strip())
        
        rating_tag = prod.find("a", class_="item-rating")
        if rating_tag:
            mat_calificacion.append(rating_tag.get("title", "Sin calificación"))
            enlace = rating_tag.get("href")
            if enlace:
                mat_enlaces_comentarios.append("https://www.newegg.com" + enlace)
    
    print("Esperando 10 segundos antes de continuar...")
    time.sleep(10)

driver.quit()

print(f"\nTotal de productos: {len(mat_productos)}")
print(f"Total de productos con calificación: {len(mat_calificacion)}")
print(f"Total de enlaces con comentarios: {len(mat_enlaces_comentarios)}")

# (Opcional) imprimir algunos productos:
for i in range(min(5, len(mat_productos))):
    print(f"{i+1}. {mat_productos[i]}")
