# SUKURTI FAILĄ: d:\CA_BTC\database\config.py
import os
from dotenv import load_dotenv

# Įkelti aplinkos kintamuosius
load_dotenv()

# MySQL prisijungimo duomenys
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '3306')
DB_NAME = os.getenv('DB_NAME', 'btc_database')

# SQLAlchemy prisijungimo eilutė
SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"