from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
#import os
import aiohttp
import asyncio
from firebase_admin import storage

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



async def download_images(image_urls, sku):
    sem = asyncio.Semaphore(5)  # Limitar a 5 descargas simultáneas
    sku_lower = sku.lower()
    
    # Lista para almacenar las URLs de las imágenes
    image_links = []

    async def download_image(session, url, index):
        async with sem:  # Adquirir el semáforo
            async with session.get(url) as response:
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

    async with aiohttp.ClientSession() as session:
        tasks = [download_image(session, url, index) for index, url in enumerate(image_urls)]
        await asyncio.gather(*tasks)

    return image_links 
