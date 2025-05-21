"""
Pavyzdinis skriptas parodantis kaip naudoti UserService klasę.
"""
import os
import sys
import logging
from datetime import datetime

# Pridedame pagrindinį projekto katalogą į kelią
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importuojame reikalingas bibliotekas
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from database import SQLALCHEMY_DATABASE_URL
from services.user_service import UserService

# Konfigūruojame žurnalą
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """
    Pagrindinė funkcija demonstruojanti UserService naudojimą.
    """
    # Prisijungiame prie duomenų bazės
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    session = Session(engine)
    
    # Sukuriame naudotojų servisą
    user_service = UserService(session)
    
    try:
        logger.info("Pradedamas naudotojų valdymo pavyzdys")
        
        # 1. Sukuriame naują naudotoją
        logger.info("1. Kuriame naują naudotoją")
        
        new_user_data = {
            "username": "testas",
            "email": "testas@example.com",
            "password": "slaptazodis123",
            "full_name": "Testavimo Naudotojas",
            "is_admin": False
        }
        
        user = user_service.create_user(new_user_data)
        
        if user:
            logger.info(f"Sukurtas naudotojas: ID={user.id}, Vardas={user.username}")
        else:
            logger.error("Nepavyko sukurti naudotojo")
            return
        
        # 2. Gauname naudotoją pagal ID
        logger.info("2. Gauname naudotoją pagal ID")
        
        retrieved_user = user_service.get_user(user.id)
        
        if retrieved_user:
            logger.info(f"Gautas naudotojas: {retrieved_user.username}, El. paštas: {retrieved_user.email}")
        else:
            logger.error("Naudotojas nerastas")
        
        # 3. Atnaujiname naudotojo duomenis
        logger.info("3. Atnaujiname naudotojo duomenis")
        
        update_data = {
            "full_name": "Atnaujintas Naudotojas",
            "is_active": True
        }
        
        updated_user = user_service.update_user(user.id, update_data)
        
        if updated_user:
            logger.info(f"Atnaujintas naudotojas: {updated_user.username}, Pilnas vardas: {updated_user.full_name}")
        else:
            logger.error("Nepavyko atnaujinti naudotojo")
        
        # 4. Tikriname prisijungimo duomenis
        logger.info("4. Tikriname prisijungimo duomenis")
        
        # Teisingi prisijungimo duomenys
        validated_user = user_service.validate_credentials("testas", "slaptazodis123")
        
        if validated_user:
            logger.info(f"Sėkmingas prisijungimas: {validated_user.username}")
        else:
            logger.error("Neteisingi prisijungimo duomenys")
        
        # Neteisingi prisijungimo duomenys
        invalid_user = user_service.validate_credentials("testas", "neteisingas")
        
        if invalid_user:
            logger.error("Netikėtai sėkmingas prisijungimas su neteisingais duomenimis")
        else:
            logger.info("Teisingai atmestas prisijungimas su neteisingais duomenimis")
        
        # 5. Gauname naudotojų sąrašą
        logger.info("5. Gauname naudotojų sąrašą")
        
        users = user_service.list_users()
        
        logger.info(f"Rasta naudotojų: {len(users)}")
        for u in users:
            logger.info(f"- {u.username} ({u.email})")
        
        # 6. Ištriname naudotoją
        logger.info("6. Ištriname naudotoją")
        
        if user_service.delete_user(user.id):
            logger.info(f"Naudotojas {user.username} ištrintas")
        else:
            logger.error(f"Nepavyko ištrinti naudotojo {user.username}")
        
        # Patikriname, ar naudotojas ištrinta
        deleted_user = user_service.get_user(user.id)
        
        if deleted_user:
            logger.error("Naudotojas nebuvo ištrintas")
        else:
            logger.info("Patvirtinta, kad naudotojas buvo ištrintas")
        
        logger.info("Naudotojų valdymo pavyzdys baigtas")
        
    except Exception as e:
        logger.error(f"Įvyko klaida: {str(e)}")
    
    finally:
        # Uždarome sesiją
        session.close()
        logger.info("Duomenų bazės sesija uždaryta")

if __name__ == "__main__":
    main()