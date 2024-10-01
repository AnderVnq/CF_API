from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
import aiohttp
import asyncio
from firebase_admin import storage
import json
from config import Config


def extract_images(driver, hover_limit=4, wait_time=2):
    """
    Extrae las URLs de las imágenes de un producto de Amazon.
    
    Parámetros:
    - driver: La instancia del navegador controlada por Selenium.
    - hover_limit: El número de miniaturas sobre las que se hace hover (predeterminado: 3).
    - wait_time: Tiempo de espera (en segundos) para que las imágenes se carguen (predeterminado: 2 segundos).
    
    Retorna:
    - Una lista con las URLs de las imágenes del producto.
    """
    images_product = []
    
    try:
        # Encuentra el contenedor de las imágenes
        container_images = driver.find_element(By.ID, "altImages")
        
        # Encuentra las miniaturas
        thumbnails = container_images.find_elements(By.XPATH, ".//input")
        
        # Miniaturas para hover (excluyendo las primeras 3)
        thumbnails_to_hover = thumbnails[3:]
        
        # Inicializa ActionChains
        actions = ActionChains(driver)
        
        # Realiza hover sobre cada miniatura para cargar las imágenes
        for index, thumbnail in enumerate(thumbnails_to_hover):
            if index >=hover_limit :
                break
            actions.move_to_element(thumbnail).perform()
            
            # Espera a que las imágenes se carguen después de hacer hover
            WebDriverWait(driver, wait_time).until(
                EC.presence_of_element_located((By.XPATH, "//div[@class='imgTagWrapper']//img"))
            )
        
        # Extrae las URLs de las imágenes cargadas
        list_images = driver.find_elements(By.XPATH, "//div[@class='imgTagWrapper']//img")
        for img in list_images:
            src = img.get_attribute("src")
            images_product.append(src)
    
    except Exception as e:
        print(f"Ocurrió un error: {e}")
        images_product = []
    
    return images_product


image_block_regex = re.compile('ImageBlockATF')

#def extract_data_image_by_size(soup):


    #script_tag = soup.find('script', text=re.compile('ImageBlockATF'))
def extract_data_image_by_size(soup):
    # Compilar la expresión regular solo una vez
    extracted_urls = []

    # Busca el script que contiene la información de las imágenes
    script_tag = soup.find('script', text=image_block_regex)
    if script_tag:
        script_content = script_tag.string.strip()

        # Limpieza del contenido del script
        match = re.search(r"'colorImages':\s*{\s*'initial':(.*?)\},\s*'colorToAsin':\s*{\s*'initial':", script_content, re.DOTALL)

        if match:
            coincidences = match.group(1).strip()  # Obtiene el contenido capturado
            #print(coincidences)
    
            if coincidences:
                # texto_for_regex = cleaned_script_content[1]
                # clean_text = texto_for_regex.split("},'colorToAsin'")[0]
                # Extraer las URLs de las imágenes
                json_data = json.loads(coincidences)
                for item in json_data:
                    if item.get('main'):
                        main_image_url = next(iter(item['main']))  # Obtiene la primera imagen
                        extracted_urls.append(main_image_url)
                        
                        # Si ya tenemos 4 URLs, rompemos el bucle
                        if len(extracted_urls) >= 4:
                            break

    if extracted_urls:
        return extracted_urls
    
    # Retornar None si no se encontraron imágenes
    return None
        # Usar una expresión regular para extraer el contenido del objeto JSON
        # match = re.search(r'=\{(.*?)\};', clean_text)
        # #print(match.string)
        # #print("match despues del sting")
        # #print(match.group(1))
        # if match:
        #     object_string = match.group(1)
        #     object_string = object_string.replace("'", '"')
        #     object_string = re.sub(r'(\w+):', r'"\1":', object_string)  # Poner las claves entre comillas
        #     object_string = object_string.rstrip(',') 
        #     #print(object_string)
        #     # Convertir la cadena de texto a un diccionario JSON
        #     json_data = json.loads('{' + object_string + '}')
        #     return json_data
        # else:
        #     print("No se encontró el objeto JSON en el script.")
        #     return None







# def extract_images_by_size(data):
#     extracted_urls = []

#     for item in data:
#         # Asegurarse de que hay al menos una imagen en 'main'
#         if item['main']:
#             # Obtener la primera imagen del 'main' directamente
#             main_image_url = next(iter(item['main']))
#             extracted_urls.append(main_image_url)

#         # Limitar el tamaño de la lista a un máximo de 6 URLs
#         if len(extracted_urls) >= 5:
#             break

#     return extracted_urls





async def download_images(image_urls, sku, max_images=4):
    sem = asyncio.Semaphore(5)  # Limitar a 5 descargas simultáneas
    sku_lower = sku.lower()
    
    # Lista para almacenar las URLs de las imágenes
    image_links = []

    # Limitar la lista de URLs a descargar a un máximo de `max_images`
    image_urls_limited = image_urls[:max_images]

    async def download_image(session, url, index):
        async with sem:  # Adquirir el semáforo
            try:
                async with session.get(url, timeout=10) as response:  # Establecer timeout de 10 segundos
                    if response.status == 200:
                        image_data = await response.read()
                        image_name = f"Public/Images/{sku_lower}/{sku_lower}_{index}.jpg"

                        # Sube la imagen a Firebase Storage
                        bucket = storage.bucket()
                        blob = bucket.blob(image_name)
                        blob.upload_from_string(image_data, content_type='image/jpeg')

                        # Obtiene la URL de descarga
                        image_url = blob.public_url
                        image_links.append(image_url)  # Agrega la URL a la lista
                        print(f"{image_name} subida a Firebase. URL: {image_url}")
                    else:
                        print(f"Error al descargar {url}: {response.status}")
            except asyncio.TimeoutError:
                print(f"Timeout al descargar {url}")
            except Exception as e:
                print(f"Error inesperado con {url}: {e}")

    async def retry_download(session, url, index, retries=3):
        for attempt in range(retries):
            try:
                await download_image(session, url, index)
                break  # Si tuvo éxito, salimos del bucle
            except Exception as e:
                print(f"Intento {attempt + 1} fallido para {url}: {e}")
                await asyncio.sleep(2)  # Esperar antes de reintentar

    async with aiohttp.ClientSession() as session:
        tasks = [retry_download(session, url, index) for index, url in enumerate(image_urls_limited)]
        await asyncio.gather(*tasks)

    return image_links