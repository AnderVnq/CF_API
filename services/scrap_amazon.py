from concurrent.futures import ThreadPoolExecutor
from utils.convertidores import validar_dimensiones
from utils.extractImages import extract_data_image_by_size,download_images
from utils.utils import  HTMLRenderer, get_buying_option_type, is_page_not_found,obtener_stock_y_cantidad ,obtener_precio , obtener_descripcion ,extract_size,extract_dimensions,extract_brand, size_handle_data_ctrl,extract_hard_disk_size,extract_ram,extract_dimensionsV3,extract_weight
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from amazoncaptcha import AmazonCaptcha
from datetime import datetime
from bs4 import BeautifulSoup
import asyncio
import time
from selenium.common.exceptions import WebDriverException

from selenium.webdriver.common.keys import Keys
# import firebase_admin
# from firebase_admin import credentials
#import re

# cred = credentials.Certificate('storagecampeonato-firebase-adminsdk-lwku5-11ad60cec5.json')
# firebase_admin.initialize_app(cred, {
#     'storageBucket': 'storagecampeonato.appspot.com'  # Reemplaza con tu nombre de bucket
# })



class AmazonScraper:
    def __init__(self, language='en_US'):
        self.language = language
        self.driver = self.init_driver()
        self.url_base = "https://www.amazon.com/dp/"
        self.url_base_dp= "https://www.amazon.com/dp/"
    def init_driver(self):
        """ Inicializa el WebDriver con las opciones deseadas """
        headers = {
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            'Accept': "*/*",
            'Accept-Language': self.language,
            'Accept-Encoding': "gzip,deflate,br",
            'Connection': "keep-alive"
        }
        selenium_url = 'http://selenium:4444/wd/hub'
        opts = Options()
        opts.add_argument("--headless") 
        opts.add_argument("--start-maximized")
        opts.add_argument("--disable-notifications")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--disable-extensions")
        opts.add_argument("--disable-software-rasterizer")  # Nueva opción para reducir tiempos de carga
        opts.add_argument("--no-sandbox")  # Mejora el rendimiento en algunos entornos
        opts.add_argument("--disable-dev-shm-usage")  # Mejora en sistemas con poca memoria compartida
        #opts.add_argument("--disk-cache-dir=/tmp/cache")  # Redireccionar caché para mejorar tiempos
        
        opts.add_argument("--ignore-certificate-errors")
        opts.add_argument(f'User-agent={headers["User-Agent"]}')

        # Intenta conectarte al servidor de Selenium
        print("Holaaaaaa")
        driver= webdriver.Remote(
            command_executor=selenium_url,
            options=opts
        )
        #time.sleep()
        return driver
    
    def is_captcha_page(self) -> bool:
        """ Verifica si la página actual es una página de captcha """
        try:
            captcha_container = self.driver.find_element(By.XPATH, "//div[@class='a-row a-spacing-double-large']")
            return captcha_container.is_displayed()
        except:
            return False
    
    def resolve_captcha(self):
        """ Resuelve el captcha si se encuentra en la página """
        wait = WebDriverWait(self.driver, 10)
        try:
            if not self.is_captcha_page():
                return True  # No hay captcha, continuar con el flujo normal
            
            link = wait.until(EC.presence_of_element_located((By.XPATH, "//img"))).get_attribute('src')
            captcha = AmazonCaptcha.fromlink(link)
            solution = captcha.solve()

            search_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='field-keywords']")))
            search_input.send_keys(solution)

            button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.a-button-text")))
            button.click()

            return True  # Resuelto exitosamente
        except Exception as e:
            print(f"Error al resolver el captcha: {e}")
            return False
    
    def open_page(self, variantes: list):
        """ Abre la página por cada sku para hacer el scraping / requiere una lista de dict """
        results = []
        #time.sleep(10)
        try:
            for variant in variantes:
                sku = variant.get("sku")
                #uuid = variant.get("uuid")
                if not sku :
                    print(f"Faltan SKU o UUID para la variante: {variant}")
                    continue
                url = f"{self.url_base}{sku}/?th=1&psc=1"
                self.driver.get(url)
                
                # Resolver captcha si es necesario
                if self.resolve_captcha():
                    if self.is_correct_product_page(sku):
                        result = self.extract_info(variant)
                        results.append(result)
        except Exception as e:
            print(f"Ocurrió un error: {e}")
        finally:
            self.driver.close()  # Asegúrate de que esto se ejecute
            self.driver.quit()   # Asegúrate de que esto se ejecute
        return results
    
    # def open_page(self, variante):
    #     """ Abre una página de producto en Amazon para las variantes proporcionadas """
    #     url_base = "https://www.amazon.com/gp/product/"

    #     # Asegúrate de que variante es un diccionario
    #     if not isinstance(variante, dict):
    #         print(f"Error: La variante no es un diccionario. Tipo: {type(variante)}")
    #         return None

    #     sku = variante.get("sku")
    #     uuid = variante.get("uuid")

    #     if not sku or not uuid:
    #         print(f"Faltan SKU o UUID para la variante: {variante}")
    #         return None
        
    #     url = f"{url_base}{sku}/?psc=1"
    #     print(f"Abriendo URL: {url}")
        
    #     try:
    #         self.driver.get(url)

    #         # Resolver captcha si es necesario
    #         is_resolve = self.resolve_captcha()
    #         if is_resolve:
    #             result = self.extract_info(variante)
    #             return result
    #         else:
    #             print(f"No se pudo resolver el captcha para la variante: {variante}")

    #     except Exception as e:
    #         print(f"Error abriendo la página para SKU {sku}: {e}")
    #         return None
    


    # def scrape_variants(self, variantes: list[dict]):
    #     results = []
    #     print("impresion desde scrape_variants 1", type(variantes))
    #     if variantes:  # Asegúrate de que la lista no esté vacía
    #         print("impresion desde scrape_variants 2", type(variantes[0]))

    #     # Imprimir el contenido de variantes para verificar
    #     # print(f"Contenido de variantes: {variantes}")

    #     with ThreadPoolExecutor(max_workers=3) as executor:
    #         future_to_variant = {executor.submit(self.open_page, variant): variant for variant in variantes}

    #         for future in future_to_variant:
    #             variant = future_to_variant[future]
    #             try:
    #                 result = future.result()
    #                 if result:
    #                     results.append(result)
    #             except Exception as e:
    #                 # Maneja cualquier error que ocurra al procesar la variante
    #                 print(f"Error procesando variante {variant.get('sku', 'sin SKU')}: {e}")

    #     return results
    def is_correct_product_page(self, sku: str) -> bool:
        try:
            # Verifica si el SKU está presente en la página, o busca algún elemento único del producto
            product_element = self.driver.find_element(By.ID,"dp-container")
            #print(product_element.te)
            
            # Si encuentras el título del producto o cualquier elemento relevante
            if product_element and sku in self.driver.page_source:
                return True
            else:
                return False
        except Exception as e:
            # Si hay un error (como que el elemento no existe), la página no es la correcta
            print(f"Error al verificar la página del producto para SKU {sku} pagina no encontrada")
        return False

    def extract_info(self, data: dict):
        """ Extrae información del producto en la página """
        print("SKU: ", data['sku'])
        # text_direccion=self.driver.find_element(By.ID,"glow-ingress-line2").text.strip()
        # if(text_direccion=="Perú"):
        #     boton_locacion=self.driver.find_element(By.ID,"nav-global-location-popover-link")
        #     boton_locacion.click()
        #     time.sleep(2)
        #     zipcode_input = self.driver.find_element(By.ID,"GLUXZipUpdateInput")
        #     zipcode_input.send_keys("33101")
        #     zipcode_input.send_keys(Keys.RETURN)
        #     time.sleep(2)
        #     #dar click al boton con este id GLUXConfirmClose
        #     container_popup=self.driver.find_element(By.XPATH,"//div[@class='a-popover-footer']")
        #     time.sleep(3)
        #     WebDriverWait(self.driver,10).until(
        #         EC.presence_of_element_located((By.ID,"GLUXConfirmClose"))
        #     )
        #     input_button=container_popup.find_element(By.XPATH,".//input[@id='GLUXConfirmClose']")
        #     input_button.click()
        #     time.sleep(3)



        html = self.driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        fecha_actual = datetime.now()
        # Convertir a formato de cadena
        fecha_str = fecha_actual.strftime('%Y-%m-%d %H:%M:%S.%f')
        data['last_updated']=fecha_str
        
        # Verificar si la página no se encuentra
        page_not_found = is_page_not_found(soup)
        if page_not_found:
            print(page_not_found)
            data['extraction']=0
            data['is_active']=0
            data['last_updated']=fecha_str
            data['stock'] = 0
            data['quantity'] = 0
            return data
        

        # Extraer título del producto
        try:
            titulo = self.driver.find_element(By.ID, "productTitle").text
            print(titulo)
        except Exception:
            titulo = None

        if not bool(int(data["brand_saved"])) and bool(int(data["verify_brand"])):
            brand_extract = extract_brand(soup)
            if(brand_extract):
                data["brand"] = brand_extract.strip().lower().title() 

    

        if not bool(int(data['size_saved'])) and bool(int(data['verify_size'])):
            size = extract_size(soup)
            data['size']=size



        if not bool(int(data['color_saved'])) and bool(int(data['verify_color'])):
            #print("/////color////")
            color  = self.extract_color(soup)
            data['color']=color
            #print("/////end color/////")

        if not bool(int(data.get("product_name_saved", 0))):
            if bool(int(data.get("verify_name", 0))):
                data['product_name'] = titulo.capitalize()

        # Extraer y descargar imágenes
        if not bool(int(data['is_exist_file'])) and bool(int(data['verify_images'])):
            measures=self.size_structure_data_ctrl(data,soup)
            if(measures['status'] == True):
                print("Response v1",measures)
                
                render_html=HTMLRenderer(self.driver)
                path_render =render_html.render_and_capture(measures,'image.png',False)
                print(path_render)
                
            data_images = extract_data_image_by_size(soup)
            print(data_images)
            if(data_images):
                links = asyncio.run(download_images(data_images, data.get('sku')))
                links.sort()
                if links:
                    data['main_image_url'] = links[0]
                    for i in range(min(len(links), 5)):  # Máximo 6 imágenes
                        if f'image_{i}' in data:
                            data[f'image_{i}'] = links[i]
            else:
                print("Error al obtener imagenes ")
        else:
            print("No posee tabla de tallas ")

        # Obtener descripción del producto

        if not bool(int(data['description_saved'])) and bool(int(data['verify_description'])):
            descripcion = obtener_descripcion(soup)
            print(descripcion)
            data['product_description'] = descripcion

        if not bool(int(data["ram_memory_saved"])) and bool(int(data['verify_ram'])):
            ram=extract_ram(soup)
            print("Ram",ram)
            data['ram_memory_capacity']=ram


        if not bool(int(data['storage_size_saved'])) and bool(int(data['verify_storage_size'])):
            storage_size=extract_hard_disk_size(soup)
            print("STORAGE_SIZE",storage_size)
            data['storage_size']=storage_size

        if not bool(int(data["dimension_saved"])):
            if bool(int(data["verify_dimension"])):
            # Dimensiones del producto
                dimensiones_producto = extract_dimensions(soup)
                print("Dimensiones: ", dimensiones_producto)
                if dimensiones_producto:
                    length, width, height = validar_dimensiones(dimensiones_producto)
                    if(length,width,height):
                        data['width'] = width
                        data['height'] = height
                        data['length'] = length
                else:
                    response_dimensions=extract_dimensionsV3(soup)
                    if response_dimensions:
                        dimensions = response_dimensions.get('Dimensions', {})
                        # Asignar los valores de largo, ancho y alto, si existen
                        data['length'] = dimensions.get('Length', None)
                        data['width'] = dimensions.get('Width', None)
                        data['height'] = dimensions.get('Height', None)

        if not bool(int(data['weight_saved'])) and bool(int(data["verify_weight"])):
            weight=extract_weight(soup)
            print("WEIGHT:",weight)
            data["weight_in_kg"]=weight

        # Obtener stock y cantidad máxima
        en_stock, cantidad_maxima = obtener_stock_y_cantidad(soup)
        print("existe stock: ", en_stock)
        print("Cantidad máxima: ", cantidad_maxima)

        data['stock'] = int(en_stock) if en_stock else 0
        data['quantity'] = cantidad_maxima if cantidad_maxima else 0

        # Verificar opción de compra y precio
        is_new = get_buying_option_type(soup)
        precio = obtener_precio(soup, is_new)
        print("Precio: ", precio)
        print("New: ", is_new)
        if is_new is not None:
            data['sku_label_status'] = int(is_new)
        if precio is not None:
            data['offer_price'] = precio
        # Si no hay precio, establecer stock en 0
        if precio is None:
            data['offer_price']=None
            data['stock'] = 0
        data_valid = self.validar_data_sku(data)
    
        data["extraction"]=0
        data["is_active"]= 0

        return data_valid
    

    def validar_data_sku(self,data):
        is_extraction = data['extraction']
        
        data["ram_memory_saved"] = self.valid_data_saved(data, "ram_memory_capacity")
        data["storage_size_saved"] = self.valid_data_saved(data, "storage_size")
        data["weight_saved"] = self.valid_data_saved(data, "weight_in_kg")
        data["is_exist_file"] = self.valid_images(data)
        data["brand_saved"] = self.valid_data_saved(data, "brand")
        data["dimension_saved"] = self.dimension_is_valid(data)
        data["size_saved"] = self.valid_data_saved(data, "size")
        data["color_saved"] = self.valid_data_saved(data, "color")
        data["product_name_saved"] = self.valid_data_saved(data, "product_name")
        data["description_saved"] = self.valid_data_saved(data, "product_description")


        if bool(data["allow_reset_data"]):
            verify_reset = self.reset_verification_data()
            for rst_vr in verify_reset:
                if rst_vr in data:
                    data[rst_vr] = 1

        return data




    def sizeStructureDataV2(self,data,measures_list=None):
        if measures_list is None:
            measures_list = []

        data_size = []
        size_list = []
        measures = {"measures": None, "status": False}

        if measures_list:
            size_reserved_keys_lower = data["size_reserved_keys"].lower()
            size_reserved_keys = size_reserved_keys_lower.split(',')

            for mi, msm in enumerate(measures_list):
                data_size.append({"title": msm["title"], "headers": msm["headers"], "data": []})

                for ind, td in enumerate(msm["data"]):
                    if data_size[mi]["headers"][ind].lower() not in size_reserved_keys:
                        resp = size_handle_data_ctrl(td.strip())  # Asume que esta función existe
                    else:
                        resp = td.strip()
                    size_list.append(resp)

                if size_list:
                    data_size[mi]["data"].append(size_list)
                    size_list = []

        measures["status"] = bool(data_size)
        measures["measures"] = data_size if data_size else None
        return measures
    






    def extract_color(self,soup:BeautifulSoup):

        extract_color = soup.select_one("#variation_color_name .selection")
        if extract_color:
            color=extract_color.get_text().replace('-','')
            print(color)
            return color
        
        return None
        #//div[@id="variation_color_name"]//span[@class="selection"]
        


    def size_structure_data_ctrl(self, data, soup: BeautifulSoup):
        # Seleccionamos todos los divs que contienen tanto el h5 como las tablas
        div_cont = soup.select("#centerCol #sizeChartV2Data_feature_div .a-popover-preload")
        data_size = []
        measures = {"measures": None, "status": False}
        
        if data["size_reserved_keys"] is None:
            tallas_permitidas = "'S','M','L','XL','X-Large','Large','Medium','Small'"
            data["size_reserved_keys"] = tallas_permitidas

        if div_cont:
            # Convertimos las palabras reservadas de tamaño a minúsculas
            size_reserved_keys_lower = data["size_reserved_keys"].lower()
            size_reserved_keys = size_reserved_keys_lower.split(',')
            keywords = ["US STANDARD", "US REGULAR COAT", "US REGULAR", "US HOODED SWEATSHIRT",
                        "US Acid Wash Hoodie", "US ANRABESS WOMEN'S SWEATSHIRT (PRODUCT MEASUREMENTS)",
                        "US Pullover Sweater", "US Wool Plaid Mini Skirt"]

            for div in div_cont:
                # Seleccionamos el título (h5) y verificamos si contiene alguna palabra clave
                title = div.select_one("h5")
                if title and any(keyword in title.text.strip().upper() for keyword in keywords):
                    # Seleccionamos la tabla justo debajo del h5
                    table = div.select_one("table")

                    if table:
                        headers = []
                        size_data = []
                        trs = table.select("tr")

                        for pos, tr in enumerate(trs):
                            # Procesar los encabezados
                            if pos == 0:
                                ths = tr.find_all("th")
                                for th in ths:
                                    header_value = th.text.strip()
                                    headers.append(header_value)

                            # Procesar los datos de las tallas
                            else:
                                tds = tr.find_all("td")
                                row_data = []
                                for idx, td in enumerate(tds):
                                    size_value = td.get_text(strip=True)  # Elimina espacios
                                    cleaned_value = ' '.join(size_value.split())  # Limpia espacios adicionales
                                    cleaned_value = cleaned_value.replace("\u00a0", "")  # Reemplaza espacio no rompible
                                    cleaned_value = cleaned_value.replace(" / ", "/").replace(" - ", "-")  # Limpia delimitadores

                                    # Determinar si la columna actual tiene un encabezado que contiene "(in)"
                                    current_header = headers[idx]  # Obtener el encabezado correspondiente
                                    if "(in)" in current_header:  # Solo convertir si el encabezado original contiene "(in)"
                                        resp = size_handle_data_ctrl(cleaned_value) if cleaned_value.lower() not in size_reserved_keys else cleaned_value.strip()
                                        
                                        try:
                                            # Convertir de pulgadas a centímetros
                                            converted_value = float(resp) * 2.54 if isinstance(resp, (int, float)) else float(resp)
                                            row_data.append(f"{converted_value:.2f}")  # Formato a dos decimales
                                        except (ValueError, TypeError):
                                            row_data.append(resp)  # Agregar el valor sin convertir si falla

                                    else:
                                        # Agregar el valor tal como está si no es una medida
                                        row_data.append(cleaned_value.strip())

                                # Solo agregar la fila si contiene datos
                                if row_data:
                                    size_data.append(row_data)

                        # Agregar los encabezados y los datos procesados
                        if size_data:
                            data_size.append({
                                "title": title.text.strip(),
                                "headers": headers,
                                "data": size_data
                            })

        # Solo actualizamos el status si tenemos datos en la tabla
        measures["status"] = bool(data_size)
        measures["measures"] = data_size if data_size else None
        return measures






    def reset_verification_data(self):
        props =[

            "verify_brand",
            "verify_weight",
            "verify_images",
            "verify_dimension",
            "verify_size",
            "verify_color",
            "verify_name",
            "verify_description",
            "verify_ram",
            "verify_storage_size"
        ]

        return props
    


    def valid_data_saved(self,data,prop_name):
        if data[prop_name]:
            return 1
        
        return 0
    


    def change_data_type(self):
        props=[
            "extraction",
            "stock",
            "is_active"
        ]
        return props
    



    def valid_images(self,data):
        if (
            data["image_thumbnail"] or
            data["main_image_url"] or
            data["image_0"] or
            data["image_1"] or
            data["image_2"] or
            data["image_3"] or
            data["image_4"] or
            data["image_5"] or
            data["image_size_link"]
        ):
            return 1
        return 0

    def dimension_is_valid(self,data):
        if (
            data["height"] or
            data["width"] or
            data["length"]
        ):
            return 1
        return 0
