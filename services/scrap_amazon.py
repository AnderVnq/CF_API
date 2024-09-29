from utils.convertidores import validar_dimensiones
from utils.extractImages import extract_data_image_by_size, extract_images,download_images
from utils.utils import  get_buying_option_type, is_page_not_found,obtener_stock_y_cantidad ,obtener_precio , obtener_descripcion , extract_variations_values ,extract_size,extract_dimensions,filtrar_ropa_y_eliminar_sku,extract_brand

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from amazoncaptcha import AmazonCaptcha
from selenium.webdriver.common.keys import Keys
import time
from bs4 import BeautifulSoup
import asyncio
import firebase_admin
from firebase_admin import credentials


cred = credentials.Certificate('storagecampeonato-firebase-adminsdk-lwku5-11ad60cec5.json')
firebase_admin.initialize_app(cred, {
    'storageBucket': 'storagecampeonato.appspot.com'  # Reemplaza con tu nombre de bucket
})



def is_captcha_page(driver: webdriver.Chrome) -> bool:
    """ Verifica si la página actual es una página de captcha """
    try:
        # Puedes ajustar el selector a algo que sea característico de las páginas de captcha
        captcha_container = driver.find_element(By.XPATH, "//div[@class='a-row a-spacing-double-large']")  
        return captcha_container.is_displayed()
    except:
        return False

def resolve_captcha(driver:webdriver.Chrome):
    
    wait = WebDriverWait(driver, 10)
    try:
        # Obtener el link del captcha
        if not is_captcha_page(driver):
            # No es una página de captcha, continuar con el flujo normal
            return True
        
        link = wait.until(EC.presence_of_element_located((By.XPATH, "//img"))).get_attribute('src')
        captcha = AmazonCaptcha.fromlink(link)
        solution = captcha.solve()

        # Ingresar el texto en el input de búsqueda
        search_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='field-keywords']")))
        search_input.send_keys(solution)

        # Hacer clic en el botón
        button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.a-button-text")))
        button.click()

        return True  # Indica que la función se completó exitosamente

    except Exception as e:
        
        print(f"Error al resolver el captcha: {e}")
        return False  

