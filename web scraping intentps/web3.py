import time
import os
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
import random

class BuscaLibreReviewsScraper:
    def __init__(self, headless=True):
        """Inicializa el scraper de reseñas de BuscaLibre"""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--lang=es-ES")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Rotar entre varios user agents para evitar bloqueos
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0"
        ]
        user_agent = random.choice(user_agents)
        chrome_options.add_argument(f"user-agent={user_agent}")
        print(f"Usando User-Agent: {user_agent}")
        
        try:
            self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.wait = WebDriverWait(self.driver, 15)
            self.driver.set_window_size(1920, 1080)
        except Exception as e:
            print(f"Error al inicializar el navegador: {str(e)}")
            raise

    def extract_book_info(self, url):
        """Extrae información básica del libro"""
        try:
            self.driver.get(url)
            time.sleep(5)  # Esperar a que cargue la página
            
            # Extraer título del libro
            try:
                titulo = self.driver.find_element(By.CSS_SELECTOR, "h1.product-title").text.strip()
            except NoSuchElementException:
                titulo = "Título no encontrado"
            
            # Extraer autor
            try:
                autor = self.driver.find_element(By.CSS_SELECTOR, "div.author-data").text.strip()
            except NoSuchElementException:
                autor = "Autor no encontrado"
            
            # Extraer ISBN o identificador
            try:
                isbn = url.split("/")[-2]
            except:
                isbn = "ISBN no encontrado"
            
            return {
                "titulo": titulo,
                "autor": autor,
                "isbn": isbn,
                "url": url
            }
        except Exception as e:
            print(f"Error al extraer información del libro: {str(e)}")
            return {
                "titulo": "Error al extraer título",
                "autor": "Error al extraer autor",
                "isbn": "Error al extraer ISBN",
                "url": url
            }

    def get_book_reviews(self, url, max_pages=10):
        """Extrae las reseñas de un libro en BuscaLibre"""
        try:
            reviews = []
            
            # Primero extraemos la información básica del libro
            book_info = self.extract_book_info(url)
            print(f"Extrayendo reseñas para: {book_info['titulo']} de {book_info['autor']}")
            
            # Navegar a la sección de reseñas
            try:
                # Primero intentamos buscar un elemento que nos lleve a las reseñas
                review_tab_selectors = [
                    "//a[contains(@href, '#reviews')]",
                    "//a[contains(text(), 'reseñas')]",
                    "//a[contains(text(), 'Reseñas')]",
                    "//a[contains(text(), 'opiniones')]",
                    "//a[contains(text(), 'comentarios')]",
                    "//div[contains(@class, 'tab-review')]",
                    "//div[contains(@id, 'reviews')]"
                ]
                
                review_tab_found = False
                for selector in review_tab_selectors:
                    try:
                        review_tab = self.driver.find_element(By.XPATH, selector)
                        review_tab.click()
                        print("Sección de reseñas encontrada y clickeada")
                        review_tab_found = True
                        time.sleep(3)
                        break
                    except NoSuchElementException:
                        continue
                
                if not review_tab_found:
                    print("No se encontró un enlace específico a reseñas, intentando hacer scroll")
                    # Hacer scroll hasta donde podrían estar las reseñas
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.7);")
                    time.sleep(2)
            
            except Exception as e:
                print(f"Error al navegar a la sección de reseñas: {str(e)}")
            
            page_count = 0
            reviews_found = False
            
            while page_count < max_pages:
                print(f"Analizando página {page_count+1} de reseñas...")
                
                # Hacer scroll para cargar contenido dinámico
                self.driver.execute_script("window.scrollBy(0, 500);")
                time.sleep(2)
                
                # Intentar encontrar reseñas con múltiples selectores
                review_elements = []
                selectors = [
                    "div.product-review-box",
                    "div.review-item",
                    "div.comment-box",
                    "div.product-comment",
                    "div.customer-review-container",
                    "div[class*='review']", 
                    "div[class*='comment']"
                ]
                
                for selector in selectors:
                    try:
                        review_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if review_elements:
                            reviews_found = True
                            print(f"Se encontraron {len(review_elements)} reseñas con selector: {selector}")
                            break
                    except Exception:
                        continue
                
                if not reviews_found:
                    print("Buscando en estructura de página alternativa...")
                    # Si no encontramos reseñas con los selectores anteriores, 
                    # intentemos capturar la estructura completa de reseñas
                    try:
                        reviews_section = self.driver.find_element(By.XPATH, "//div[contains(@class, 'reviews') or contains(@id, 'reviews') or contains(@class, 'comentarios')]")
                        print("Sección de reseñas detectada, analizando estructura...")
                        
                        # Imprimir clase para depuración
                        print(f"Clase de la sección de reseñas: {reviews_section.get_attribute('class')}")
                        
                        # Intentemos identificar elementos individuales dentro de esta sección
                        child_elements = reviews_section.find_elements(By.XPATH, "./div | ./ul/li | ./div/div")
                        if child_elements:
                            review_elements = child_elements
                            reviews_found = True
                            print(f"Se encontraron {len(review_elements)} posibles elementos de reseña")
                    except NoSuchElementException:
                        print("No se encontró una sección de reseñas clara")
                
                if not review_elements:
                    print(f"No se han encontrado reseñas en la página {page_count+1}")
                    # Si no hemos encontrado nada en la primera página, probablemente no hay reseñas
                    if page_count == 0:
                        print("No parece haber reseñas para este libro")
                    break
                
                for review in review_elements:
                    try:
                        # Nombre del usuario
                        try:
                            username = review.find_element(By.CSS_SELECTOR, ".user-name, .reviewer-name, .comment-author").text.strip()
                        except NoSuchElementException:
                            # Intentar con XPath más general si el selector CSS no funciona
                            try:
                                username = review.find_element(By.XPATH, ".//div[contains(@class, 'user') or contains(@class, 'author')]").text.strip()
                            except NoSuchElementException:
                                username = "Usuario anónimo"
                        
                        # Valoración
                        try:
                            # Primero intentar encontrar elementos de estrellas
                            stars = review.find_elements(By.CSS_SELECTOR, ".fa-star, .star-filled, .rating-star")
                            if stars:
                                rating = len(stars)
                            else:
                                # Si no hay estrellas, buscar un texto con la valoración
                                rating_text = review.find_element(By.CSS_SELECTOR, ".rating, .stars, .score").text
                                rating = rating_text.strip()
                        except NoSuchElementException:
                            rating = "N/A"
                        
                        # Fecha de la reseña
                        try:
                            date = review.find_element(By.CSS_SELECTOR, ".review-date, .comment-date, .date").text.strip()
                        except NoSuchElementException:
                            date = "Fecha no disponible"
                        
                        # Título de la reseña
                        try:
                            title = review.find_element(By.CSS_SELECTOR, ".review-title, .comment-title, h3, h4").text.strip()
                        except NoSuchElementException:
                            title = "Sin título"
                        
                        # Contenido de la reseña
                        try:
                            content = review.find_element(By.CSS_SELECTOR, ".review-content, .comment-content, .review-text, p").text.strip()
                        except NoSuchElementException:
                            content = "Sin contenido"
                        
                        reviews.append({
                            "libro_titulo": book_info["titulo"],
                            "libro_autor": book_info["autor"],
                            "libro_isbn": book_info["isbn"],
                            "usuario": username,
                            "valoracion": rating,
                            "titulo": title,
                            "fecha": date,
                            "contenido": content
                        })
                    
                    except Exception as e:
                        print(f"Error al extraer datos de una reseña: {str(e)}")
                        continue
                
                # Si hemos extraído reseñas, intentar ir a la siguiente página
                if reviews:
                    try:
                        next_page_selectors = [
                            "//a[contains(@class, 'next') or contains(@rel, 'next')]",
                            "//a[contains(text(), 'Siguiente')]",
                            "//a[contains(text(), 'siguiente')]",
                            "//a[contains(text(), 'Next')]",
                            "//li[contains(@class, 'next')]/a",
                            "//button[contains(text(), 'Siguiente') or contains(@class, 'next')]"
                        ]
                        
                        next_found = False
                        for selector in next_page_selectors:
                            try:
                                next_button = self.driver.find_element(By.XPATH, selector)
                                if next_button.is_displayed() and next_button.is_enabled():
                                    print("Botón 'Siguiente' encontrado, navegando a la siguiente página...")
                                    next_button.click()
                                    time.sleep(5)  # Esperar a que cargue la siguiente página
                                    next_found = True
                                    break
                            except NoSuchElementException:
                                continue
                        
                        if next_found:
                            page_count += 1
                        else:
                            print("No se encontró botón para la página siguiente o no hay más páginas.")
                            break
                            
                    except Exception as e:
                        print(f"Error al navegar a la siguiente página: {str(e)}")
                        break
                else:
                    print("No se pudieron extraer reseñas en esta página.")
                    break
            
            return reviews, book_info
        
        except Exception as e:
            print(f"Error durante el scraping: {str(e)}")
            return [], {}
    
    def close(self):
        """Cierra el navegador"""
        if self.driver:
            self.driver.quit()


