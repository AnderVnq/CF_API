from flask import Blueprint, jsonify
#from services.scrap_amazon import open_page#,iniciar_webdriver
from models.amazon import Amazon
from services.variantes import Variantes

variant_bp = Blueprint('variantes', __name__)




@variant_bp.route('/variantes', methods=['GET'])
def resize():


    model = Amazon('amazon')
    
    data = model.get_variants_detail()
    
    if not data:
        return {"Error ":"No hay data"}
    print(f"Tipo de data: {type(data)}")
    #rint(data)  
    scraper_variante = Variantes().open_page_variant(data)
    response = Amazon('amazon').execture_procedure_variantes(scraper_variante)
    print("responseeeeeeeeee-----------------")
    print(response)
    print("response -----------------------------------------------")
    #resize.get_all_product_images()
    return scraper_variante
    
