"""
Šis modulis paleidžia duomenų bazės konfigūraciją
"""
import os
import sys

# Pridedame projekto katalogą į Python kelią
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("Duomenų bazės konfigūracija")
    print("===========================")
    
    try:
        from database.db_config import configure_database
        db_url = configure_database()
        print(f"Duomenų bazės konfigūracija sėkminga!")
        print(f"Dabar galite paleisti migracijas su komanda: python run_migrations.py")
    except Exception as e:
        print(f"Įvyko klaida konfigūruojant duomenų bazę: {str(e)}")
        print("Prieš bandant dar kartą, įsitikinkite, kad:")
        print("1. MySQL serveris yra paleistas")
        print("2. Jūs turite reikiamas teises prisijungti prie serverio")
        print("3. Duomenų bazė, kurią nurodėte, egzistuoja")