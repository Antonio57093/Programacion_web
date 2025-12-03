import mysql.connector
import os
from dotenv import load_dotenv  # AÑADE ESTA IMPORTACIÓN

load_dotenv()

class Database:
    def __init__(self):
        if 'RENDER' in os.environ or 'DATABASE_URL' in os.environ:
            # Configuración para producción (Render/Aiven)
            self.config = {
                "host": "lexcorp-proyectopw.e.aivencloud.com",
                "user": "avnadmin",
                "password": os.environ.get('DB_PASSWORD'),
                "database": "lexcorp",
                "port": 20105,
                "raise_on_warnings": True
            }
        else:
            # Configuración para desarrollo local
            self.config = {
                "host": os.environ.get('DB_HOST', 'localhost'),
                "user": os.environ.get('DB_USER', 'root'),
                "password": os.environ.get('DB_PASSWORD_LOCAL'),
                "database": os.environ.get('DB_NAME', 'lexcorp'),
                "raise_on_warnings": True
            }
    
    def connect(self):
        return mysql.connector.connect(**self.config)