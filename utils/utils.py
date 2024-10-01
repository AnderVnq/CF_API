import json
import re
from bs4 import BeautifulSoup
import os
from utils.convertidores import inch_to_centimeter
import time
from PIL import Image
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC






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
        # Comprobar si el producto es usado directamente
        if soup.find(id='used_buybox_desktop'):
            return False  # El producto es usado, retorna False

        # Buscar el div con los datos de precios
        objetos_div = soup.find('div', class_='a-section aok-hidden twister-plus-buying-options-price-data')
        
        # Retornar False si no se encuentra el div
        if not objetos_div or not objetos_div.text.strip():
            return False

        # Extraer y procesar el JSON en una sola línea
        price_data = json.loads(objetos_div.text)

        # Retornar True si se encuentra un grupo con tipo "NEW"
        return any(group.get("buyingOptionType") == "NEW" for group in price_data.get("desktop_buybox_group_1", []))

    except json.JSONDecodeError:
        print("Error al decodificar el JSON de precios.")
        return False
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")
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
    cantidad_max = None  # Inicializar en None

    try:
        # Buscar el texto de disponibilidad y limpiar espacios
        stock = soup.find(id="availability").get_text(strip=True)

        # Verificar disponibilidad
        if "Disponible" in stock or "In stock" in stock:
            en_stock = True

            # Buscar el contenedor de cantidad
            cantidad_container = soup.find(id="quantity")
            if cantidad_container:
                # Obtener la última cantidad en el texto
                cantidad_texto = cantidad_container.get_text()
                cantidades = cantidad_texto.split()
                if cantidades:  # Si hay cantidades disponibles
                    try:
                        cantidad_max = int(cantidades[-1])  # Obtener la última cantidad
                    except ValueError:
                        cantidad_max = None  # Mantener como None si no se puede convertir

        # Verificar si hay stock limitado en el texto
        elif match := re.search(r'\d+', stock):  # Usar el operador walrus para simplificar
            en_stock = True
            cantidad_max = int(match.group(0))  # Obtener el primer número encontrado

    except Exception as e:
        print(f"Ocurrió un error: {e}")

    return en_stock, cantidad_max





def obtener_precio(soup: BeautifulSoup, is_new: bool) -> float:
    """Obtiene el precio de un producto dependiendo si es nuevo o usado."""
    
    try:
        # Determinar el selector según el tipo de producto
        selector = "#corePrice_feature_div span" if is_new else "#usedBuySection .a-size-base.a-color-price.offer-price.a-text-normal"
        precio_element = soup.select_one(selector)
        
        if precio_element:
            precio_normal = precio_element.get_text(strip=True)
            # Sanitizar el precio y devolverlo
            return sanitizar_precio(precio_normal)

    except Exception as e:
        print(f"Ocurrió un error al obtener el precio: {e}")

    return None


def obtener_descripcion(soup: BeautifulSoup) -> str:
    """Obtiene la descripción del producto desde el HTML proporcionado."""
    
    try:
        # Intentar obtener la descripción desde diferentes contenedores en orden de preferencia
        for container_id in ["feature-bullets", "productFactsDesktop_feature_div", "productDescription"]:
            descripcion_element = soup.find(id=container_id)
            if descripcion_element:
                # Si se encuentra un contenedor, obtener el texto
                if container_id == "feature-bullets":
                    desc_ul = descripcion_element.find('ul')
                    return desc_ul.get_text(strip=True) if desc_ul else None
                else:
                    # Para otros contenedores, obtener todas las listas
                    texto_listas = [ul.get_text(strip=True) for ul in descripcion_element.find_all('ul')]
                    return "\n".join(texto_listas) if texto_listas else None
    
    except Exception as e:
        print(f"Ocurrió un error al obtener la descripción: {e}")

    return None






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




def extract_brandV1(soup: BeautifulSoup):
    """Extrae la marca del producto desde el script que contiene el JSON."""
    
    # Buscar el script que contiene el JSON de la marca
    script_tag = soup.find('script', text=re.compile('rhapsodyARIngressViewModel'))

    if script_tag:
        # Extraer y limpiar el contenido del script
        script_content = script_tag.string
        cleaned_script_content = re.sub(r"\\n|\\'", "", script_content).replace(" ", "").replace("\n", "")
        
        # Extraer el objeto JSON utilizando una expresión regular
        match = re.search(r'rhapsodyARIngressViewModel\s*=\s*\{(.*?)\};', cleaned_script_content)

        if match:
            object_string = match.group(1)
            object_string = re.sub(r"'", '"', object_string)  # Reemplazar comillas simples por dobles
            object_string = re.sub(r'(\w+):', r'"\1":', object_string)  # Poner las claves entre comillas
            object_string = object_string.rstrip(',')  # Eliminar la coma final
            
            # Convertir la cadena de texto a un diccionario JSON
            json_data = json.loads('{' + object_string + '}')
            return json_data

        print("No se encontró el objeto JSON en el script.")
        return None

    print("No se encontró el script.")
    return None





