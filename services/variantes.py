from services.scrap_amazon import AmazonScraper
#from models.amazon import Amazon
from utils.utils import extract_variations_values , is_page_not_found
from bs4 import BeautifulSoup
from datetime import datetime


class Variantes(AmazonScraper):

    def __init__(self, language='en_US'):
        super().__init__(language)



    def scraping_variant(self,variantes):

        results = []
        #url_base = "https://www.amazon.com/gp/product/"
        for variant in variantes:

            #print(type(variant))
            sku = variant.get("sku")
            uuid = variant.get("uuid")
            if not sku or not uuid:
                print(f"Faltan SKU o UUID para la variante: {variant}")
                continue
            url = f"{self.url_base_dp}{sku}/?psc=1"
            self.driver.get(url)
            # Resolver captcha si es necesario
            if self.resolve_captcha():
                if self.is_correct_product_page(sku):
                    result = self.extract_info(variant)
            results.append(result)
        return results


    def open_page_variant(self,variantes):

        #results=[]

        for variant in variantes:
            sku=variant.get('sku')

            if not sku :
                print(f"Error al procesar sku : {variant}") 
                continue
            url=f"{self.url_base}{sku}/?psc=1"
            self.driver.get(url)

            if self.resolve_captcha():
                if self.is_correct_product_page(sku):
                    result=self.scraping_data_variant(variant)
                    #results.append(result)

        return result






    def scraping_data_variant(self, data: dict):
        sku_list = []
        html = self.driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        fecha_actual = datetime.now()
        fecha_str = fecha_actual.strftime('%Y-%m-%d %H:%M:%S.%f')
        
        data["is_parent"] = 1
        #child_data = data.copy()  # Hacemos una copia inicial de `data`
        
        # Extraer variantes y parent_asin
        variantes, parent_asin = extract_variations_values(soup)

        for key, value in variantes.items():
            child_data = data.copy()  # Hacemos una copia nueva para cada iteración
            
            # Actualizamos los valores en `child_data`
            child_data["sku"] = key
            child_data["size"] = value[0]
            child_data["product_url"] = f"{self.url_base_dp}{key}?psc=1";
        #     # # data["use_product_url"] = 1;            
            if value[0] is not None:
                child_data["size_saved"] = 1
                child_data["verify_size"] = 0
            else:
                child_data["size_saved"] = 0
                child_data["verify_size"] = 1

            child_data["uuid"] = None
            child_data["is_parent"] = 0
            child_data["is_child"] = 1
            child_data["get_variation"] = 0

            # Añadimos la copia actualizada a `sku_list`
            sku_list.append(child_data)
            #child_data=None

        if  sku_list is not None:
            data["get_variation"] = 0
            sku_list.append(data)

        data["get_variation"] = 0

        return sku_list


        







        # if page_not_found:
            
        #     # data["is_parent"]=1
        #     # data["size_saved"]=0
        #     # data["verify_size"]=1
        #     # # data["product_url"] = f"{self.url_base_dp}{key}?psc=1";
        #     # # data["use_product_url"] = 1; 
        #     # data["uuid"]=None
        #     # #---- esto se pone fuera del bucle / para el padre---
        #     # data["is_parent"]=0
        #     # data["is_child"]=1
        #     # data["get_variation"]=0
        # #aplicar logica -----------------------------
