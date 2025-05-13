from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time

# Configuración de opciones del navegador
options = Options()
options.headless = False  # Cambiar a True si no deseas que se abra la ventana del navegador

# Inicia el navegador con Selenium
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# URL de la propiedad en Airbnb
url = "https://www.airbnb.com.co/rooms/710073172937237702?category_tag=Tag%3A677&search_mode=flex_destinations_search&adults=1&check_in=2025-05-11&check_out=2025-05-16&children=0&infants=0&pets=0&photo_id=1485429804&source_impression_id=p3_1747014678_P30z_3TW21mjBKmL&previous_page_section_name=1000&federated_search_id=89f7d3ae-a09b-4ccf-a8c1-47bf09273052"

driver.get(url)

# Función para obtener comentarios de una página
def obtener_comentarios():
    # Espera a que los comentarios estén cargados
    time.sleep(3)
    
    # Obtiene el HTML de la página
    soup = BeautifulSoup(driver.page_source, "html.parser")
    
    # Encuentra todos los comentarios
    comentarios = soup.find_all('span', class_='_1ra0q4sv')

    comentarios_lista = []
    for comentario in comentarios:
        texto_comentario = comentario.get_text()
        comentarios_lista.append(texto_comentario)
    
    return comentarios_lista

# Lista para guardar los comentarios
todos_los_comentarios = []

# Iterar sobre las primeras 10 páginas de comentarios (si es posible)
for i in range(10):
    comentarios_pagina = obtener_comentarios()
    todos_los_comentarios.extend(comentarios_pagina)
    
    # Intentar ir a la siguiente página de comentarios
    try:
        siguiente_pagina = driver.find_element(By.XPATH, '//button[contains(text(), "Siguiente")]')
        siguiente_pagina.click()
        time.sleep(3)
    except Exception as e:
        print(f"No se pudo encontrar la siguiente página: {e}")
        break

# Muestra los comentarios obtenidos
for i, comentario in enumerate(todos_los_comentarios, 1):
    print(f"{i}. {comentario}")

# Cierra el navegador
driver.quit()
