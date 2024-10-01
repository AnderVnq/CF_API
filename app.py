from flask import Flask
from config import Config
from routes.amazon_routes import product_bp
from routes.resize_img_route import resize_bp
import firebase_admin
from firebase_admin import credentials,initialize_app


app = Flask(__name__)
app.config.from_object(Config)

cred = credentials.Certificate(Config.FIREBASE_CREDENTIALS)
initialize_app(cred, {
    'storageBucket': Config.FIREBASE_STORAGE_BUCKET
})

# Registrando las rutas
app.register_blueprint(product_bp)
app.register_blueprint(resize_bp)


if __name__ == "__main__":
    app.run(debug=True)








# def main():
#     # Inicializar el controlador de Selenium
#     driver = iniciar_webdriver()
#     # Lista de variantes (SKUs)
#     sku= ["B0B984GDXY"]
#     #sku=["B09BP4YFGT","B09NQNG86N","B0B984GDXY","B006PDD2RE","B0D3WRF5MQ","B0CCSVKXWN","B0CCSRQJNC","B08DRB42QZ","B0D3WVZXDR","B0CCSSX2JX","B08DQXS11T","B08DQZ3XSD","B09BP76G2X","B09BP4BCWR","B0CCSSM837","B0CCSSQLG4","B0D3WKXJS8","B0D3WJWPH8","B0CCSVCWS7","B0D3WK9BP5","B08DR7K19Z","B0D3WCWB3B","B0D3WK8L23","B0CCST4MKJ","B0D3WK99W5","B0CCSTXX24","B08DQR9PX1","B08DQZFFGN","B0D3WPM69Z","B08DR22BBY","B08DQWM8XQ","B09BP4YFGT","B08DR3ZFL4"]
#     # Llamar a la función para abrir páginas y extraer la información
#     open_page(driver, sku)
    
#     # Cerrar el navegador al terminar
#     driver.quit()

# Ejecutar el programa
# if __name__ == "__main__":
#     main()