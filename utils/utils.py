# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.support.ui import Select
import json
import re
from bs4 import BeautifulSoup

from utils.convertidores import parse_dimensions





def sanitizar_precio(precio_normal):
    # Combina la lista en un solo string y elimina espacios en blanco al inicio y al final
    precio = ''.join(precio_normal).strip()
    
    # Reemplaza saltos de línea y otros espacios con un espacio
    precio = precio.replace('\n', ' ').replace('\r', ' ').strip()
    
    # Encuentra la parte numérica del precio usando expresiones regulares
    match = re.search(r'(\d+)(?:[.\s]*(\d+))?', precio)
    
    if match:
        # Extrae los valores entero y decimal
        entero = match.group(1)
        decimal = match.group(2) if match.group(2) else '00'  # Asegura que haya parte decimal
        precio_limpio = f"{entero}.{decimal}"  # Forma el precio como "38.99"
        
        try:
            # Convierte el precio a un número (float)
            precio_num = float(precio_limpio)
        except ValueError:
            precio_num = None  # Maneja el caso si no se puede convertir a float
    else:
        precio_num = None  # Si no se encontró un precio válido

    return precio_num




def get_buying_option_type(soup: BeautifulSoup):
    try:
        # Verificar si existe el div para productos usados en todo el DOM
        used_product_div = soup.find(id='used_buybox_desktop')
        if used_product_div:
            return False  # El producto es usado, retorna False

        # Buscar el div con los datos de precios
        objetos_div = soup.find('div', class_='a-section aok-hidden twister-plus-buying-options-price-data')

        if not objetos_div:
            return False  # Si no se encuentra el div con la información de compra, retorna False

        # Extraer el texto JSON y convertirlo en un diccionario
        price_data = json.loads(objetos_div.text)

        # Recorre los grupos para encontrar el tipo "NEW" y retorna True si lo encuentra
        for group in price_data.get("desktop_buybox_group_1", []):
            if group.get("buyingOptionType") == "NEW":
                return True  # Retorna True si el producto es nuevo

        return False  # Retorna False si no se encuentra el valor "NEW"

    except Exception as e:
        print(f"Ocurrió un error: {e}")
        return False
    

# def obtener_stock_y_cantidad(driver: webdriver.Chrome):
#     en_stock = False
#     cantidad_max = 0

#     try:
#         stock = driver.find_element(By.ID, "availability").text.strip()

#         # Verificar si está disponible o si se indica un stock limitado
#         if "Disponible" in stock or "In stock" in stock:
#             en_stock = True

#             try:
#                 # Buscar la cantidad máxima seleccionable en el dropdown
#                 cantidad_container = driver.find_element(By.ID, "quantity")
#                 select = Select(cantidad_container)
#                 opciones = select.options
#                 cantidad_max = opciones[-1].text
#                 #print("Cantidad máxima disponible:", cantidad_max)

#             except Exception:
#                 # Si no existe dropdown de cantidad, mantener la cantidad como 1 por defecto
#                 cantidad_max = 1

#         # Caso donde el stock indica un número limitado en el texto
#         else:
#             match = re.findall(r'\d+', stock)  # Encuentra todos los números en el texto
#             if match:
#                 en_stock = True
#                 cantidad_max = int(match[0]) 

#     except Exception as e:
#         print(f"Ocurrió un error: {e}")
#         en_stock = False
#         cantidad_max = 0

#     return en_stock, cantidad_max


def obtener_stock_y_cantidad(soup: BeautifulSoup):
    en_stock = False
    cantidad_max = 0

    try:
        # Buscar el texto de disponibilidad
        stock = soup.find(id="availability").get_text(strip=True)

        # Verificar si está disponible o si se indica un stock limitado
        if "Disponible" in stock or "In stock" in stock:
            en_stock = True

            # Buscar el contenedor donde se indican las cantidades
            cantidad_container = soup.find(id="quantity")
            if cantidad_container:
                # Obtener el texto del contenedor y limpiar espacios
                cantidad_texto = cantidad_container.get_text()
                # Dividir el texto en números y eliminar espacios
                cantidades = cantidad_texto.split()
                # Obtener la última cantidad, convertir a entero
                if cantidades:
                    cantidad_max = int(cantidades[-1])  # Obtener la última cantidad

            # Si no existe dropdown de cantidad, mantener la cantidad como 1 por defecto
            if cantidad_max == 0:
                cantidad_max = 1

        # Caso donde el stock indica un número limitado en el texto
        else:
            match = re.findall(r'\d+', stock)  # Encuentra todos los números en el texto
            if match:
                en_stock = True
                cantidad_max = int(match[0]) 

    except Exception as e:
        print(f"Ocurrió un error: {e}")
        en_stock = False
        cantidad_max = 0

    return en_stock, cantidad_max





