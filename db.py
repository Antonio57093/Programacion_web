# db.py - VERSIÓN QUE FUNCIONA EN AMBOS
import mysql.connector
import os

class Database:
    def __init__(self):
        # Si estamos en Render (tiene DATABASE_URL)
        if 'RENDER' in os.environ or 'DATABASE_URL' in os.environ:
            # Configuración para Aiven en Render
            self.config = {
                "host": "lexcorp-proyectopw.e.aivencloud.com",
                "user": "avnadmin",
                "password": os.environ.get('DB_PASSWORD'),
                "database": "lexcorp",
                "port": 20105,
                "raise_on_warnings": True
            }
        else:
            self.config = {
                "host": "localhost",
                "user": "root",
                "password": "C8be1987d0d4",
                "database": "lexcorp",
                "raise_on_warnings": True
            }

    def connect(self):
        return mysql.connector.connect(**self.config)