def open_page(variantes: list ,language='en_US'):

    results = []
    url_base = "https://www.amazon.com/gp/product/"
    cambio_location=False
    headers={
        'User-Agent':"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        'Accept':"*/*",
        'Accept-Language': language,
        'Accept-Encoding':"gzip,deflate,br",
        'Connection':"keep-alive"
    }
    opts=Options()
    opts.add_argument("--headless") 
    opts.add_argument("--start-maximized")
    opts.add_argument("--disable-notifications")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--disable-extensions")
    opts.add_argument("--ignore-certificate-errors")
    opts.add_argument(f'User-agent={headers["User-Agent"]}')
    driver = webdriver.Chrome(options=opts)

    for variant in variantes:
        sku = variant.get("sku")
        uuid = variant.get("uuid")

        if not sku or not uuid:
            print(f"Missing sku or uuid for variant: {variant}")
            continue

        url = f"{url_base}{sku}/?psc=1"
        url_ingles = f"{url_base}{sku}/?th=1&language=en_US&psc=1" 
        driver.get(url)
        #time.sleep(2)

        is_resolve = resolve_captcha(driver)
        if is_resolve:

            # if cambio_location==False:

            #     try:
            #         #Optional: You can uncomment this if you want to set the location
            #         text_direccion = driver.find_element(By.ID, "glow-ingress-line2").text.strip()
            #         if text_direccion == "Perú" or text_direccion == "Peru":
            #             boton_locacion = driver.find_element(By.ID, "nav-global-location-popover-link")
            #             boton_locacion.click()
            #             time.sleep(2)
            #             zipcode_input = driver.find_element(By.ID, "GLUXZipUpdateInput")
            #             zipcode_input.send_keys("33101")
            #             zipcode_input.send_keys(Keys.RETURN)
            #             time.sleep(1)
            #             container_popup = driver.find_element(By.XPATH, "//div[@class='a-popover-footer']")
            #             time.sleep(4)
            #             WebDriverWait(driver, 10).until(
            #                 EC.presence_of_element_located((By.ID, "GLUXConfirmClose"))
            #             )
            #             input_button = container_popup.find_element(By.XPATH, ".//input[@id='GLUXConfirmClose']")
            #             input_button.click()
            #             time.sleep(2)
            #     except NoSuchElementException:
            #         pass

            resultado = extract_info(driver,variant)
            resultado_dic = resultado
            results.append(resultado_dic)

    return results




def extract_info(driver: webdriver.Chrome, data: dict):
    #driver.implicitly_wait(5)
    print("SKU: ", data['sku'])
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")

    # Verificar si la página no se encuentra
    page_not_found = is_page_not_found(soup)
    if page_not_found:
        print(page_not_found)
        data['stock'] = 0
        data['quantity'] = 0
        return data

    # Extraer título del producto
    try:
        titulo = driver.find_element(By.ID, "productTitle").text
        print(titulo)
    except Exception:
        titulo = None

    size = extract_size(soup)
    print(size)

    if 'product_name' in data and not bool(int(data.get("product_name_saved", 0))):
        if bool(int(data.get("verify_name", 0))):
            data['product_name'] = titulo

    # Extraer y descargar imágenes
    data_images = extract_data_image_by_size(soup)
    #imagenes = extract_images_by_size(data_images)
    print(data_images)
    links = asyncio.run(download_images(data_images, data.get('sku')))
    links.sort()
    # Obtener descripción del producto
    descripcion = obtener_descripcion(soup).replace("\n", "")
    print(descripcion)

    if 'product_description' in data and not bool(int(data.get("description_saved", 0))):
        if bool(int(data.get("verify_description", 0))):
            data['product_description'] = descripcion

    # Obtener stock y cantidad máxima
    en_stock, cantidad_maxima = obtener_stock_y_cantidad(soup)
    print("existe stock: ", en_stock)
    print("Cantidad máxima: ", cantidad_maxima)

    if en_stock is not None:
        data['stock'] = en_stock
    if cantidad_maxima is not None:
        data['quantity'] = cantidad_maxima

    # Verificar opción de compra
    is_new = get_buying_option_type(soup)
    precio = obtener_precio(soup, is_new)

    print("Precio: ", precio)
    print("New: ", is_new)

    if is_new is not None:
        data['sku_label_status'] = is_new
    if precio is not None:
        data['offer_price'] = precio


    if not bool(int(data.get("brand_saved", 0))):
        if bool(int(data.get("verify_brand", 0))):
            # Aquí iría la lógica para establecer la marca
            brand = extract_brand(soup)
            data['brand'] = brand


    # Verificar si las imágenes ya existen o si es necesario descargarlas
    if not bool(int(data["dimension_saved"])):
        if bool(int(data["verify_dimension"])):
        # Dimensiones del producto
            dimensiones_producto = extract_dimensions(soup)
    print("Dimensiones: ", dimensiones_producto)

    if dimensiones_producto:
        length, width, height = validar_dimensiones(dimensiones_producto)
        print("Largo:", length)
        print("Ancho:", width)
        print("Alto:", height)

        if 'width' in data:
            if bool(int(data.get("width_saved", 0))):  # Validación para width
                data['width'] = width
        if 'height' in data:
            if bool(int(data.get("height_saved", 0))):  # Validación para height
                data['height'] = height
        if 'length' in data:
            if bool(int(data.get("length_saved", 0))):  # Validación para length
                data['length'] = length



    # Descargar imágenes y actualizar el diccionario con las URLs

    if links:
        data['main_image_url']=links[0]

    for i in range(min(len(links), 6)):  # Asegurarse de que solo se asignen hasta 6 imágenes
        if f'image_{i}' in data:
            data[f'image_{i}'] = links[i]

    # Si no hay precio, establecer stock en 0
    if precio is None:
        data['stock'] = 0


    return data