def obtener_precio(soup: BeautifulSoup, is_new: bool) -> float:
    """Obtiene el precio de un producto dependiendo si es nuevo o usado."""
    precio_normal = None

    try:
        if is_new:
            # Obtener precio para producto nuevo
            precio_element = soup.select_one("#corePrice_feature_div span")
            if precio_element:
                precio_normal = precio_element.get_text(strip=True)
        else:
            # Obtener precio para producto usado
            precio_element = soup.select_one("#usedBuySection .a-size-base.a-color-price.offer-price.a-text-normal")
            if precio_element:
                precio_normal = precio_element.get_text(strip=True)

        # Sanitizar el precio y devolverlo
        if precio_normal:
            precio_sanitizado = sanitizar_precio(precio_normal)
            return precio_sanitizado

    except Exception as e:
        print(f"Ocurrió un error al obtener el precio: {e}")

    return 0.0



def obtener_descripcion(soup: BeautifulSoup) -> str:
    """Obtiene la descripción del producto desde el HTML proporcionado."""
    descripcion = 'N/A'  # Valor por defecto si no se encuentra descripción

    try:
        # Intentar obtener la descripción desde el contenedor principal
        descripcion_element = soup.find(id="feature-bullets")
        if descripcion_element:
            desc_ul = descripcion_element.find('ul')
            #print(desc_ul.get_text(strip=True))
            descripcion = desc_ul.get_text(strip=True)
        else:
            # Si no se encuentra, intentar obtener desde otro contenedor
            texto_listas = []
            descripcion_container = soup.find(id="productFactsDesktop_feature_div")
            if descripcion_container:
                descripciones = descripcion_container.find_all('ul')
                for i in descripciones:
                    texto_listas.append(i.get_text(strip=True))
                # Unir las descripciones en una sola cadena
                descripcion = "\n".join(texto_listas)
            else:
                # Si tampoco se encuentra, intentar buscar en el div 'productDescription'
                product_description = soup.find(id="productDescription")
                if product_description:
                    descripcion = product_description.get_text(strip=True)
    
    except Exception as e:
        print(f"Ocurrió un error al obtener la descripción: {e}")

    return descripcion






def extract_variations_values(soup: BeautifulSoup): 
    # Buscar todas las etiquetas <script> con type="text/javascript"
    script_tag= soup.find('script', text=re.compile('twister-js-init-dpx-data'))

    if script_tag:
        script_content = script_tag.string
        #print(script_content)

        cleaned_script_content = script_content.replace("\\n", "").replace("\\'", "'").replace(' ', '').replace("\n","")

        cleaned_script_content=cleaned_script_content.split("dimensionValuesDisplayData")
        texto_for_regex=cleaned_script_content[1]
        #print(texto_for_regex)

        pattern = r'^(.*?)(?="pwASINs)'

        # Busca el patrón en la cadena
        match = re.search(pattern,texto_for_regex)

        if match:
            result = match.group(1)[2:-1]

            json_data=json.loads(result)
            #print(json_data)
            return json_data


    return None






def extract_brand(soup:BeautifulSoup):
    # Buscar el contenido del script que contiene el JSON
    script_tag = soup.find('script', text=re.compile('rhapsodyARIngressViewModel'))

    # Si se encuentra el script, extraer el JSON
    if script_tag:
        script_content = script_tag.string

        cleaned_script_content = script_content.replace("\\n", "").replace("\\'", "'").replace(' ', '').replace("\n","")

        cleaned_script_content=cleaned_script_content.split("rhapsodyARIngressViewModel")

        texto_for_regex=cleaned_script_content[1]
        #print(texto_for_regex)
        # Usar una expresión regular para extraer el contenido del objeto JSON
        match = re.search(r'=\{(.*?)\};', texto_for_regex)
        #print(match.string)
        #print("match despues del sting")
        #print(match.group(1))
        if match:
            object_string = match.group(1)
            object_string = object_string.replace("'", '"')
            object_string = re.sub(r'(\w+):', r'"\1":', object_string)  # Poner las claves entre comillas
            object_string = object_string.rstrip(',') 
            #print(object_string)
            # Convertir la cadena de texto a un diccionario JSON
            json_data = json.loads('{' + object_string + '}')
            return json_data
        else:
            print("No se encontró el objeto JSON en el script.")
            return None
    else:
        print("No se encontró el script.")
        return None


