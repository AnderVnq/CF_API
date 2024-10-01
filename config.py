import os

class Config:
    # Configuración de Firebase
    FIREBASE_CREDENTIALS = os.path.join(os.path.dirname(__file__), 'storagecampeonato-firebase-adminsdk-lwku5-11ad60cec5.json')
    FIREBASE_STORAGE_BUCKET = 'storagecampeonato.appspot.com'  # Reemplaza con tu nombre de bucket
    
    
    # Configuraciones de rutas
    IMAGES_PATH = os.path.join(os.path.dirname(__file__))#"/var/www/html/Public/Images"
    DOCS_PATH = os.path.join(os.path.dirname(__file__))#"/var/www/html/Public/docs"
    DOMAIN = os.path.join(os.path.dirname(__file__))#"https://www.comprafacil.pics/Public/Images/"
    PUBLIC_PATH = os.path.join(os.path.dirname(__file__))#"/var/www/html/Public"
    MAIN_PATH = os.path.join(os.path.dirname(__file__))#"/var/www/html"

    @classmethod
    def get_base_paths(cls):
        return {
            "images_path": cls.IMAGES_PATH,
            "docs_path": cls.DOCS_PATH,
            "domain": cls.DOMAIN,
            "public_path": cls.PUBLIC_PATH,
            "main_path": cls.MAIN_PATH,
        }