def main():
    # URLs de libros en BuscaLibre para extraer reseñas
    urls = [
        "https://www.buscalibre.com.co/libro-los-divinos-laura-restrepo-libro-fisico/9789585428829/p/49974000",
        "https://www.buscalibre.com.co/libro-la-isla-bajo-el-mar-isabel-allende/9788499897318/p/31107818",
        "https://www.buscalibre.com.co/libro-el-amor-en-los-tiempos-del-colera-gabriel-garcia-marquez/9789585118362/p/4471097",
        "https://www.buscalibre.com.co/libro-cien-anos-de-soledad-gabriel-garcia-marquez/9788420471839/p/24083353",
        "https://www.buscalibre.com.co/libro-el-olvido-que-seremos-penguin-random-house-libro-fisico/9789585118171/p/3599772"
    ]
    
    # Configuración
    max_pages_per_book = 5
    headless = False  # Para BuscaLibre es mejor verlo en acción para detectar captchas o problemas
    excel_filename = "buscalibre_resenas_libros.xlsx"
    
    print("=== Iniciando extracción de reseñas de libros en BuscaLibre ===")
    print(f"Total de libros a analizar: {len(urls)}")
    print(f"Páginas a extraer por libro: {max_pages_per_book}")
    print(f"Modo headless: {'Activado' if headless else 'Desactivado'}")
    
    # Iniciar scraper
    scraper = BuscaLibreReviewsScraper(headless=headless)
    all_reviews = []
    books_info = []
    
    try:
        for i, url in enumerate(urls, 1):
            print(f"\n[{i}/{len(urls)}] Procesando URL: {url}")
            reviews, book_info = scraper.get_book_reviews(url, max_pages=max_pages_per_book)
            
            if reviews:
                all_reviews.extend(reviews)
                books_info.append(book_info)
                print(f"Se extrajeron {len(reviews)} reseñas para el libro: {book_info['titulo']}")
            else:
                print(f"No se encontraron reseñas para el libro en: {url}")
            
            # Esperar un tiempo aleatorio entre libros para evitar bloqueos
            wait_time = random.uniform(8, 15)
            print(f"Esperando {wait_time:.1f} segundos antes del siguiente libro...")
            time.sleep(wait_time)
        
        if all_reviews:
            # Crear DataFrame para reseñas
            df_reviews = pd.DataFrame(all_reviews)
            
            # Crear DataFrame para información de libros
            df_books = pd.DataFrame(books_info)
            
            # Guardar ambos en diferentes hojas del mismo archivo Excel
            with pd.ExcelWriter(excel_filename, engine='openpyxl') as writer:
                df_reviews.to_excel(writer, sheet_name='Reseñas', index=False)
                df_books.to_excel(writer, sheet_name='Libros', index=False)
            
            print(f"\n¡Éxito! Se han extraído un total de {len(all_reviews)} reseñas de {len(books_info)} libros")
            print(f"Los datos se han guardado en: {os.path.abspath(excel_filename)}")
        else:
            print("\nNo se encontraron reseñas en ninguno de los libros.")
    
    except Exception as e:
        print(f"Error en la ejecución principal: {str(e)}")
    
    finally:
        scraper.close()
        print("\nProceso finalizado.")

if __name__ == "__main__":
    main()