from concurrent.futures import ThreadPoolExecutor
from utils.convertidores import inch_to_centimeter, validar_dimensiones
from utils.extractImages import extract_data_image_by_size, extract_images,download_images
from utils.utils import  HTMLRenderer, format_number_ctrl, get_buying_option_type, is_page_not_found,obtener_stock_y_cantidad ,obtener_precio , obtener_descripcion , extract_variations_values ,extract_size,extract_dimensions,filtrar_ropa_y_eliminar_sku,extract_brand, size_handle_data_ctrl
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from amazoncaptcha import AmazonCaptcha
# from selenium.webdriver.common.keys import Keys
# import time
from datetime import datetime
from bs4 import BeautifulSoup
import asyncio
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
    
    def init_driver(self):
        """ Inicializa el WebDriver con las opciones deseadas """
        headers = {
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            'Accept': "*/*",
            'Accept-Language': self.language,
            'Accept-Encoding': "gzip,deflate,br",
            'Connection': "keep-alive"
        }
        
        opts = Options()
        opts.add_argument("--headless") 
        opts.add_argument("--start-maximized")
        opts.add_argument("--disable-notifications")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--disable-extensions")
        opts.add_argument("--ignore-certificate-errors")
        opts.add_argument(f'User-agent={headers["User-Agent"]}')
        return webdriver.Chrome(options=opts)
    
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
    
    # def open_page(self, variantes: list):
    #     """ Abre una página de producto en Amazon para las variantes proporcionadas """
    #     results = []
    #     url_base = "https://www.amazon.com/gp/product/"

    #     for variant in variantes:

    #         #print(type(variant))
    #         sku = variant.get("sku")
    #         uuid = variant.get("uuid")
    #         if not sku or not uuid:
    #             print(f"Faltan SKU o UUID para la variante: {variant}")
    #             continue
    #         url = f"{url_base}{sku}/?psc=1"
    #         self.driver.get(url)
    #         # Resolver captcha si es necesario
    #         is_resolve = self.resolve_captcha()
    #         if is_resolve:
    #             result = self.extract_info(variant)
    #         results.append(result)
    #     return results
    
    def open_page(self, variante):
        """ Abre una página de producto en Amazon para las variantes proporcionadas """
        url_base = "https://www.amazon.com/gp/product/"

        # Asegúrate de que variante es un diccionario
        if not isinstance(variante, dict):
            print(f"Error: La variante no es un diccionario. Tipo: {type(variante)}")
            return None

        sku = variante.get("sku")
        uuid = variante.get("uuid")

        if not sku or not uuid:
            print(f"Faltan SKU o UUID para la variante: {variante}")
            return None
        
        url = f"{url_base}{sku}/?psc=1"
        print(f"Abriendo URL: {url}")
        
        try:
            self.driver.get(url)

            # Resolver captcha si es necesario
            is_resolve = self.resolve_captcha()
            if is_resolve:
                result = self.extract_info(variante)
                return result
            else:
                print(f"No se pudo resolver el captcha para la variante: {variante}")

        except Exception as e:
            print(f"Error abriendo la página para SKU {sku}: {e}")
            return None
    


    def scrape_variants(self, variantes: list[dict]):
        results = []
        print("impresion desde scrape_variants 1", type(variantes))
        if variantes:  # Asegúrate de que la lista no esté vacía
            print("impresion desde scrape_variants 2", type(variantes[0]))

        # Imprimir el contenido de variantes para verificar
        # print(f"Contenido de variantes: {variantes}")

        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_variant = {executor.submit(self.open_page, variant): variant for variant in variantes}

            for future in future_to_variant:
                variant = future_to_variant[future]
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                except Exception as e:
                    # Maneja cualquier error que ocurra al procesar la variante
                    print(f"Error procesando variante {variant.get('sku', 'sin SKU')}: {e}")

        return results


    def extract_info(self, data: dict):
        """ Extrae información del producto en la página """
        print("SKU: ", data['sku'])
        html = self.driver.page_source
        soup = BeautifulSoup(html, "html.parser")

        # Verificar si la página no se encuentra
        page_not_found = is_page_not_found(soup)
        if page_not_found:
            print(page_not_found)
            fecha_actual = datetime.now()
            # Convertir a formato de cadena
            fecha_str = fecha_actual.strftime('%Y-%m-%d %H:%M:%S.%f')
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


        fecha_actual = datetime.now()

        # Convertir a formato de cadena
        fecha_str = fecha_actual.strftime('%Y-%m-%d %H:%M:%S.%f')

        data['last_updated']=fecha_str

        if not bool(int(data['size_saved'])) and bool(int(data['verify_size'])):
            size = extract_size(soup)
            print("Size",size)

        if "brand" in data and not bool(int(data["brand_saved"])) and bool(int(data["verify_brand"])):
            data["brand"] = data["brand"].strip().lower().title() 


        if not bool(int(data['color_saved'])) and bool(int(data['verify_color'])):
            
            print("validando color")
        print("/////color////")
        self.extract_color(soup)
        print("/////end color/////")

        if 'product_name' in data and not bool(int(data.get("product_name_saved", 0))):
            if bool(int(data.get("verify_name", 0))):
                data['product_name'] = titulo

        # Extraer y descargar imágenes
        data_images = extract_data_image_by_size(soup)
        print(data_images)
        if(data_images):
            links = asyncio.run(download_images(data_images, data.get('sku')))
            links.sort()
        else:
            print("Error al obtener imagenes ")
        # Obtener descripción del producto

        if not bool(int(data['description_saved'])) and bool(int(data['verify_description'])):
                descripcion = obtener_descripcion(soup).replace("\n", "")
                print(descripcion)
                data['product_description'] = descripcion


        if not bool(int(data["dimension_saved"])):
            if bool(int(data["verify_dimension"])):
            # Dimensiones del producto
                dimensiones_producto = extract_dimensions(soup)
                print("Dimensiones: ", dimensiones_producto)
                if dimensiones_producto:
                    length, width, height = validar_dimensiones(dimensiones_producto)
                    if(length,width,height):
                        print("Largo:", length)
                        print("Ancho:", width)
                        print("Alto:", height)
                        data['width'] = width
                        data['height'] = height
                        data['length'] = length


        # Obtener stock y cantidad máxima
        en_stock, cantidad_maxima = obtener_stock_y_cantidad(soup)
        print("existe stock: ", en_stock)
        print("Cantidad máxima: ", cantidad_maxima)

        if en_stock is not None:
            data['stock'] = en_stock
        if cantidad_maxima is not None:
            data['quantity'] = cantidad_maxima

        # Verificar opción de compra y precio
        is_new = get_buying_option_type(soup)
        precio = obtener_precio(soup, is_new)

        print("Precio: ", precio)
        print("New: ", is_new)

        if is_new is not None:
            data['sku_label_status'] = is_new
        if precio is not None:
            data['offer_price'] = precio

        # Descargar imágenes y actualizar el diccionario con las URLs
        if links:
            data['main_image_url'] = links[0]

            for i in range(min(len(links), 6)):  # Máximo 6 imágenes
                if f'image_{i}' in data:
                    data[f'image_{i}'] = links[i]

        # Si no hay precio, establecer stock en 0
        if precio is None:
            data['stock'] = 0
        

        measures=self.size_structure_data_ctrl(data,soup)
        if(measures['status'] == True):
            print("Response v1",measures)



            if not bool(int(data['is_exist_file'])) and bool(int(data['verify_images'])):
                render_html=HTMLRenderer(self.driver)
                path_render =render_html.render_and_capture(measures,'image.png',False)
                print(path_render)

        else:
            print("No posee tabla de tallas ")
        #     

        #     print("size: ",response_size)


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
            print(extract_color.get_text().replace('-',''))
        #//div[@id="variation_color_name"]//span[@class="selection"]
        


    def size_structure_data_ctrl(self, data, soup: BeautifulSoup):
        # Seleccionamos todos los divs que contienen tanto el h5 como las tablas
        div_cont = soup.select("#centerCol #sizeChartV2Data_feature_div .a-popover-preload")
        data_size = []
        measures = {"measures": None, "status": False}

        if div_cont:
            # Convertimos las palabras reservadas de tamaño a minúsculas
            size_reserved_keys_lower = data["size_reserved_keys"].lower()
            size_reserved_keys = size_reserved_keys_lower.split(',')
            keywords = ["US STANDARD", "US REGULAR COAT", "US REGULAR"]
            for div in div_cont:
                # Seleccionamos el título (h5) y verificamos si contiene "US STANDARD"
                title = div.select_one("h5")
                print(title.text.strip().upper())
                if title and any(keyword in title.text.strip().upper() for keyword in keywords):  # Verifica si el texto contiene "US STANDARD"
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
                                    header_value = th.text.strip().replace("(in)", "(cm)")
                                    if header_value not in headers:
                                        headers.append(header_value)

                            # Procesar los datos de las tallas
                            else:
                                tds = tr.find_all("td")
                                row_data = []
                                for td in tds:
                                    size_value = td.get_text(strip=True)  # Elimina espacios
                                    cleaned_value = ' '.join(size_value.split())  # Limpia espacios adicionales
                                    cleaned_value = cleaned_value.replace("\u00a0", "")  # Reemplaza espacio no rompible
                                    cleaned_value = cleaned_value.replace(" / ", "/").replace(" - ", "-")  # Limpia delimitadores
                                    contains_cm = any("cm" in header for header in headers)
                                    # Procesar el valor de la talla
                                    if contains_cm :
                                        resp = (size_handle_data_ctrl(cleaned_value) 
                                                if cleaned_value.lower() not in size_reserved_keys 
                                                else cleaned_value.strip())
                                        row_data.append(resp)
                                    else:
                                        resp = cleaned_value.strip()
                                        row_data.append(resp)
                                # Solo agregar la fila si contiene datos
                                if row_data:
                                    size_data.append(row_data)

                        # Agregar los encabezados y los datos procesados
                        data_size.append({"title": title.text.strip(), "headers": headers, "data": size_data})

        # Solo actualizamos el status si tenemos datos en la tabla
        measures["status"] = bool(data_size)
        measures["measures"] = data_size if data_size else None
        return measures
