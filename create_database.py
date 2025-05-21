"""
Šis modulis sukuria duomenų bazę, jei jos dar nėra
"""
import os
import sys
import pymysql
from getpass import getpass

# Pridedame projekto katalogą į Python kelią
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_database():
    """
    Sukuria duomenų bazę
    """
    print("Duomenų bazės kūrimas")
    print("====================")
    
    # Perskaitome duomenų bazės konfigūraciją iš .env failo jei egzistuoja
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    
    db_user = "root"
    db_password = "final_boss"
    db_host = "localhost"
    db_port = 3306
    db_name = "ca_btc"
    
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if line.strip() and not line.strip().startswith('#'):
                    try:
                        key, value = line.strip().split('=', 1)
                        if key == "DB_USER":
                            db_user = value
                        elif key == "DB_PASSWORD":
                            db_password = value
                        elif key == "DB_HOST":
                            db_host = value
                        elif key == "DB_PORT":
                            db_port = int(value)
                        elif key == "DB_NAME":
                            db_name = value
                    except ValueError:
                        pass
    
    # Klausiame vartotojo įvesti parametrus
    print("Įveskite duomenų bazės administratoriaus prisijungimo informaciją:")
    db_user = input(f"Vartotojo vardas [{db_user}]: ") or db_user
    db_password = getpass(f"Slaptažodis: ") or db_password
    db_host = input(f"Serveris [{db_host}]: ") or db_host
    db_port = input(f"Prievadas [{db_port}]: ") or db_port
    db_name = input(f"Duomenų bazės pavadinimas [{db_name}]: ") or db_name
    
    try:
        # Prisijungiame prie MySQL serverio be duomenų bazės
        connection = pymysql.connect(
            host=db_host,
            user=db_user,
            password=db_password,
            port=int(db_port),
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        try:
            with connection.cursor() as cursor:
                # Sukuriame duomenų bazę, jei jos dar nėra
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                
                # Sukuriame vartotoją, jei jo dar nėra
                cursor.execute(f"SELECT 1 FROM mysql.user WHERE user = '{db_user}'")
                user_exists = cursor.fetchone() is not None
                
                if not user_exists:
                    create_user = input(f"Vartotojas '{db_user}' neegzistuoja. Ar norite jį sukurti? (y/n): ")
                    if create_user.lower() == 'y':
                        new_password = getpass(f"Įveskite slaptažodį naujam vartotojui: ")
                        cursor.execute(f"CREATE USER '{db_user}'@'%' IDENTIFIED BY '{new_password}'")
                        cursor.execute(f"GRANT ALL PRIVILEGES ON `{db_name}`.* TO '{db_user}'@'%'")
                        cursor.execute("FLUSH PRIVILEGES")
                
            connection.commit()
            print(f"✓ Duomenų bazė '{db_name}' sėkmingai sukurta arba jau egzistavo!")
            
            # Išsaugome konfigūraciją į .env failą
            with open(env_path, 'w') as f:
                f.write("# Duomenų bazės prisijungimo informacija\n")
                f.write(f"DB_USER={db_user}\n")
                f.write(f"DB_PASSWORD={db_password}\n")
                f.write(f"DB_HOST={db_host}\n")
                f.write(f"DB_PORT={db_port}\n")
                f.write(f"DB_NAME={db_name}\n")
                f.write("DEBUG=False\n")
            
            print(f"✓ Konfigūracija išsaugota į {env_path}")
            
        finally:
            connection.close()
            
    except Exception as e:
        print(f"✗ Klaida kuriant duomenų bazę: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    if create_database():
        print("Dabar galite paleisti konfigūraciją su komanda: python configure_db.py")
        print("Arba iš karto paleisti migracijas su komanda: python run_migrations.py")
    else:
        print("Duomenų bazės kūrimas nepavyko. Pabandykite dar kartą.")