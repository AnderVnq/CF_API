import os

class Config:
    # Configuración de Firebase
    FIREBASE_CREDENTIALS = os.path.join(os.path.dirname(__file__), 'storagecampeonato-firebase-adminsdk-lwku5-11ad60cec5.json')
    FIREBASE_STORAGE_BUCKET = 'storagecampeonato.appspot.com'  # Reemplaza con tu nombre de bucket