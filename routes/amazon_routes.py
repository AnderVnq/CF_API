from flask import Blueprint, jsonify
#from services.scrap_amazon import open_page#,iniciar_webdriver
from models.amazon import Amazon
from services.scrap_amazon import AmazonScraper
import json

product_bp = Blueprint('product', __name__)




@product_bp.route('/scrape', methods=['GET'])
def scrape():

    #driver = iniciar_webdriver()
    data =Amazon('amazon').get_product_detail()
    #data = json.loads(data)
    print(f"Tipo de data: {type(data)}")

    #data = amazon.get_product_detail()
    scraper = AmazonScraper()
    #response_scrap=scraper.open_page(data) #normal
    response_scrap=scraper.scrape_variants(data) # mulihilo
    #response_db=Amazon.massive_update_model('scraping',reponse_scrap)
    if response_scrap:#if response_db:
        return jsonify(data)  # Retornar la respuesta en formato JSON
    else:
        return jsonify({"error": "No se encontraron datos"}), 404 
    



#

@product_bp.route('/',methods=['GET'])
def hello_world():
    return '¡data!'