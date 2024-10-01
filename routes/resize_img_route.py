from flask import Blueprint, jsonify
#from services.scrap_amazon import open_page#,iniciar_webdriver
from services.resizeImgData import ResizeImage


resize_bp = Blueprint('resize', __name__)




@resize_bp.route('/resize', methods=['GET'])
def resize():

    resize = ResizeImage()
    data =resize.resizeImage('img_resize_jpg')  
    
    print(f"Tipo de data: {type(data)}")
    #rint(data)  
    
    #resize.get_all_product_images()
    return "data"
    