def extract_manufacturer_from_table(soup: BeautifulSoup):
    # Buscar la tabla en los diferentes posibles IDs
    table = soup.find(id='productDetails_techSpec_section_2') or \
            soup.find(id='productDetails_techSpec_section_1') or \
            soup.find(id='productDetails_detailBullets_sections1')

    # Si se encuentra la tabla, buscar el valor del "Fabricante"
    if table:
        for row in table.find_all('tr'):
            header = row.find('th').get_text(strip=True)
            if header == "Fabricante":
                manufacturer = row.find('td').get_text(strip=True)
                return {"Fabricante": manufacturer}
    else:
        print("No se encontró ninguna tabla con la información deseada.")
    return None




def extract_size(soup):
    # Buscar el elemento utilizando el selector CSS
    element = soup.select_one('div#variation_size_name span.a-dropdown-prompt')
    
    # Si el elemento se encuentra, devolver su texto; si no, devolver None
    if element:
        return element.get_text().strip()
    else:
        return None








def extract_dimensions_and_brand(soup):
    dimensiones_producto = None
    brand_sanitizado = None

    extraction_brand = extract_brand(soup)
    if extraction_brand:
        brand_sanitizado = extraction_brand['brand']



    # Buscar la tabla de especificaciones técnicas
    table = soup.find(id='productDetails_techSpec_section_2') or \
            soup.find(id='productDetails_techSpec_section_1') or \
            soup.find(id='productDetails_detailBullets_sections1')

    if table:
        # Encontrar todas las filas de la tabla
        rows = table.find_all('tr')

        # Recorre cada fila buscando dimensiones y marca
        for row in rows:
            th = row.find('th').text.strip() if row.find('th') else ''

            if brand_sanitizado ==None:
                if "Marca" in th or "Fabricante" in th:
                    marca = row.find('td').text.strip() if row.find('td') else ''
                    brand_sanitizado = marca

            if "Dimensiones" in th or "Dimensions" in th:
                dimensiones_producto = row.find('td').text.strip() if row.find('td') else ''
                length, width, height = parse_dimensions(dimensiones_producto)
                print("Dimensiones:", dimensiones_producto)
                print("Largo", length)
                print("Ancho", width)
                print("Alto", height)

    # Si no se encontró la tabla, buscar en el div con ID 'detailBullets_feature_div'
    if not dimensiones_producto or not brand_sanitizado:
        detalles_productos_container = soup.find(id="detailBullets_feature_div")
        if detalles_productos_container:
            items = detalles_productos_container.find_all('li')

            # Recorre los elementos de la lista buscando dimensiones
            for item in items:
                label_element = item.find(class_='a-text-bold')
                label = label_element.text.strip() if label_element else ''

                if dimensiones_producto and brand_sanitizado:
                    break

                if "Dimensiones" in label or "Dimensions" in label:
                    spans = item.find_all('span')
                    if len(spans) > 2:
                        dimensiones_producto = spans[2].text.strip()
                        peso = dimensiones_producto.split(";")[1].strip() if ";" in dimensiones_producto else ''
                        # peso_convertido = parse_weight(peso)
                        length, width, height = parse_dimensions(dimensiones_producto)
                        print("Dimensiones:", dimensiones_producto)
                        print("Largo", length)
                        print("Ancho", width)
                        print("Alto", height)
                        print("Peso", peso)
                        # print("Peso convertido", peso_convertido)

    return brand_sanitizado, dimensiones_producto











def filtrar_ropa_y_eliminar_sku(diccionario, ropa, lista_skus_a_eliminar):
    # Definir las tallas permitidas
    tallas_permitidas = {"S", "M", "L", "XL","X-Large","Large","Medium","Small"}
    
    # Crear un nuevo diccionario para almacenar el resultado
    diccionario_filtrado = {}
    
    # Recorrer el diccionario
    for sku, detalles in diccionario.items():
        talla = detalles[0]  # La talla está en la primera posición de la lista
        
        # Si el SKU está en la lista de SKUs a eliminar, lo ignoramos
        if sku in lista_skus_a_eliminar:
            continue
        
        # Si ropa es True, filtrar por tallas permitidas
        if ropa:
            if talla in tallas_permitidas:
                diccionario_filtrado[sku] = detalles
        else:
            # Si ropa es False, mantenemos todos los elementos
            diccionario_filtrado[sku] = detalles

    return diccionario_filtrado














