from utils.convertidores import parse_dimensions , parse_weight
from utils.extractImages import extract_images,download_images
from utils.utils import  get_buying_option_type, is_page_not_found,obtener_stock_y_cantidad ,obtener_precio , obtener_descripcion , extract_variations_values ,extract_size,extract_dimensions_and_brand,filtrar_ropa_y_eliminar_sku
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
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


def iniciar_webdriver(language='en_US'):

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
    return driver




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

def open_page(driver: webdriver.Chrome, variantes: list):
    results = []
    url_base = "https://www.amazon.com/gp/product/"

    for variant in variantes:
        sku = variant.get("sku")
        uuid = variant.get("uuid")

        if not sku or not uuid:
            print(f"Missing sku or uuid for variant: {variant}")
            continue

        url = f"{url_base}{sku}/?psc=1"
        url_ingles = f"{url_base}{sku}/?th=1&language=en_US&psc=1" 
        driver.get(url)
        time.sleep(2)

        is_resolve = resolve_captcha(driver)
        if is_resolve:
            try:
                #Optional: You can uncomment this if you want to set the location
                text_direccion = driver.find_element(By.ID, "glow-ingress-line2").text.strip()
                if text_direccion == "Perú" or text_direccion == "Peru":
                    boton_locacion = driver.find_element(By.ID, "nav-global-location-popover-link")
                    boton_locacion.click()
                    time.sleep(2)
                    zipcode_input = driver.find_element(By.ID, "GLUXZipUpdateInput")
                    zipcode_input.send_keys("33101")
                    zipcode_input.send_keys(Keys.RETURN)
                    time.sleep(1)
                    container_popup = driver.find_element(By.XPATH, "//div[@class='a-popover-footer']")
                    time.sleep(4)
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.ID, "GLUXConfirmClose"))
                    )
                    input_button = container_popup.find_element(By.XPATH, ".//input[@id='GLUXConfirmClose']")
                    input_button.click()
                    time.sleep(2)
            except NoSuchElementException:
                pass


            resultado = extract_info(driver,variant)
            resultado_dic = resultado
            results.append(resultado_dic)

    return results




def extract_info(driver: webdriver.Chrome, data: dict):
    #driver.implicitly_wait(5)


    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")

    page_not_found=is_page_not_found(soup)
    if(page_not_found):
        print(page_not_found)

        data['stock']=0
        data['quantity']=0
        return data
    
    # Extraer datos de la página
    try:
        titulo = driver.find_element(By.ID, "productTitle").text
        print(titulo)
    except Exception:
        titulo=None
    
    soup = BeautifulSoup(html, "html.parser")
    size = extract_size(soup)
    print(size)

    # Modificar el diccionario solo si la clave existe
    if 'product_name' in data:
        data['product_name'] = titulo

    images = extract_images(driver)
    print(images)

    descripcion = obtener_descripcion(soup).replace("\n", "")
    print(descripcion)

    if 'product_description' in data:
        data['product_description'] = descripcion

    en_stock, cantidad_maxima = obtener_stock_y_cantidad(soup)
    print("existe stock: ", en_stock)
    print("Cantidad_maxima: ", cantidad_maxima)
    
    if 'stock' in data:
        data['stock'] = en_stock  # Ajustar stock basado en disponibilidad
    if 'quantity' in data:
        data['quantity'] = cantidad_maxima  # Establecer cantidad

    is_new = get_buying_option_type(soup)
    precio = obtener_precio(soup, is_new)

    print("Precio: ", precio)
    print("New: ", is_new)

    if 'sku_label_status' in data:
        data['sku_label_status'] = is_new
    if 'offer_price' in data:
        data['offer_price'] = precio

    variantes = extract_variations_values(soup)
    if variantes:
        print(variantes)
        asd = filtrar_ropa_y_eliminar_sku(variantes, True, data.get('sku'))
        print("///////////////////////////////////////////")
        print(asd)

    brand,dimensiones_producto = extract_dimensions_and_brand(soup)


    if dimensiones_producto:
        length, width, height = parse_dimensions(dimensiones_producto)
        if 'width' in data:
            data['width'] = width
        if 'height' in data:
            data['height'] = height
        if 'length' in data:
            data['length'] = length

    if brand:
        data['brand']=brand
    # Descargar imágenes y actualizar el diccionario
    links = asyncio.run(download_images(images, data.get('sku')))
    links.sort()

    for i in range(min(len(links), 6)):  # Asegurar que solo se asignen hasta 6 imágenes
        if f'image_{i}' in data:
            data[f'image_{i}'] = links[i]

    # Devolver el diccionario modificado
    return data
    #print(producto.to_json())

    # with open(f'output{time.time()}.html', 'w', encoding='utf-8') as file:
    #     file.write(str(soup.prettify()))
    #print(producto.to_json())

    # with open(f'output{time.time()}.html', 'w', encoding='utf-8') as file:
    #     file.write(str(soup.prettify()))
