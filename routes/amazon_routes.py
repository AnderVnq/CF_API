from flask import Blueprint, jsonify
from services.scrap_amazon import open_page,iniciar_webdriver
from models.amazon import Amazon
product_bp = Blueprint('product', __name__)




@product_bp.route('/scrape', methods=['GET'])
def scrape():

    driver = iniciar_webdriver()
    amazon =Amazon('amazon')
    data = amazon.get_product_detail()
    data = open_page(driver, data)
    response_db=Amazon.massive_update_model('scraping',data)
    if response_db:
        return jsonify(data)  # Retornar la respuesta en formato JSON
    else:
        return jsonify({"error": "No se encontraron datos"}), 404 
    

@product_bp.route('/',methods=['GET'])
def hello_world():
    return '¡data!'