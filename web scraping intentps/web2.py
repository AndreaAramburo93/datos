import time
import os
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import random

class AmazonCommentsScraper:
    def __init__(self, headless=True):
        """Inicializa el scraper de comentarios de Amazon"""
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
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0"
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
    
    def get_product_comments(self, url, max_pages=3):
        """Extrae los comentarios de un producto de Amazon"""
        try:
            comments = []
            product_id = url.split('/')[-2] if url.split('/')[-1] == '' else url.split('/')[-1]
            product_id = product_id.split('?')[0] if '?' in product_id else product_id
            print(f"Extrayendo comentarios del producto: {product_id}")
            
            # Navegar a la página del producto
            self.driver.get(url)
            time.sleep(3)
            
            # Aceptar cookies si aparece el diálogo
            try:
                accept_cookies = self.driver.find_element(By.ID, "sp-cc-accept")
                accept_cookies.click()
                time.sleep(2)
            except NoSuchElementException:
                pass
            
            # Ir directamente a la sección de reviews modificando la URL
            reviews_url = url.split('/ref=')[0] if '/ref=' in url else url
            if not reviews_url.endswith('/'):
                reviews_url += '/'
            reviews_url += 'product-reviews/'
            
            print(f"Accediendo a: {reviews_url}")
            self.driver.get(reviews_url)
            time.sleep(3)
            
            # Si no funciona el método directo, intentar con un método alternativo
            if "product-reviews" not in self.driver.current_url:
                print("Buscando un método alternativo para acceder a comentarios...")
                self.driver.get(url)
                time.sleep(2)
                
                try:
                    # Intentar encontrar el enlace de comentarios
                    self.driver.execute_script("window.scrollBy(0, 800);")
                    time.sleep(1)
                    
                    selectors = [
                        "//a[contains(@data-hook, 'see-all-reviews-link')]",
                        "//a[contains(text(), 'comentarios')]",
                        "//a[contains(text(), 'opiniones')]",
                        "//a[contains(text(), 'reviews')]",
                        "//a[contains(@href, 'product-reviews')]",
                        "//div[contains(@id, 'reviews-summary')]//a"
                    ]
                    
                    for selector in selectors:
                        try:
                            reviews_link = self.driver.find_element(By.XPATH, selector)
                            reviews_link.click()
                            time.sleep(3)
                            break
                        except NoSuchElementException:
                            continue
                except Exception as e:
                    print(f"Error al buscar el enlace de comentarios: {str(e)}")
            
            page_count = 0
            
            while page_count < max_pages:
                print(f"Analizando página {page_count+1} de comentarios...")
                
                # Hacer scroll para cargar contenido dinámico
                for _ in range(3):
                    self.driver.execute_script("window.scrollBy(0, 500);")
                    time.sleep(0.5)
                
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
                            print(f"Se encontraron {len(review_elements)} comentarios")
                            break
                    except Exception:
                        continue
                
                if not review_elements:
                    print(f"No se han encontrado comentarios en la página {page_count+1}")
                    break
                
                for review in review_elements:
                    try:
                        # Información del usuario y fecha
                        user_info = review.find_element(By.CSS_SELECTOR, ".a-profile-name").text
                        
                        try:
                            rating_text = review.find_element(By.CSS_SELECTOR, "i[data-hook='review-star-rating'], i[data-hook='cmps-review-star-rating']").get_attribute("class")
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
                        
                        try:
                            content = review.find_element(By.CSS_SELECTOR, "[data-hook='review-body']").text.strip()
                        except NoSuchElementException:
                            content = "Sin contenido"
                        
                        try:
                            verified = "Compra verificada" in review.text
                        except:
                            verified = False
                        
                        try:
                            helpful_text = review.find_element(By.CSS_SELECTOR, "[data-hook='helpful-vote-statement']").text
                            helpful = helpful_text.split()[0] if helpful_text else "0"
                            if helpful.lower() in ["a", "una", "one"]:
                                helpful = "1"
                            elif helpful.lower() in ["dos", "two"]:
                                helpful = "2"
                        except NoSuchElementException:
                            helpful = "0"
                        
                        comments.append({
                            "producto": product_id,
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
                
                # Verificar si hay una página siguiente
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
                                self.driver.get(next_page_url)
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
                        print("No hay más páginas de comentarios.")
                        break
                        
                except Exception as e:
                    print(f"Error al navegar a la siguiente página: {str(e)}")
                    break
            
            print(f"Se extrajeron {len(comments)} comentarios para el producto {product_id}")
            return comments
        
        except Exception as e:
            print(f"Error durante el scraping: {str(e)}")
            return []
    
    def close(self):
        """Cierra el navegador"""
        if self.driver:
            self.driver.quit()


def main():
    # URLs de productos de Amazon para extraer comentarios
    urls = [
        "https://www.amazon.com/-/es/Sony-a6400-C%C3%A1mara-objetivo-intercambiable/dp/B07MTWVN3M/?_encoding=UTF8&pd_rd_w=3Lbxo&content-id=amzn1.sym.c2cf8313-b86b-4327-9de4-9398adaa570b%3Aamzn1.symc.a68f4ca3-28dc-4388-a2cf-24672c480d8f&pf_rd_p=c2cf8313-b86b-4327-9de4-9398adaa570b&pf_rd_r=VGK85Y7BZZ97MQ7HF4F0&pd_rd_wg=wmOK7&pd_rd_r=b6a31ca1-64d3-4f6c-b843-481b3e76c659&ref_=pd_hp_d_atf_ci_mcx_mr_ca_hp_atf_d&th=1",  # SSD Samsung
        "https://www.amazon.com/-/es/Canon-T6-C%C3%A1mara-r%C3%A9flex-digital/dp/B01D93Z89W/?_encoding=UTF8&pd_rd_w=3Lbxo&content-id=amzn1.sym.c2cf8313-b86b-4327-9de4-9398adaa570b%3Aamzn1.symc.a68f4ca3-28dc-4388-a2cf-24672c480d8f&pf_rd_p=c2cf8313-b86b-4327-9de4-9398adaa570b&pf_rd_r=VGK85Y7BZZ97MQ7HF4F0&pd_rd_wg=wmOK7&pd_rd_r=b6a31ca1-64d3-4f6c-b843-481b3e76c659&ref_=pd_hp_d_atf_ci_mcx_mr_ca_hp_atf_d",  # Ratón gaming
        "https://www.amazon.com/-/es/Canon-PowerShot-ELPH-360-transistores/dp/B019UDI1EE/?_encoding=UTF8&pd_rd_w=3Lbxo&content-id=amzn1.sym.c2cf8313-b86b-4327-9de4-9398adaa570b%3Aamzn1.symc.a68f4ca3-28dc-4388-a2cf-24672c480d8f&pf_rd_p=c2cf8313-b86b-4327-9de4-9398adaa570b&pf_rd_r=VGK85Y7BZZ97MQ7HF4F0&pd_rd_wg=wmOK7&pd_rd_r=b6a31ca1-64d3-4f6c-b843-481b3e76c659&ref_=pd_hp_d_atf_ci_mcx_mr_ca_hp_atf_d&th=1",  # Memoria RAM
        "https://www.amazon.com/-/es/4K-autom%C3%A1tico-fotograf%C3%ADa-bater%C3%ADas-compacta/dp/B0DHRQRLYW/ref=pd_vtp_strm_strm_cts_d_sccl_2_5/137-3222530-7772769?pd_rd_r=83f737cb-8364-4dfe-bae2-bb8c497de33e&pd_rd_wg=5JUPu&pd_rd_w=vtFz1&pd_rd_i=B0DHRQRLYW&th=1",  # Auriculares
        "https://www.amazon.com/dp/B0DSKQ5XH3/ref=sspa_dk_detail_3?pd_rd_i=B0DSKQ5XH3&pd_rd_w=aHvwq&content-id=amzn1.sym.85ceacba-39b1-4243-8f28-2e014f9512c7&pf_rd_p=85ceacba-39b1-4243-8f28-2e014f9512c7&pf_rd_r=WN253K22KG6BNFY2MRCY&pd_rd_wg=ovoiC&pd_rd_r=5b3d10e9-993e-41fc-add9-31a803244dfd&s=photo&sp_csd=d2lkZ2V0TmFtZT1zcF9kZXRhaWxfdGhlbWF0aWM&th=1"  # Smartphone
    ]
    
    # Configuración
    max_pages_per_product = 10
    headless = True  # Cambiar a False si quieres ver el navegador
    excel_filename = "amazon_comments_all.xlsx"
    
    print("=== Iniciando extracción de comentarios de Amazon ===")
    print(f"Total de productos a analizar: {len(urls)}")
    print(f"Páginas a extraer por producto: {max_pages_per_product}")
    print(f"Modo headless: {'Activado' if headless else 'Desactivado'}")
    
    # Iniciar scraper
    scraper = AmazonCommentsScraper(headless=headless)
    all_comments = []
    
    try:
        for i, url in enumerate(urls, 1):
            print(f"\n[{i}/{len(urls)}] Procesando URL: {url}")
            comments = scraper.get_product_comments(url, max_pages=max_pages_per_product)
            all_comments.extend(comments)
            
            # Esperar un tiempo aleatorio entre productos para evitar bloqueos
            wait_time = random.uniform(5, 10)
            print(f"Esperando {wait_time:.1f} segundos antes del siguiente producto...")
            time.sleep(wait_time)
        
        if all_comments:
            # Convertir a DataFrame y guardar como Excel
            df = pd.DataFrame(all_comments)
            
            # Guardar como Excel
            df.to_excel(excel_filename, index=False, engine='openpyxl')
            print(f"\n¡Éxito! Se han extraído un total de {len(all_comments)} comentarios")
            print(f"Los datos se han guardado en: {os.path.abspath(excel_filename)}")
        else:
            print("\nNo se encontraron comentarios en ninguno de los productos.")
    
    except Exception as e:
        print(f"Error en la ejecución principal: {str(e)}")
    
    finally:
        scraper.close()
        print("\nProceso finalizado.")

if __name__ == "__main__":
    main()