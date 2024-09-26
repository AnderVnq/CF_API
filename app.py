from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from sshtunnel import SSHTunnelForwarder
from routes.amazon_routes import product_bp




app = Flask(__name__)
app.config.from_object(Config)


# server = SSHTunnelForwarder(
#     (app.config['SSH_HOST'], app.config['SSH_PORT']),
#     ssh_username=app.config['SSH_USER'],
#     ssh_password=app.config['SSH_PASSWORD'],  # O usa ssh_pkey para la clave privada
#     remote_bind_address=(app.config['MYSQL_HOST'], 3306)
# )

# server.start()

# # Configurar la URI de la base de datos usando la dirección local del túnel
# app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql://{app.config["MYSQL_USER"]}:{app.config["MYSQL_PASSWORD"]}@127.0.0.1:{server.local_bind_port}/{app.config["MYSQL_DB"]}'
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# db = SQLAlchemy(app)



# Registrando las rutas
app.register_blueprint(product_bp)



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