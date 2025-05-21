"""
Programos konfigūracija
"""
import os
import urllib.parse
from dotenv import load_dotenv

# Bandome įkelti .env failą, jei jis egzistuoja
load_dotenv()

# Duomenų bazės prisijungimo informacija
# Pirmiausia bandom gauti iš aplinkos kintamųjų, jei nėra, naudojame numatytuosius
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "final_boss")  # Tuščias slaptažodis kaip numatytasis
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "ca_btc")

# Užkoduojame slaptažodį, jei jame yra specialių simbolių
encoded_password = urllib.parse.quote_plus(DB_PASSWORD)

# SQLAlchemy duomenų bazės URL
SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Papildomos konfigūracijos, jei reikia
DEBUG = os.getenv("DEBUG", "False").lower() == "true"