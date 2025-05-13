import time
import csv
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

class AmazonCommentsScraper:
    def __init__(self, headless=True):
        """Inicializa el scraper de comentarios de Amazon"""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless=new")  # Versión moderna de headless
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--lang=es-ES")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")  # Evita detección
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Rotar entre varios user agents para evitar bloqueos
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0"
        ]
        import random
        user_agent = random.choice(user_agents)
        chrome_options.add_argument(f"user-agent={user_agent}")
        print(f"Usando User-Agent: {user_agent}")
        
        # Inicializar WebDriver con opciones mejoradas
        try:
            self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
            # Establecer scripts para evadir detección
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.wait = WebDriverWait(self.driver, 15)  # Aumentar tiempo de espera
            
            # Configurar el tamaño de la ventana
            self.driver.set_window_size(1920, 1080)
        except Exception as e:
            print(f"Error al inicializar el navegador: {str(e)}")
            raise
    
    def get_product_comments(self, url, max_pages=5):
        """Extrae los comentarios de un producto de Amazon
        
        Args:
            url (str): URL del producto de Amazon
            max_pages (int): Número máximo de páginas a extraer
        
        Returns:
            list: Lista de diccionarios con la información de los comentarios
        """
        try:
            comments = []
            
            # Navegar a la página del producto
            self.driver.get(url)
            time.sleep(3)  # Esperar un poco más para que cargue la página
            
            # Aceptar cookies si aparece el diálogo
            try:
                accept_cookies = self.driver.find_element(By.ID, "sp-cc-accept")
                accept_cookies.click()
                time.sleep(2)
            except NoSuchElementException:
                pass
            
            # Primer intento: ir directamente a la sección de reviews modificando la URL
            reviews_url = url.split('/ref=')[0] if '/ref=' in url else url
            if not reviews_url.endswith('/'):
                reviews_url += '/'
            reviews_url += 'product-reviews/'
            
            print(f"Intentando acceder directamente a la URL de comentarios: {reviews_url}")
            self.driver.get(reviews_url)
            time.sleep(3)
            
            # Si no funciona el método directo, intentar con el enlace en la página
            if "product-reviews" not in self.driver.current_url:
                print("Navegando de vuelta a la página de producto para buscar el enlace de comentarios")
                self.driver.get(url)
                time.sleep(2)
                
                try:
                    # Intentar encontrar el enlace de comentarios y hacer clic
                    self.driver.execute_script("window.scrollBy(0, 800);")  # Desplazarse hacia abajo
                    time.sleep(1)
                    
                    # Intentar varios selectores para el enlace de comentarios
                    selectors = [
                        "//a[contains(@data-hook, 'see-all-reviews-link')]",
                        "//a[contains(text(), 'comentarios')]",
                        "//a[contains(text(), 'opiniones')]",
                        "//a[contains(text(), 'reviews')]",
                        "//a[contains(@href, 'product-reviews')]",
                        "//div[contains(@id, 'reviews-summary')]//a"
                    ]
                    
                    clicked = False
                    for selector in selectors:
                        try:
                            print(f"Intentando selector: {selector}")
                            reviews_link = self.driver.find_element(By.XPATH, selector)
                            print(f"Enlace encontrado: {reviews_link.text}")
                            reviews_link.click()
                            clicked = True
                            time.sleep(3)
                            break
                        except NoSuchElementException:
                            continue
                    
                    if not clicked:
                        print("No se pudo encontrar el enlace a los comentarios.")
                except Exception as e:
                    print(f"Error al buscar el enlace de comentarios: {str(e)}")
            
            # Verificar que estamos en la página de comentarios
            if "product-reviews" not in self.driver.current_url and "customer-reviews" not in self.driver.current_url:
                print("ADVERTENCIA: No parece que estemos en la página de comentarios.")
                print(f"URL actual: {self.driver.current_url}")
            
            page_count = 0
            
            while page_count < max_pages:
                # Esperar a que carguen los comentarios
                print(f"Analizando página {page_count+1} de comentarios...")
                
                # Hacer scroll para cargar contenido dinámico
                for _ in range(3):
                    self.driver.execute_script("window.scrollBy(0, 500);")
                    time.sleep(0.5)
                
                # Capturar lo que hay en la página para depuración
                page_source = self.driver.page_source
                with open(f"amazon_page_{page_count+1}.html", "w", encoding="utf-8") as f:
                    f.write(page_source)
                print(f"Se ha guardado el código fuente en amazon_page_{page_count+1}.html para depuración")
                
                # Intentar encontrar comentarios con múltiples selectores
                review_elements = []
                selectors = [
                    "div[data-hook='review']",
                    "div.review",
                    "div.a-section.review", 
                    "div[id^='customer_review']"
                ]
                
                for selector in selectors:
                    try:
                        review_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if review_elements:
                            print(f"Se encontraron {len(review_elements)} comentarios con selector: {selector}")
                            break
                    except Exception as e:
                        print(f"Error con selector {selector}: {str(e)}")
                
                if not review_elements:
                    print(f"No se han encontrado comentarios en la página {page_count+1}")
                    break
                
                for review in review_elements:
                    try:
                        # Información del usuario y fecha
                        user_info = review.find_element(By.CSS_SELECTOR, ".a-profile-name").text
                        
                        try:
                            rating_text = review.find_element(By.CSS_SELECTOR, "i[data-hook='review-star-rating'], i[data-hook='cmps-review-star-rating']").get_attribute("class")
                            # Extraer el número de la valoración del texto de la clase (por ejemplo, "a-star-5" para 5 estrellas)
                            rating = rating_text.split("-")[-1] if "-" in rating_text else "N/A"
                        except NoSuchElementException:
                            rating = "N/A"
                        
                        try:
                            title = review.find_element(By.CSS_SELECTOR, "a[data-hook='review-title'] span, [data-hook='review-title'] span").text.strip()
                        except NoSuchElementException:
                            title = "Sin título"
                        
                        try:
                            date_text = review.find_element(By.CSS_SELECTOR, "[data-hook='review-date']").text
                        except NoSuchElementException:
                            date_text = "Fecha no disponible"
                        
                        # Contenido del comentario
                        try:
                            content = review.find_element(By.CSS_SELECTOR, "[data-hook='review-body']").text.strip()
                        except NoSuchElementException:
                            content = "Sin contenido"
                        
                        # Verificación de compra
                        try:
                            verified = "Compra verificada" in review.text
                        except:
                            verified = False
                        
                        # Votos útiles
                        try:
                            helpful_text = review.find_element(By.CSS_SELECTOR, "[data-hook='helpful-vote-statement']").text
                            helpful = helpful_text.split()[0] if helpful_text else "0"
                            # Convertir texto como "A una persona" a un número
                            if helpful.lower() in ["a", "una", "one"]:
                                helpful = "1"
                            elif helpful.lower() in ["dos", "two"]:
                                helpful = "2"
                        except NoSuchElementException:
                            helpful = "0"
                        
                        comments.append({
                            "usuario": user_info,
                            "valoracion": rating,
                            "titulo": title,
                            "fecha": date_text,
                            "contenido": content,
                            "verificado": verified,
                            "votos_utiles": helpful
                        })
                    
                    except Exception as e:
                        print(f"Error al extraer datos de un comentario: {str(e)}")
                        continue
                
                # Verificar si hay una página siguiente con diferentes selectores
                try:
                    next_page_selectors = [
                        "//li[@class='a-last']/a",
                        "//a[contains(@href, 'pageNumber') and contains(text(), 'Siguiente')]",
                        "//a[contains(@href, 'pageNumber') and contains(text(), 'Next')]",
                        "//a[contains(@href, 'pageNumber') and contains(@aria-label, 'Next')]",
                        "//span[contains(text(), 'Siguiente')]/parent::a",
                        "//span[contains(text(), 'Next')]/parent::a"
                    ]
                    
                    next_found = False
                    for selector in next_page_selectors:
                        try:
                            next_page = self.driver.find_element(By.XPATH, selector)
                            next_page_url = next_page.get_attribute('href')
                            if next_page_url:
                                print(f"Navegando a la siguiente página con URL: {next_page_url}")
                                self.driver.get(next_page_url)  # A veces es más confiable usar get que click
                                time.sleep(3)
                                next_found = True
                                break
                            else:
                                next_page.click()
                                time.sleep(3)
                                next_found = True
                                break
                        except Exception:
                            continue
                    
                    if next_found:
                        page_count += 1
                    else:
                        print("No se encontró botón para la página siguiente.")
                        break
                        
                except Exception as e:
                    print(f"Error al navegar a la siguiente página: {str(e)}")
                    break
            
            return comments
        
        except Exception as e:
            print(f"Error durante el scraping: {str(e)}")
            return []
    
    def print_comment(self, comment, index=None):
        """Imprime un comentario de forma formateada en la terminal
        
        Args:
            comment (dict): Diccionario con los datos del comentario
            index (int, optional): Índice del comentario
        """
        sep_line = "-" * 80
        
        print(sep_line)
        if index is not None:
            print(f"COMENTARIO #{index}")
        
        print(f"Usuario: {comment['usuario']}")
        print(f"Valoración: {'⭐' * int(comment['valoracion']) if comment['valoracion'].isdigit() else comment['valoracion']}")
        print(f"Título: {comment['titulo']}")
        print(f"Fecha: {comment['fecha']}")
        print(f"Verificado: {'Sí' if comment['verificado'] else 'No'}")
        print(f"Votos útiles: {comment['votos_utiles']}")
        print("\nContenido:")
        print(comment['contenido'])
        print(sep_line)
        print()
    
    def display_comments_summary(self, comments, max_display=5):
        """Muestra un resumen de los comentarios extraídos en la terminal
        
        Args:
            comments (list): Lista de diccionarios con los comentarios
            max_display (int): Número máximo de comentarios a mostrar completos
        """
        if not comments:
            print("No hay comentarios para mostrar.")
            return
        
        print("\n" + "=" * 30 + " RESUMEN DE COMENTARIOS " + "=" * 30)
        print(f"Total de comentarios extraídos: {len(comments)}")
        
        # Análisis de valoraciones
        ratings = [int(c['valoracion']) for c in comments if c['valoracion'].isdigit()]
        if ratings:
            avg_rating = sum(ratings) / len(ratings)
            rating_dist = {}
            for r in ratings:
                rating_dist[r] = rating_dist.get(r, 0) + 1
                
            print(f"\nValoración promedio: {avg_rating:.1f} ⭐")
            print("Distribución de valoraciones:")
            for r in range(5, 0, -1):
                count = rating_dist.get(r, 0)
                percentage = (count / len(ratings)) * 100 if ratings else 0
                print(f"  {r} ⭐: {count} ({percentage:.1f}%)")
        
        # Mostrar los primeros comentarios (limitado por max_display)
        print(f"\nMostrando los primeros {min(max_display, len(comments))} comentarios:")
        for i, comment in enumerate(comments[:max_display], 1):
            self.print_comment(comment, i)
            
        if len(comments) > max_display:
            print(f"... y {len(comments) - max_display} comentarios más (guardados en el CSV).")
    
    def save_to_csv(self, comments, filename="amazon_comments.csv"):
        """Guarda los comentarios en un archivo CSV
        
        Args:
            comments (list): Lista de diccionarios con los comentarios
            filename (str): Nombre del archivo CSV
        """
        if not comments:
            print("No hay comentarios para guardar.")
            return
        
        try:
            fieldnames = ["usuario", "valoracion", "titulo", "fecha", "contenido", "verificado", "votos_utiles"]
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for comment in comments:
                    writer.writerow(comment)
            
            print(f"Se han guardado {len(comments)} comentarios en {filename}")
            
        except Exception as e:
            print(f"Error al guardar en CSV: {str(e)}")
    
    def close(self):
        """Cierra el navegador"""
        if self.driver:
            self.driver.quit()

