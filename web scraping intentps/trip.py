from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time

# Inicia el navegador con Selenium
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

# URL del restaurante en TripAdvisor
url = "https://www.tripadvisor.co/Restaurant_Review-g150807-d21387518-Reviews-Divina_Carne-Cancun_Yucatan_Peninsula.html"
driver.get(url)

# Función para obtener comentarios de una página
def obtener_comentarios():
    # Espera a que los comentarios estén cargados
    time.sleep(3)
    
    # Obtiene el HTML de la página
    soup = BeautifulSoup(driver.page_source, "html.parser")
    
    # Encuentra todos los comentarios
    comentarios = soup.find_all('q', class_='IRsGHoPm')
    
    comentarios_lista = []
    for comentario in comentarios:
        texto_comentario = comentario.get_text()
        comentarios_lista.append(texto_comentario)
    
    return comentarios_lista

# Lista para guardar los comentarios
todos_los_comentarios = []

# Iterar sobre las primeras 10 páginas
for i in range(10):
    comentarios_pagina = obtener_comentarios()
    todos_los_comentarios.extend(comentarios_pagina)
    
    # Intentar ir a la siguiente página de comentarios
    try:
        siguiente_pagina = driver.find_element(By.CLASS_NAME, "nav.next.taLnk.ui_button.primary")
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
