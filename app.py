from flask import Flask, jsonify
from config import Config
from routes.amazon_routes import product_bp
from routes.resize_img_route import resize_bp
from routes.variantes_routes import variant_bp
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
app.register_blueprint(variant_bp)


@app.errorhandler(500)
def internal_server_error(e):
    app.logger.error(f"Error 500: {str(e)}")  # Registrar el error
    response = {
        "error": "Internal Server Error",
        "message": "Ocurrió un problema en el servidor, por favor intenta más tarde."
    }
    return jsonify(response), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0',port=5000,debug=True)






