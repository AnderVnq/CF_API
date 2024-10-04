from flask import Blueprint, jsonify
from models.amazon import Amazon
from services.scrap_amazon import AmazonScraper
import json

product_bp = Blueprint('product', __name__)


@product_bp.route('/scrape', methods=['GET'])
def scrape():

    #driver = iniciar_webdriver()
    data =Amazon('amazon').get_product_detail() # heredar 
    #data = json.loads(data)
    #print(data)
    if data ==None:
        return jsonify({"error": "No se encontraron datos"}), 404 
    print(type(data))
    scraper = AmazonScraper()
    response_scrap=scraper.open_page(data) #normal
    #response_scrap=scraper.scrape_variants(data) # mulihilo
    Amazon.massive_update_modelv2('scraping',response_scrap)
    if response_scrap:#if response_db:
        #scraper.driver.quit()
        return jsonify(response_scrap)  # Retornar la respuesta en formato JSON
    else:
        return jsonify({"error": "No se actualizaron correctamente los datos"}), 400 
    



#

@product_bp.route('/',methods=['GET'])
def hello_world():
    return '¡data!'