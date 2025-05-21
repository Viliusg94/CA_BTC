"""
Šis modulis padeda sukonfigūruoti duomenų bazės prisijungimą interaktyviai
"""
import os
import sys
from sqlalchemy import create_engine, text

# Pridedame projekto katalogą į Python kelią
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_connection(db_url):
    """
    Patikrina prisijungimą prie duomenų bazės
    
    Args:
        db_url (str): Duomenų bazės prisijungimo URL
        
    Returns:
        bool: Ar prisijungimas sėkmingas
    """
    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✓ Prisijungimas prie duomenų bazės sėkmingas!")
            return True
    except Exception as e:
        print(f"✗ Nepavyko prisijungti prie duomenų bazės: {str(e)}")
        return False

def configure_database():
    """
    Interaktyviai konfigūruoja duomenų bazės prisijungimą
    
    Returns:
        str: Duomenų bazės prisijungimo URL
    """
    print("Duomenų bazės konfigūracija")
    print("===========================")
    print("Įveskite duomenų bazės prisijungimo informaciją:")
    
    # Pirmiausia bandome nuskaityti egzistuojančius parametrus iš .env failo
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    
    default_user = "root"
    default_password = "final_boss"
    default_host = "localhost"
    default_port = "3306"
    default_name = "ca_btc"
    
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if line.strip() and not line.strip().startswith('#'):
                    key, value = line.strip().split('=', 1)
                    if key == "DB_USER":
                        default_user = value
                    elif key == "DB_PASSWORD":
                        default_password = value
                    elif key == "DB_HOST":
                        default_host = value
                    elif key == "DB_PORT":
                        default_port = value
                    elif key == "DB_NAME":
                        default_name = value
    
    # Klausiame vartotojo įvesti parametrus
    user = input(f"Vartotojo vardas [{default_user}]: ") or default_user
    password = input(f"Slaptažodis [{default_password}]: ") or default_password
    host = input(f"Serveris [{default_host}]: ") or default_host
    port = input(f"Prievadas [{default_port}]: ") or default_port
    db_name = input(f"Duomenų bazės pavadinimas [{default_name}]: ") or default_name
    
    # Sukuriame prisijungimo URL
    db_url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{db_name}"
    
    # Tikriname prisijungimą
    if test_connection(db_url):
        # Išsaugome parametrus į .env failą
        with open(env_path, 'w') as f:
            f.write(f"# Duomenų bazės prisijungimo informacija\n")
            f.write(f"DB_USER={user}\n")
            f.write(f"DB_PASSWORD={password}\n")
            f.write(f"DB_HOST={host}\n")
            f.write(f"DB_PORT={port}\n")
            f.write(f"DB_NAME={db_name}\n")
            f.write(f"DEBUG=False\n")
        
        print(f"✓ Konfigūracija išsaugota į {env_path}")
        return db_url
    else:
        print("✗ Nepavyko prisijungti prie duomenų bazės su nurodytais parametrais.")
        retry = input("Ar norite bandyti dar kartą? (y/n): ")
        if retry.lower() == 'y':
            return configure_database()
        else:
            sys.exit(1)

if __name__ == "__main__":
    configure_database()