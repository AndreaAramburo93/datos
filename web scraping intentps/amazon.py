import time
import csv
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager


class AmazonReviewScraper:
    def __init__(self, url, pages=10, output_file="amazon_reviews.csv"):
        """
        Inicializa el scraper de reseñas de Amazon.
        
        Args:
            url (str): URL del producto de Amazon
            pages (int): Número de páginas de reseñas a extraer
            output_file (str): Nombre del archivo CSV para guardar las reseñas
        """
        self.url = url
        self.pages = pages
        self.output_file = output_file
        self.reviews = []
        self.setup_driver()
        
    def setup_driver(self):
        """Configura el navegador Chrome con Selenium"""
        options = Options()
        # Configuraciones para evitar detección del scraping
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        
        # User agent aleatorio
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"
        ]
        options.add_argument(f"user-agent={random.choice(user_agents)}")
        
        # Ejecutar en modo headless (sin interfaz gráfica) - opcional
        # options.add_argument("--headless")
        
        # Inicializar el driver
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        
    def get_product_info(self):
        """Obtiene información básica del producto"""
        try:
            self.driver.get(self.url)
            time.sleep(2)  # Esperar a que cargue la página
            
            product_title = self.driver.find_element(By.ID, "productTitle").text.strip()
            
            try:
                product_price = self.driver.find_element(By.ID, "priceblock_ourprice").text.strip()
            except NoSuchElementException:
                try:
                    product_price = self.driver.find_element(By.CLASS_NAME, "a-price").text.strip()
                except:
                    product_price = "Precio no disponible"
                    
            print(f"Producto: {product_title}")
            print(f"Precio: {product_price}")
            return product_title, product_price
            
        except Exception as e:
            print(f"Error al obtener información del producto: {str(e)}")
            return "Producto desconocido", "Precio desconocido"
            
    def go_to_reviews_page(self):
        """Navega a la sección de reseñas"""
        try:
            # Encontrar y hacer clic en el enlace "Ver todas las reseñas"
            try:
                all_reviews_link = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//a[contains(@data-hook,'see-all-reviews-link') or contains(text(),'Ver todas las reseñas') or contains(text(),'See all reviews')]"))
                )
                all_reviews_link.click()
            except (NoSuchElementException, TimeoutException):
                # Si no encuentra el botón específico, buscar alternativas
                try:
                    alternative_link = self.driver.find_element(By.XPATH, "//a[contains(@href,'customerReviews')]")
                    alternative_link.click()
                except:
                    print("No se pudo encontrar el enlace a las reseñas. Intentando URL directa...")
                    # Construir URL directa a las reseñas
                    base_url = self.url.split("/dp/")[0]
                    product_id = self.url.split("/dp/")[1].split("/")[0]
                    reviews_url = f"{base_url}/product-reviews/{product_id}"
                    self.driver.get(reviews_url)
                    
            time.sleep(3)  # Esperar a que cargue la página de reseñas
            return True
            
        except Exception as e:
            print(f"Error al navegar a la página de reseñas: {str(e)}")
            return False
            
    def extract_reviews_from_page(self):
        """Extrae las reseñas de la página actual"""
        try:
            wait = WebDriverWait(self.driver, 100)
            review_containers = wait.until(
                EC.presence_of_all_elements_located((By.XPATH, "//div[contains(@data-hook,'review')]"))
            )
            
            page_reviews = []
            
            for container in review_containers:
                try:
                    review = {}
                    
                    # Obtener nombre del revisor
                    try:
                        review['reviewer'] = container.find_element(By.XPATH, ".//span[contains(@class,'profile-name')]").text.strip()
                    except:
                        review['reviewer'] = "Usuario anónimo"
                    
                    # Obtener puntuación (estrellas)
                    try:
                        stars_element = container.find_element(By.XPATH, ".//i[contains(@data-hook,'review-star-rating')]/span")
                        stars_text = stars_element.get_attribute("innerHTML")
                        review['stars'] = stars_text.split(" de ")[0]
                    except:
                        try:
                            stars_element = container.find_element(By.XPATH, ".//i[contains(@class,'a-star')]/span")
                            stars_text = stars_element.get_attribute("innerHTML")
                            review['stars'] = stars_text.split(" out of ")[0]
                        except:
                            review['stars'] = "No disponible"
                    
                    # Obtener título de la reseña
                    try:
                        review['title'] = container.find_element(By.XPATH, ".//a[contains(@data-hook,'review-title')]/span").text.strip()
                    except:
                        try:
                            review['title'] = container.find_element(By.XPATH, ".//span[contains(@data-hook,'review-title')]").text.strip()
                        except:
                            review['title'] = "Sin título"
                    
                    # Obtener fecha de la reseña
                    try:
                        review['date'] = container.find_element(By.XPATH, ".//span[contains(@data-hook,'review-date')]").text.strip()
                    except:
                        review['date'] = "Fecha desconocida"
                    
                    # Obtener texto de la reseña
                    try:
                        review['text'] = container.find_element(By.XPATH, ".//span[contains(@data-hook,'review-body')]").text.strip()
                    except:
                        try:
                            review['text'] = container.find_element(By.XPATH, ".//div[contains(@class,'review-data')]/span").text.strip()
                        except:
                            review['text'] = "Sin texto"
                    
                    # Verificar si es una compra verificada
                    try:
                        verified = container.find_element(By.XPATH, ".//span[contains(text(),'Compra verificada') or contains(text(),'Verified Purchase')]")
                        review['verified'] = "Sí"
                    except:
                        review['verified'] = "No"
                        
                    page_reviews.append(review)
                    
                except Exception as e:
                    print(f"Error al procesar una reseña individual: {str(e)}")
                    continue
                    
            return page_reviews
            
        except Exception as e:
            print(f"Error al extraer reseñas de la página: {str(e)}")
            return []
            
    def go_to_next_page(self):
        """Navega a la siguiente página de reseñas"""
        try:
            next_button = self.driver.find_element(By.XPATH, "//li[@class='a-last']/a")
            next_button.click()
            time.sleep(random.uniform(2, 4))  # Espera aleatoria para evitar detección
            return True
        except NoSuchElementException:
            print("No hay más páginas de reseñas disponibles")
            return False
        except Exception as e:
            print(f"Error al navegar a la siguiente página: {str(e)}")
            return False
            
    def save_to_csv(self):
        """Guarda las reseñas extraídas en un archivo CSV"""
        try:
            with open(self.output_file, mode='w', newline='', encoding='utf-8') as file:
                if not self.reviews:
                    print("No hay reseñas para guardar")
                    return False
                    
                fieldnames = self.reviews[0].keys()
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                
                for review in self.reviews:
                    writer.writerow(review)
                    
                print(f"Se han guardado {len(self.reviews)} reseñas en {self.output_file}")
                return True
                
        except Exception as e:
            print(f"Error al guardar el archivo CSV: {str(e)}")
            return False
            
    def scrape(self):
        """Ejecuta el proceso completo de extracción de reseñas"""
        try:
            # Obtener información del producto
            product_title, product_price = self.get_product_info()
            
            # Ir a la página de reseñas
            if not self.go_to_reviews_page():
                print("No se pudo acceder a la página de reseñas")
                self.driver.quit()
                return False
                
            # Extraer reseñas de múltiples páginas
            page_num = 1
            while page_num <= self.pages:
                print(f"Extrayendo reseñas de la página {page_num} de {self.pages}...")
                
                # Extraer reseñas de la página actual
                page_reviews = self.extract_reviews_from_page()
                if page_reviews:
                    self.reviews.extend(page_reviews)
                    print(f"Se han extraído {len(page_reviews)} reseñas de la página {page_num}")
                else:
                    print(f"No se pudieron extraer reseñas de la página {page_num}")
                
                # Si hemos alcanzado el número deseado de páginas o no hay más páginas, salir del bucle
                if page_num == self.pages:
                    break
                    
                # Ir a la siguiente página
                if not self.go_to_next_page():
                    print("No hay más páginas disponibles")
                    break
                    
                page_num += 1
                
                # Pausa aleatoria entre páginas para evitar detección
                time.sleep(random.uniform(3, 7))
                
            # Guardar reseñas en CSV
            self.save_to_csv()
            
            # Cerrar el navegador
            self.driver.quit()
            
            print(f"Proceso completado. Se han extraído un total de {len(self.reviews)} reseñas")
            return True
            
        except Exception as e:
            print(f"Error durante el proceso de scraping: {str(e)}")
            self.driver.quit()
            return False


# Ejemplo de uso
if __name__ == "__main__":
    # URL del producto de Amazon
    product_url = "https://www.amazon.com/-/es/Apple-Tel%C3%A9fono-celular-desbloqueado-reacondicionado/dp/B0DHJH2GZL"
    
    # Crear y ejecutar el scraper
    scraper = AmazonReviewScraper(
        url=product_url,
        pages=10,  # Extraer reseñas de las primeras 10 páginas
        output_file="iphone_reviews.csv"  # Guardar en este archivo
    )
    
    scraper.scrape()