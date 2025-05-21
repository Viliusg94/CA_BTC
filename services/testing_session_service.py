"""
Modelių testavimo sesijų valdymo servisas.
Šis modulis teikia metodus darbui su modelių testavimo sesijomis.
"""
import uuid
import json
import logging
from datetime import datetime, timezone
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from database.models.user_models import UserSession, TestingSession
from utils.id_generator import generate_hash_id, ensure_unique_id

# Sukonfigūruojame logerį
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestingSessionService:
    """
    Servisas darbui su modelių testavimo sesijomis.
    Teikia metodus testavimo sesijų kūrimui, gavimui ir atnaujinimui.
    """
    
    def __init__(self, session: Session):
        """
        Inicializuoja TestingSessionService objektą.
        
        Args:
            session: SQLAlchemy sesijos objektas duomenų bazės operacijoms
        """
        self.session = session
    
    def create_testing_session(self, user_session_id: str, testing_data: dict) -> TestingSession:
        """
        Sukuria naują modelio testavimo sesiją.
        
        Args:
            user_session_id: Naudotojo sesijos ID
            testing_data: Testavimo sesijos duomenys
            
        Returns:
            TestingSession: Sukurta testavimo sesija arba None, jei įvyko klaida
        """
        try:
            # Gauname naudotojo sesiją
            user_session = self.session.query(UserSession).filter(UserSession.id == user_session_id).first()
            
            if not user_session:
                logger.error(f"Naudotojo sesija su ID {user_session_id} nerasta")
                return None
            
            # Tikriname, ar sesijos tipas yra "testing"
            if user_session.session_type != "testing":
                logger.error(f"Naudotojo sesija su ID {user_session_id} nėra testavimo tipo. Esamas tipas: {user_session.session_type}")
                return None
            
            # Tikriname, ar jau yra sukurta testavimo sesija
            if user_session.testing_session:
                logger.warning(f"Naudotojo sesijai su ID {user_session_id} jau yra sukurta testavimo sesija")
                return user_session.testing_session
            
            # Generuojame unikalų ID testavimo sesijai
            unique_id = ensure_unique_id(
                self.session,
                TestingSession,
                generate_hash_id,
                prefix="TST"
            )
            
            if not unique_id:
                logger.error("Nepavyko sugeneruoti unikalaus testavimo sesijos ID")
                return None
            
            # Pridedame sugeneruotą ID
            testing_data['id'] = unique_id
            
            # Pridedame sesijos ID
            testing_data['session_id'] = user_session_id
            
            # Jei yra test_params kaip žodynas, konvertuojame į JSON
            if 'test_params' in testing_data and isinstance(testing_data['test_params'], dict):
                testing_data['test_params'] = json.dumps(testing_data['test_params'])
            
            # Jei yra results kaip žodynas, konvertuojame į JSON
            if 'results' in testing_data and isinstance(testing_data['results'], dict):
                testing_data['results'] = json.dumps(testing_data['results'])
            
            # Pridedame sukūrimo ir atnaujinimo laikus
            current_time = datetime.now(timezone.utc)
            testing_data['created_at'] = current_time
            testing_data['updated_at'] = current_time
            
            # Sukuriame naują testavimo sesijos objektą
            new_testing_session = TestingSession(**testing_data)
            
            # Pridedame į duomenų bazę
            self.session.add(new_testing_session)
            self.session.commit()
            
            logger.info(f"Sukurta nauja testavimo sesija: {new_testing_session.id} sesijai {user_session_id}")
            return new_testing_session
            
        except SQLAlchemyError as e:
            # Atšaukiame transakciją, jei įvyko klaida
            self.session.rollback()
            logger.error(f"Klaida kuriant testavimo sesiją: {str(e)}")
            return None
    
    def get_testing_session(self, testing_session_id: str) -> TestingSession:
        """
        Grąžina testavimo sesiją pagal ID.
        
        Args:
            testing_session_id: Testavimo sesijos ID
            
        Returns:
            TestingSession: Testavimo sesijos objektas arba None, jei sesija nerasta
        """
        try:
            testing_session = self.session.query(TestingSession).filter(TestingSession.id == testing_session_id).first()
            return testing_session
        except SQLAlchemyError as e:
            logger.error(f"Klaida gaunant testavimo sesiją: {str(e)}")
            return None
    
    def get_testing_session_by_user_session(self, user_session_id: str) -> TestingSession:
        """
        Grąžina testavimo sesiją pagal naudotojo sesijos ID.
        
        Args:
            user_session_id: Naudotojo sesijos ID
            
        Returns:
            TestingSession: Testavimo sesijos objektas arba None, jei sesija nerasta
        """
        try:
            testing_session = self.session.query(TestingSession).filter(TestingSession.session_id == user_session_id).first()
            return testing_session
        except SQLAlchemyError as e:
            logger.error(f"Klaida gaunant testavimo sesiją pagal naudotojo sesiją: {str(e)}")
            return None
    
    def list_testing_sessions(self, model_id: str = None, status: str = None, limit: int = 100, offset: int = 0) -> list:
        """
        Grąžina testavimo sesijų sąrašą.
        
        Args:
            model_id: Filtruoti pagal modelio ID (pasirinktinai)
            status: Filtruoti pagal būseną (pasirinktinai)
            limit: Maksimalus grąžinamų sesijų skaičius
            offset: Kiek sesijų praleisti (puslapis)
            
        Returns:
            list: Testavimo sesijų objektų sąrašas
        """
        try:
            query = self.session.query(TestingSession)
            
            if model_id:
                query = query.filter(TestingSession.model_id == model_id)
            
            if status:
                query = query.filter(TestingSession.testing_status == status)
            
            query = query.order_by(TestingSession.created_at.desc()).limit(limit).offset(offset)
            
            testing_sessions = query.all()
            return testing_sessions
        except SQLAlchemyError as e:
            logger.error(f"Klaida gaunant testavimo sesijų sąrašą: {str(e)}")
            return []
    
    def update_testing_session(self, testing_session_id: str, update_data: dict) -> TestingSession:
        """
        Atnaujina testavimo sesijos duomenis.
        
        Args:
            testing_session_id: Testavimo sesijos ID
            update_data: Atnaujinami duomenys
            
        Returns:
            TestingSession: Atnaujinta testavimo sesija arba None, jei įvyko klaida
        """
        try:
            # Gauname testavimo sesiją
            testing_session = self.session.query(TestingSession).filter(TestingSession.id == testing_session_id).first()
            
            if not testing_session:
                logger.warning(f"Testavimo sesija su ID {testing_session_id} nerasta")
                return None
            
            # Jei yra test_params kaip žodynas, konvertuojame į JSON
            if 'test_params' in update_data and isinstance(update_data['test_params'], dict):
                update_data['test_params'] = json.dumps(update_data['test_params'])
            
            # Jei yra results kaip žodynas, konvertuojame į JSON
            if 'results' in update_data and isinstance(update_data['results'], dict):
                update_data['results'] = json.dumps(update_data['results'])
            
            # Atnaujinimo data
            update_data['updated_at'] = datetime.now(timezone.utc)
            
            # Atnaujiname atributus
            for key, value in update_data.items():
                if hasattr(testing_session, key):
                    setattr(testing_session, key, value)
            
            # Išsaugome pakeitimus
            self.session.commit()
            
            logger.info(f"Testavimo sesija {testing_session.id} atnaujinta")
            return testing_session
            
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Klaida atnaujinant testavimo sesiją: {str(e)}")
            return None
    
    def save_test_results(self, testing_session_id: str, results: dict, success: bool = True) -> TestingSession:
        """
        Išsaugo testavimo rezultatus.
        
        Args:
            testing_session_id: Testavimo sesijos ID
            results: Testavimo rezultatai (bus konvertuojami į JSON)
            success: Ar testas pavyko
            
        Returns:
            TestingSession: Atnaujinta testavimo sesija arba None, jei įvyko klaida
        """
        try:
            # Gauname testavimo sesiją
            testing_session = self.session.query(TestingSession).filter(TestingSession.id == testing_session_id).first()
            
            if not testing_session:
                logger.warning(f"Testavimo sesija su ID {testing_session_id} nerasta")
                return None
            
            # Atnaujiname rezultatus ir būseną
            testing_session.results = json.dumps(results)
            testing_session.success = success
            testing_session.testing_status = "completed"
            testing_session.updated_at = datetime.now(timezone.utc)
            
            # Išsaugome pakeitimus
            self.session.commit()
            
            # Uždarome susietą naudotojo sesiją
            if testing_session.session.is_active:
                testing_session.session.is_active = False
                testing_session.session.end_time = datetime.now(timezone.utc)
                testing_session.session.status = "completed"
                self.session.commit()
            
            logger.info(f"Testavimo sesijos {testing_session.id} rezultatai išsaugoti. Sėkmė: {success}")
            return testing_session
            
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Klaida išsaugant testavimo rezultatus: {str(e)}")
            return None