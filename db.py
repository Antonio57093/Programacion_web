# PROGRAMA: db.py
# DESCRIPCIÓN:
#   Clase para manejar la conexión a la base de datos MySQL.
#   Centraliza la configuración de la BD para usar desde app.py.
#   Tecnologías: mysql-connector-python

import mysql.connector

class Database:
    def __init__(self):
        self.config = {
            "host": "localhost",
            "user": "root",
            "password": "C&be1987d0d4",
            "database": "lexcorp",
            "raise_on_warnings": True
        }

    def connect(self):
        return mysql.connector.connect(**self.config)