def extract_brand(soup: BeautifulSoup) -> str:
    """Extrae la marca utilizando v1 o v2 según corresponda."""
    
    brand = extract_brandV1(soup)

    if brand is None:
        brand = extract_brandV2(soup)

    return brand






def size_handle_data_ctrl(text):
    # Remover "inch" del texto
    text = re.sub(r'\s*inch\s*', '', text, flags=re.I)

    # Detectar "/" o "-" y dividir el texto, y guardar el delimitador
    match = re.search(r'[\/-]', text)
    if match:
        delimiter = match.group(0)
        parts = text.split(delimiter)
    else:
        # Si no se encuentra ningún delimitador, solo devolvemos el texto convertido
        parts = [text]
        delimiter = ''

    # Convertir cada parte de pulgadas a centímetros
    def inches_to_cm(part):
        part = part.strip()
        if part.replace('.', '', 1).isdigit():  # Verifica si es numérico, incluyendo decimales
            cm_value = float(part) * 2.54  # Convierte pulgadas a centímetros
            return f"{cm_value:.2f}"  # Formatear a dos decimales
        return part

    # Aplicar la conversión a todas las partes
    converted_parts = [inches_to_cm(part) for part in parts]

    # Concatenar las partes convertidas usando el delimitador original
    result = delimiter.join(converted_parts)
    return result




def size_handle_data_ctrl(text):
    # Remover "inch" del texto
    text = re.sub(r'\s*inch\s*', '', text, flags=re.IGNORECASE)
    
    # Detectar "/" o "-" y dividir el texto, y guardar el delimitador
    delimiter = None
    parts = []
    if '/' in text or '-' in text:
        if '/' in text:
            delimiter = '/'
        else:
            delimiter = '-'
        parts = text.split(delimiter)
    else:
        parts = [text]  # Si no hay delimitador, solo devolvemos el texto
    # Convertir cada parte de pulgadas a centímetros
    converted_parts = []
    for part in parts:
        part = part.strip()
        # Asegurarse de que es un número
        if part.isnumeric():
            cm_value = format_number_ctrl(inch_to_centimeter(float(part)))
            converted_parts.append(cm_value)
        else:
            converted_parts.append(part)  # Si no es un número, se mantiene como está
    # Concatenar las partes convertidas usando el delimitador original
    result = delimiter.join(map(str, converted_parts)) if delimiter else ''.join(map(str, converted_parts))
    
    return result






def format_number_ctrl(value):
    # Formatear el número según sea necesario
    return round(value, 2)



# def extract_brand(soup:BeautifulSoup):
#     # Buscar el contenido del script que contiene el JSON
#     script_tag = soup.find('script', text=re.compile('rhapsodyARIngressViewModel'))

#     # Si se encuentra el script, extraer el JSON
#     if script_tag:
#         script_content = script_tag.string

#         cleaned_script_content = script_content.replace("\\n", "").replace("\\'", "'").replace(' ', '').replace("\n","")

#         cleaned_script_content=cleaned_script_content.split("rhapsodyARIngressViewModel")

#         texto_for_regex=cleaned_script_content[1]
#         #print(texto_for_regex)
#         # Usar una expresión regular para extraer el contenido del objeto JSON
#         match = re.search(r'=\{(.*?)\};', texto_for_regex)
#         #print(match.string)
#         #print("match despues del sting")
#         #print(match.group(1))
#         if match:
#             object_string = match.group(1)
#             object_string = object_string.replace("'", '"')
#             object_string = re.sub(r'(\w+):', r'"\1":', object_string)  # Poner las claves entre comillas
#             object_string = object_string.rstrip(',') 
#             #print(object_string)
#             # Convertir la cadena de texto a un diccionario JSON
#             json_data = json.loads('{' + object_string + '}')
#             return json_data
#         else:
#             print("No se encontró el objeto JSON en el script.")
#             return None
#     else:
#         print("No se encontró el script.")
#         return None


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


def ignore_irrelevant_dimensions_label(th_text):
    """Ignora etiquetas que contienen palabras irrelevantes para dimensiones."""
    th_text = th_text.lower()  # Convertir a minúsculas para comparaciones consistentes
    ignored_keywords = [
        "display dimensions", "pantalla artículo", 
        "item display dimensions", "dimensiones pantalla"
    ]
    return any(keyword in th_text for keyword in ignored_keywords)