def is_page_not_found(soup:BeautifulSoup) -> bool:
    # Obtiene el HTML de la página

    
    # Busca la etiqueta <title>
    title_tag = soup.find('title')
    if title_tag:
        title_text = title_tag.text.strip()
        if "Page Not Found" in title_text or "Documento no encontrado" in title_text:
            return True

    # Verifica el contenido del <body> para mensajes de error
    body_tag = soup.find('body')
    if body_tag:
        body_text = body_tag.text.strip()
        if "Lo sentimos. La dirección web que has especificado no es una página activa de nuestro sitio." in body_text:
            return True

    return False












    # try:
    #     table = None
    #     # Buscar la tabla de detalles si está disponible
    #     #table = driver.find_element(By.ID, 'productDetails_detailBullets_sections1')productDetails_techSpec_section_1
    #     try:
    #         # Busca secuencialmente las posibles tablas
    #         table = driver.find_element(By.ID, 'productDetails_techSpec_section_2')
    #     except Exception:
    #         try:
    #             table = driver.find_element(By.ID, 'productDetails_techSpec_section_1')
    #         except Exception:
    #             try:
    #                 table = driver.find_element(By.ID, 'productDetails_detailBullets_sections1')
    #             except Exception:
    #                 table = None  # Si no se encuentra ninguna tabla, asigna None


    #     rows = table.find_elements(By.TAG_NAME, 'tr')
        
    #     # Recorre cada fila buscando dimensiones
    #     for row in rows:
    #         if dimensiones_producto and brand_sanitizado:
    #             break 
    #         th = row.find_element(By.TAG_NAME, 'th').text.strip()

    #         if "Marca" in th:
    #             marca= row.find_element(By.TAG_NAME,'td').text
    #             brand_sanitizado = marca
    #             #print("Marca",brand_sanitizado)

    #         if "Dimensiones" in th or "Dimensions" in th:
    #             dimensiones_producto = row.find_element(By.TAG_NAME, 'td').text.strip()
    #             length, width, height = parse_dimensions(dimensiones_producto)
    #             print("Dimensiones:", dimensiones_producto) 
    #             print("Largo",length)
    #             print("Ancho",width)    
    #             print("Alto",height)
    # except Exception:
    #     # Si no se encuentra la tabla, busca en el div con ID 'detailBullets_feature_div'
    #     try:

    #         extraction_brand = extract_brand(soup)
    #         if extraction_brand:
    #             brand_sanitizado=extraction_brand['brand']
            

    #         detalles_productos_container = driver.find_element(By.ID, "detailBullets_feature_div")
    #         items = detalles_productos_container.find_elements(By.TAG_NAME, 'li')
    #         # Recorre los elementos de la lista buscando ASIN y dimensiones
    #         for item in items:
    #             label_element = item.find_element(By.CLASS_NAME, 'a-text-bold')
    #             label = label_element.text.strip()
    #             if dimensiones_producto and brand_sanitizado:
    #                 break
                

    #             if "Dimensiones" in label or "Dimensions" in label:
    #                 dimensiones_producto = item.find_elements(By.TAG_NAME, 'span')[2].text
    #                 peso=dimensiones_producto.split(";")[1]
    #                 #peso_convertido=parse_weight(peso)
    #                 length, width, height = parse_dimensions(dimensiones_producto)
    #                 print("Dimensiones:", dimensiones_producto) 
    #                 print("Largo",length)
    #                 print("Ancho",width)    
    #                 print("Alto",height)
    #                 print("Peso",peso)
    #                 #print("Peso convertido",peso_convertido)
    #     except Exception:
    #         pass 

    # if(is_new):
    #     es_nuevo=True

    #     precio_normal = driver.find_element(By.XPATH,"//div[@id='corePrice_feature_div']//span").text
    #     if precio_normal:
    #         precio_sanitizado=sanitizar_precio(precio_normal)
    #         print(precio_sanitizado)
    # else:
    #     precio_normal = driver.find_element(By.XPATH,"//div[@id='usedBuySection']//span[@class='a-size-base a-color-price offer-price a-text-normal']").text
    #     if precio_normal:
    #         precio_sanitizado=sanitizar_precio(precio_normal)
    #         print(precio_sanitizado)


# def obtener_imagenes_desde_soup(soup):
#     # Buscar el script que contiene 'colorImages'
#     script = soup.find("script", text=re.compile("colorImages"))
    
