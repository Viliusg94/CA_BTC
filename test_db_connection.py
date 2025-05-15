from database.models import init_db, BtcPriceData
from database.db_init import create_database
from sqlalchemy import text

def test_mysql_connection():
    """Testuoja MySQL ryšį"""
    print("Testuojamas MySQL prisijungimas...")
    
    # Sukuriame duomenų bazę, jei jos dar nėra
    created = create_database()
    
    if not created:
        print("Nepavyko sukurti duomenų bazės. Patikrinkite konfigūraciją .env faile.")
        return False
    
    # Inicializuojame prisijungimą
    try:
        engine, session = init_db()
        
        # Bandome vykdyti paprastą užklausą
        result = session.execute(text("SELECT 1")).fetchone()
        
        if result and result[0] == 1:
            print("MySQL prisijungimas sėkmingas!")
            
            # Patikriname, ar veikia lentelės
            tables_query = "SHOW TABLES"
            tables = session.execute(text(tables_query)).fetchall()
            
            print("Duomenų bazės lentelės:")
            for table in tables:
                print(f"- {table[0]}")
            
            # Patikriname, kiek įrašų turime BTC lentelėje
            count_query = "SELECT COUNT(*) FROM btc_price_data"
            count = session.execute(text(count_query)).fetchone()
            
            print(f"BTC kainų įrašų skaičius: {count[0]}")
            
            session.close()
            return True
        else:
            print("Nepavyko vykdyti paprastos užklausos.")
            session.close()
            return False
            
    except Exception as e:
        print(f"Klaida testuojant MySQL prisijungimą: {e}")
        return False

if __name__ == "__main__":
    test_mysql_connection()