def extract_dimensions(soup: BeautifulSoup) -> str:
    """Extrae dimensiones del producto desde el HTML proporcionado."""
    
    dimensiones_producto = None

    # Buscar la tabla de especificaciones técnicas
    tables = [
        soup.find(id='productDetails_techSpec_section_2'),
        soup.find(id='productDetails_techSpec_section_1'),
        soup.find(id='productDetails_detailBullets_sections1'),
        *soup.find_all("table", "a-keyvalue prodDetTable"),
    ]

    for table in tables:
        if not table:
            continue  # Saltar si la tabla no existe

        rows = table.find_all('tr')
        for row in rows:
            th = row.find('th').text.strip() if row.find('th') else ''

            # Ignorar si el encabezado contiene palabras irrelevantes
            if ignore_irrelevant_dimensions_label(th):
                continue  # Saltar esta fila si contiene términos irrelevantes

            # Extraer dimensiones
            if any(keyword in th for keyword in ["Dimensiones", "Dimensions"]):
                dimensiones_producto = row.find('td').text.strip() if row.find('td') else ''
                #print("Dimensiones:", dimensiones_producto)  # Para depuración
                break  # Salir del bucle si se encuentra dimensiones

        if dimensiones_producto:
            break  # Salir si se han encontrado dimensiones

    # Si no se encontró en la tabla, buscar en el div con ID 'detailBullets_feature_div'
    if not dimensiones_producto:
        detalles_productos_container = soup.find(id="detailBullets_feature_div")
        if detalles_productos_container:
            items = detalles_productos_container.find_all('li')

            for item in items:
                label_element = item.find(class_='a-text-bold')
                label = label_element.text.strip() if label_element else ''

                # Ignorar si el encabezado contiene palabras irrelevantes
                if ignore_irrelevant_dimensions_label(label):
                    continue  # Saltar este elemento si contiene términos irrelevantes

                # Extraer dimensiones
                if any(keyword in label for keyword in ["Dimensiones", "Dimensions"]):
                    spans = item.find_all('span')
                    if len(spans) > 2:
                        dimensiones_producto = spans[2].text.strip()
                        peso = dimensiones_producto.split(";")[1].strip() if ";" in dimensiones_producto else ''
                        print("Peso:", peso)  # Para depuración
                        break  # Salir si se encuentra dimensiones

    return dimensiones_producto




def extract_brandV2(soup: BeautifulSoup) -> str:
    """Extrae la marca del producto desde el HTML proporcionado."""
    
    brand_sanitizado = None
    # brand_data = extract_brand(soup)

    # if brand_data is not None:
    #     brand_sanitizado = brand_data.get('brand')

    # Buscar la tabla de especificaciones técnicas
    tables = [
        soup.find(id='productDetails_techSpec_section_2'),
        soup.find(id='productDetails_techSpec_section_1'),
        soup.find(id='productDetails_detailBullets_sections1'),
        *soup.find_all("table", "a-keyvalue prodDetTable"),
    ]

    for table in tables:
        if not table:
            continue  # Saltar si la tabla no existe

        rows = table.find_all('tr')
        for row in rows:
            th = row.find('th').text.strip() if row.find('th') else ''

            # Ignorar si el encabezado contiene palabras irrelevantes
            if ignore_irrelevant_dimensions_label(th):
                continue  # Saltar esta fila si contiene términos irrelevantes

            # Extraer marca
            if brand_sanitizado is None and any(keyword in th for keyword in ["Marca", "Brand", "Fabricante"]):
                brand_sanitizado = row.find('td').text.strip() if row.find('td') else ''

            # Salir si se ha encontrado la marca
            if brand_sanitizado:
                break

        if brand_sanitizado:
            break  # Salir si se ha encontrado la marca

    return brand_sanitizado








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














def is_page_not_found(soup: BeautifulSoup) -> bool:
    """Verifica si la página mostrada es un error de 'Página no encontrada'."""
    
    # Lista de palabras clave que indican que la página no se encontró
    keywords = [
        "Page Not Found",
        "Documento no encontrado",
        "Lo sentimos. La dirección web que has especificado no es una página activa de nuestro sitio."
    ]
    
    # Comprueba el título de la página
    title_tag = soup.title
    if title_tag and any(keyword in title_tag.text for keyword in keywords[:2]):
        return True
    
    # Comprueba el cuerpo de la página
    body_text = soup.body.get_text(strip=True) if soup.body else ""
    if any(keyword in body_text for keyword in keywords[2:]):
        return True

    return False










