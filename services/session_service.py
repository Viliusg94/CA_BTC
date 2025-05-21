"""
Naudotojų sesijų valdymo servisas.
Šis modulis teikia metodus darbui su naudotojų sesijomis.
"""
import uuid
import json
import logging
from datetime import datetime, timezone
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from database.models.user_models import UserSession, User
from utils.id_generator import generate_session_id, ensure_unique_id

# Sukonfigūruojame logerį
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SessionService:
    """
    Servisas darbui su naudotojų sesijomis.
    Teikia metodus sesijų kūrimui, gavimui, atnaujinimui ir paieškai.
    """
    
    def __init__(self, session: Session):
        """
        Inicializuoja SessionService objektą.
        
        Args:
            session: SQLAlchemy sesijos objektas duomenų bazės operacijoms
        """
        self.session = session
    
    def create_session(self, session_data: dict) -> UserSession:
        """
        Sukuria naują naudotojo sesiją.
        
        Args:
            session_data: Sesijos duomenys (user_id, session_type, ip_address, ...)
            
        Returns:
            UserSession: Sukurta sesija arba None, jei įvyko klaida
        """
        try:
            # Patikrinkime, ar yra būtini laukai
            if 'user_id' not in session_data:
                logger.error("Nepateiktas privalomas laukas: user_id")
                return None
            
            # Nustatome sesijos tipą, jei nepateiktas
            if 'session_type' not in session_data:
                session_data['session_type'] = 'general'  # Numatytasis sesijos tipas
            
            # Generuojame unikalų ID sesijai
            unique_id = ensure_unique_id(
                self.session,
                UserSession,
                generate_session_id,
                session_type=session_data['session_type']
            )
            
            if not unique_id:
                logger.error("Nepavyko sugeneruoti unikalaus sesijos ID")
                return None
            
            # Pridedame sugeneruotą ID
            session_data['id'] = unique_id
            
            # Konvertuojame metadata į JSON, jei reikia
            if 'metadata' in session_data and isinstance(session_data['metadata'], dict):
                session_data['metadata'] = json.dumps(session_data['metadata'])
            
            # Nustatome sesijos pradžios laiką, jei nepateikta
            if 'start_time' not in session_data:
                session_data['start_time'] = datetime.now(timezone.utc)
            
            # Nustatome sukūrimo ir atnaujinimo laikus
            current_time = datetime.now(timezone.utc)
            session_data['created_at'] = current_time
            session_data['updated_at'] = current_time
            
            # Sukuriame naują sesijos objektą
            new_session = UserSession(**session_data)
            
            # Pridedame į duomenų bazę
            self.session.add(new_session)
            self.session.commit()
            
            logger.info(f"Sukurta nauja sesija: {new_session.id} naudotojui {new_session.user_id}")
            return new_session
            
        except SQLAlchemyError as e:
            # Atšaukiame transakciją, jei įvyko klaida
            self.session.rollback()
            logger.error(f"Klaida kuriant sesiją: {str(e)}")
            return None
    
    def get_session(self, session_id: str) -> UserSession:
        """
        Grąžina sesiją pagal ID.
        
        Args:
            session_id: Sesijos ID
            
        Returns:
            UserSession: Sesijos objektas arba None, jei sesija nerasta
        """
        try:
            session = self.session.query(UserSession).filter(UserSession.id == session_id).first()
            return session
        except SQLAlchemyError as e:
            logger.error(f"Klaida gaunant sesiją: {str(e)}")
            return None
    
    def list_user_sessions(self, user_id: str, active_only: bool = False, limit: int = 100, offset: int = 0) -> list:
        """
        Grąžina naudotojo sesijų sąrašą.
        
        Args:
            user_id: Naudotojo ID
            active_only: Ar grąžinti tik aktyvias sesijas
            limit: Maksimalus grąžinamų sesijų skaičius
            offset: Kiek sesijų praleisti (puslapis)
            
        Returns:
            list: Sesijų objektų sąrašas
        """
        try:
            query = self.session.query(UserSession).filter(UserSession.user_id == user_id)
            
            if active_only:
                query = query.filter(UserSession.is_active == True)
            
            query = query.order_by(UserSession.start_time.desc()).limit(limit).offset(offset)
            
            sessions = query.all()
            return sessions
        except SQLAlchemyError as e:
            logger.error(f"Klaida gaunant naudotojo sesijas: {str(e)}")
            return []
    
    def list_sessions_by_type(self, session_type: str, limit: int = 100, offset: int = 0) -> list:
        """
        Grąžina sesijų sąrašą pagal tipą.
        
        Args:
            session_type: Sesijos tipas (training/testing/general)
            limit: Maksimalus grąžinamų sesijų skaičius
            offset: Kiek sesijų praleisti (puslapis)
            
        Returns:
            list: Sesijų objektų sąrašas
        """
        try:
            sessions = self.session.query(UserSession).filter(
                UserSession.session_type == session_type
            ).order_by(UserSession.start_time.desc()).limit(limit).offset(offset).all()
            
            return sessions
        except SQLAlchemyError as e:
            logger.error(f"Klaida gaunant sesijas pagal tipą: {str(e)}")
            return []
    
    def list_active_sessions(self, limit: int = 100, offset: int = 0) -> list:
        """
        Grąžina aktyvių sesijų sąrašą.
        
        Args:
            limit: Maksimalus grąžinamų sesijų skaičius
            offset: Kiek sesijų praleisti (puslapis)
            
        Returns:
            list: Sesijų objektų sąrašas
        """
        try:
            sessions = self.session.query(UserSession).filter(
                UserSession.is_active == True
            ).order_by(UserSession.start_time.desc()).limit(limit).offset(offset).all()
            
            return sessions
        except SQLAlchemyError as e:
            logger.error(f"Klaida gaunant aktyvias sesijas: {str(e)}")
            return []
    
    def update_session(self, session_id: str, update_data: dict) -> UserSession:
        """
        Atnaujina sesijos duomenis.
        
        Args:
            session_id: Sesijos ID
            update_data: Atnaujinami duomenys
            
        Returns:
            UserSession: Atnaujinta sesija arba None, jei įvyko klaida
        """
        try:
            # Gauname sesiją
            session = self.session.query(UserSession).filter(UserSession.id == session_id).first()
            
            if not session:
                logger.warning(f"Sesija su ID {session_id} nerasta")
                return None
            
            # Konvertuojame metadata į JSON, jei reikia
            if 'metadata' in update_data and isinstance(update_data['metadata'], dict):
                update_data['metadata'] = json.dumps(update_data['metadata'])
            
            # Atnaujinimo data
            update_data['updated_at'] = datetime.now(timezone.utc)
            
            # Atnaujiname atributus
            for key, value in update_data.items():
                if hasattr(session, key):
                    setattr(session, key, value)
            
            # Išsaugome pakeitimus
            self.session.commit()
            
            logger.info(f"Sesija {session.id} atnaujinta")
            return session
            
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Klaida atnaujinant sesiją: {str(e)}")
            return None
    
    def end_session(self, session_id: str) -> UserSession:
        """
        Baigia naudotojo sesiją.
        
        Args:
            session_id: Sesijos ID
            
        Returns:
            UserSession: Atnaujinta sesija arba None, jei įvyko klaida
        """
        try:
            # Gauname sesiją
            session = self.session.query(UserSession).filter(UserSession.id == session_id).first()
            
            if not session:
                logger.warning(f"Sesija su ID {session_id} nerasta")
                return None
            
            # Jei sesija jau neaktyvi, tiesiog grąžiname ją
            if not session.is_active:
                logger.info(f"Sesija {session.id} jau baigta")
                return session
            
            # Atnaujiname sesijos būseną
            current_time = datetime.now(timezone.utc)
            session.is_active = False
            session.end_time = current_time
            session.status = "completed"
            session.updated_at = current_time
            
            # Išsaugome pakeitimus
            self.session.commit()
            
            logger.info(f"Sesija {session.id} baigta")
            return session
            
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Klaida baigiant sesiją: {str(e)}")
            return None
    
    def delete_session(self, session_id: str) -> bool:
        """
        Ištrina sesiją.
        
        Args:
            session_id: Sesijos ID
            
        Returns:
            bool: Ar sesija buvo sėkmingai ištrinta
        """
        try:
            # Gauname sesiją
            session = self.session.query(UserSession).filter(UserSession.id == session_id).first()
            
            if not session:
                logger.warning(f"Sesija su ID {session_id} nerasta")
                return False
            
            # Ištriname sesiją
            self.session.delete(session)
            self.session.commit()
            
            logger.info(f"Sesija {session.id} ištrinta")
            return True
            
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Klaida trinant sesiją: {str(e)}")
            return False
    
    def delete_user_sessions(self, user_id: str) -> int:
        """
        Ištrina visas naudotojo sesijas.
        
        Args:
            user_id: Naudotojo ID
            
        Returns:
            int: Ištrintų sesijų skaičius
        """
        try:
            # Gauname naudotojo sesijų skaičių
            count = self.session.query(UserSession).filter(UserSession.user_id == user_id).count()
            
            # Ištriname visas naudotojo sesijas
            self.session.query(UserSession).filter(UserSession.user_id == user_id).delete()
            self.session.commit()
            
            logger.info(f"Ištrintos {count} naudotojo {user_id} sesijos")
            return count
            
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Klaida trinant naudotojo sesijas: {str(e)}")
            return 0