#     if script:
#         # Usar expresión regular para extraer el objeto colorImages
#         pattern = re.compile(r"'colorImages':\s*({.*?})", re.DOTALL)
#         match = pattern.search(script.string)
        
#         if match:
#             try:
#                 # Convertir el objeto encontrado en un diccionario de Python
#                 color_images_json = match.group(1)
#                 color_images_data = json.loads(color_images_json)
                
#                 # Extraer las URLs de las imágenes
#                 images = color_images_data.get('initial', [])
#                 urls = []
#                 for image in images:
#                     urls.append({
#                         "hiRes": image.get('hiRes'),
#                         "thumb": image.get('thumb'),
#                         "large": image.get('large')
#                     })
                
#                 # Si no hay imágenes, devolver lista vacía
#                 return urls if urls else []
#             except json.JSONDecodeError:
#                 # Si el JSON no puede ser parseado, devolver lista vacía
#                 return []
#         else:
#             # Si no se encuentra el objeto colorImages, devolver lista vacía
#             return []
#     else:
#         # Si no se encuentra el script con colorImages, devolver lista vacía
#         return []









#precio 

    # try:
    #     descripcion=driver.find_element(By.ID,"feature-bullets").text
    #     print(descripcion)
    # except Exception :

    #     try:
    #         texto_listas=[]
    #         toggle_description= driver.find_element(By.XPATH,"//div[@id='productFactsToggleButton']//a")
    #         toggle_description.click()
    #         descripcion_container= driver.find_element(By.ID,"productFactsDesktop_feature_div")
    #         descripciones=descripcion_container.find_elements(By.TAG_NAME,'ul')
    #         for i in descripciones:
    #             texto_listas.append(i.text)

    #         descripcion="\n".join(texto_listas)
    #         print(descripcion)
    #     except:
    #         descripcion='N/A'




    # if(is_new):
    #     es_nuevo=True

    #     precio_normal = driver.find_element(By.XPATH,"//div[@id='corePrice_feature_div']//span").text
    #     if precio_normal:
    #         precio_sanitizado=sanitizar_precio(precio_normal)
    #         print(precio_sanitizado)
    # else:
    #     precio_normal = driver.find_element(By.XPATH,"//div[@id='usedBuySection']//span[@class='a-size-base a-color-price offer-price a-text-normal']").text
    #     if precio_normal:
    #         precio_sanitizado=sanitizar_precio(precio_normal)
    #         print(precio_sanitizado)


# def obtener_imagenes_desde_soup(soup):
#     # Buscar el script que contiene 'colorImages'
#     script = soup.find("script", text=re.compile("colorImages"))
    
#     if script:
#         # Usar expresión regular para extraer el objeto colorImages
#         pattern = re.compile(r"'colorImages':\s*({.*?})", re.DOTALL)
#         match = pattern.search(script.string)
        
#         if match:
#             try:
#                 # Convertir el objeto encontrado en un diccionario de Python
#                 color_images_json = match.group(1)
#                 color_images_data = json.loads(color_images_json)
                
#                 # Extraer las URLs de las imágenes
#                 images = color_images_data.get('initial', [])
#                 urls = []
#                 for image in images:
#                     urls.append({
#                         "hiRes": image.get('hiRes'),
#                         "thumb": image.get('thumb'),
#                         "large": image.get('large')
#                     })
                
#                 # Si no hay imágenes, devolver lista vacía
#                 return urls if urls else []
#             except json.JSONDecodeError:
#                 # Si el JSON no puede ser parseado, devolver lista vacía
#                 return []
#         else:
#             # Si no se encuentra el objeto colorImages, devolver lista vacía
#             return []
#     else:
#         # Si no se encuentra el script con colorImages, devolver lista vacía
#         return []









#precio 

    # try:
    #     descripcion=driver.find_element(By.ID,"feature-bullets").text
    #     print(descripcion)
    # except Exception :

    #     try:
    #         texto_listas=[]
    #         toggle_description= driver.find_element(By.XPATH,"//div[@id='productFactsToggleButton']//a")
    #         toggle_description.click()
    #         descripcion_container= driver.find_element(By.ID,"productFactsDesktop_feature_div")
    #         descripciones=descripcion_container.find_elements(By.TAG_NAME,'ul')
    #         for i in descripciones:
    #             texto_listas.append(i.text)

    #         descripcion="\n".join(texto_listas)
    #         print(descripcion)
    #     except:
    #         descripcion='N/A'