class HTMLRenderer:
    def __init__(self, driver):
        self.driver = driver  # Driver de Selenium inicializado

    def generate_html_table(self, data):
        """Genera una estructura HTML de tabla a partir de los datos con los estilos proporcionados."""
        headers = ''.join([f'<th>{header}</th>' for header in data['measures'][0]['headers']])
        rows = ''.join([
            '<tr>' + ''.join([f'<td>{col}</td>' for col in row]) + '</tr>'
            for row in data['measures'][0]['data']
        ])
        
        html_structure = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Table</title>
            <style>
                html {{
                    display: flex;
                    align-items: center;
                    flex-direction: column;
                    gap: 16px;
                    justify-content: center;
                    width: 100%;                    
                }}
                body {{
                    max-width: 1024px;
                    display: flex;
                    align-items: center;
                    flex-direction: column;
                    gap: 30px;
                    justify-content: center;
                    width: 100%;
                    padding:4px;  
                }}
                .content_group {{
                    width: 100%;
                    padding: 12px;
                }}
                table {{
                    width: 100%;
                    border-collapse: separate;
                    border-spacing: 0;
                    border: 1px solid #9f9f9f;
                    border-radius: 10px;
                    overflow: hidden;
                }}
                th {{
                    color: #222;
                    font-size: 12px;
                }}
                td {{
                    font-size: 12px;
                }}
                th, td {{
                    padding: 6px;
                    text-align: left;
                    border-bottom: 1px solid #9f9f9f;
                }}
                th:first-child, td:first-child {{
                    color: #222 !important;
                    font-weight: 600;
                }}
                tr:last-child th, tr:last-child td {{
                    border-bottom: none;
                }}
                th:first-child, td:first-child {{
                    border-left: 1px solid #9f9f9f;
                }}
                th:last-child, td:last-child {{
                    border-right: 1px solid #9f9f9f;
                }}
                .table-title {{
                    font-weight: 600;
                    color: #222;
                    text-align: center;
                    font-size: 14px;
                    margin-bottom: 10px;
                }}
            </style>
        </head>
        <body>
            <div class="content_group">
                <div class="table-title">{data['measures'][0]['title']}</div>
                <table>
                    <thead>
                        <tr>{headers}</tr>
                    </thead>
                    <tbody>
                        {rows}
                    </tbody>
                </table>
            </div>
        </body>
        </html>
        """
        return html_structure

    def save_html_to_file(self, html_content, file_name='table.html'):
        """Guarda la estructura HTML en un archivo."""
        file_path = os.path.join(os.getcwd(), file_name)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        return file_path

    def render_and_capture(self, data, output_image='screenshot.png', delete_after_capture=False):
        """Genera el HTML, lo carga en el navegador, toma una captura de pantalla, y opcionalmente elimina la captura."""
        # Generar el HTML de la tabla con los datos
        html_content = self.generate_html_table(data)

        # Guardar el HTML en un archivo temporal
        html_file_path = self.save_html_to_file(html_content)

        try:
            # Cargar el archivo HTML localmente en el navegador
            self.driver.get(f"file://{html_file_path}")
            
            # Esperar a que la tabla sea visible en el DOM
            WebDriverWait(self.driver, 10).until(EC.visibility_of_element_located((By.TAG_NAME, 'table')))
            
            # Encuentra la tabla usando Selenium
            table_element = self.driver.find_element(By.TAG_NAME, 'table')

            # Obtener las dimensiones de la tabla
            location = table_element.location
            size = table_element.size

            # Tomar captura de pantalla de toda la página
            screenshot_path = os.path.join(os.getcwd(), output_image)
            self.driver.save_screenshot(screenshot_path)

            # Usar PIL para recortar la captura de pantalla solo a la tabla
            image = Image.open(screenshot_path)
            left = location['x']
            top = location['y']
            right = left + size['width'] - 75
            bottom = top + size['height'] +20
            cropped_image = image.crop((left, top, right, bottom))

            # Guardar la imagen recortada
            cropped_image.save(screenshot_path)

            # Verificar si se debe eliminar la captura después de guardarla
            if delete_after_capture:
                if os.path.exists(screenshot_path):
                    os.remove(screenshot_path)
                    return f"La captura de pantalla '{output_image}' ha sido eliminada."
                else:
                    return f"Error: No se encontró la captura de pantalla '{output_image}' para eliminar."

            return screenshot_path  # Devuelve la ruta de la captura de pantalla si no se elimina

        except Exception as e:
            return f"Error al procesar: {e}"

        finally:
            # Siempre eliminar el archivo HTML temporal después de la captura
            if os.path.exists(html_file_path):
                os.remove(html_file_path)

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