def main():
    # Función para obtener input del usuario
    def get_user_input():
        url = input("Introduce la URL del producto de Amazon (o presiona Enter para usar la predeterminada): ")
        if not url:
            url = "https://www.amazon.com/-/es/SanDisk-Tarjeta-memoria-Extreme-UHS-I/dp/B09X7FXHVJ/"
        
        try:
            pages = int(input("Número de páginas a extraer (presiona Enter para usar 3): ") or "3")
        except ValueError:
            pages = 3
        
        try:
            use_headless = input("¿Ejecutar en modo headless? (s/n, predeterminado: n): ").lower() == 's'
        except:
            use_headless = False
            
        filename = input("Nombre del archivo CSV para guardar (o presiona Enter para usar el predeterminado): ")
        if not filename:
            # Extraer el nombre del producto de la URL
            product_name = url.split('/')[-2] if url.split('/')[-1] == '' else url.split('/')[-1]
            if product_name == "ref=pd_sim_recs_d_sccl_1_1" or not product_name or "=" in product_name:
                product_name = "producto"
            filename = f"amazon_{product_name}_comments.csv"
        
        if not filename.endswith('.csv'):
            filename += '.csv'
            
        return url, pages, use_headless, filename
    
    # Obtener input del usuario
    url, max_pages, headless, csv_filename = get_user_input()
    
    print("\n=== Configuración ===")
    print(f"URL: {url}")
    print(f"Páginas a extraer: {max_pages}")
    print(f"Modo headless: {'Sí' if headless else 'No'}")
    print(f"Archivo CSV: {csv_filename}")
    print("====================\n")
    
    # Ejecutar el scraper con opciones del usuario
    scraper = AmazonCommentsScraper(headless=headless)
    
    try:
        print(f"Extrayendo comentarios de: {url}")
        comments = scraper.get_product_comments(url, max_pages=max_pages)
        
        if comments:
            print(f"\n¡Éxito! Se encontraron {len(comments)} comentarios")
            
            # Mostrar los comentarios en la terminal
            scraper.display_comments_summary(comments, max_display=3)  # Mostrar solo los primeros 3 comentarios completos
            
            # Guardar en CSV
            scraper.save_to_csv(comments, csv_filename)
            print(f"Los datos se han guardado en: {os.path.abspath(csv_filename)}")
            
            # Preguntar si quiere ver más comentarios
            if len(comments) > 3:
                show_more = input("\n¿Quieres ver más comentarios? (s/n): ").lower() == 's'
                if show_more:
                    while True:
                        try:
                            num_to_show = int(input("¿Cuántos comentarios adicionales quieres ver? (o 0 para salir): "))
                            if num_to_show <= 0:
                                break
                                
                            start_idx = 3  # Ya hemos mostrado los primeros 3
                            end_idx = min(start_idx + num_to_show, len(comments))
                            
                            for i, comment in enumerate(comments[start_idx:end_idx], start_idx + 1):
                                scraper.print_comment(comment, i)
                                
                            if end_idx >= len(comments):
                                print("Has visto todos los comentarios disponibles.")
                                break
                                
                            start_idx = end_idx
                        except ValueError:
                            print("Por favor, introduce un número válido.")
        else:
            print("\nNo se encontraron comentarios.")
            print("Posibles razones:")
            print("1. El producto no tiene comentarios")
            print("2. Amazon está bloqueando el acceso a los comentarios")
            print("3. La estructura de la página ha cambiado")
            print("\nSugerencias:")
            print("- Intenta ejecutar sin modo headless para ver lo que ocurre")
            print("- Verifica manualmente si el producto tiene comentarios")
            print("- Prueba con otro producto de Amazon")
    
    except Exception as e:
        print(f"Error en la ejecución principal: {str(e)}")
    
    finally:
        scraper.close()
        input("\nPresiona Enter para finalizar...")

if __name__ == "__main__":
    main()