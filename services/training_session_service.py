"""
Modelių treniravimo sesijų valdymo servisas.
Šis modulis teikia metodus darbui su modelių treniravimo sesijomis.
"""
import uuid
import json
import logging
from datetime import datetime, timezone
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from database.models.user_models import UserSession, TrainingSession
from utils.id_generator import generate_hash_id, ensure_unique_id

# Sukonfigūruojame logerį
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TrainingSessionService:
    """
    Servisas darbui su modelių treniravimo sesijomis.
    Teikia metodus treniravimo sesijų kūrimui, gavimui ir atnaujinimui.
    """
    
    def __init__(self, session: Session):
        """
        Inicializuoja TrainingSessionService objektą.
        
        Args:
            session: SQLAlchemy sesijos objektas duomenų bazės operacijoms
        """
        self.session = session
    
    def create_training_session(self, user_session_id: str, training_data: dict) -> TrainingSession:
        """
        Sukuria naują modelio treniravimo sesiją.
        
        Args:
            user_session_id: Naudotojo sesijos ID
            training_data: Treniravimo sesijos duomenys
            
        Returns:
            TrainingSession: Sukurta treniravimo sesija arba None, jei įvyko klaida
        """
        try:
            # Gauname naudotojo sesiją
            user_session = self.session.query(UserSession).filter(UserSession.id == user_session_id).first()
            
            if not user_session:
                logger.error(f"Naudotojo sesija su ID {user_session_id} nerasta")
                return None
            
            # Tikriname, ar sesijos tipas yra "training"
            if user_session.session_type != "training":
                logger.error(f"Naudotojo sesija su ID {user_session_id} nėra treniravimo tipo. Esamas tipas: {user_session.session_type}")
                return None
            
            # Tikriname, ar jau yra sukurta treniravimo sesija
            if user_session.training_session:
                logger.warning(f"Naudotojo sesijai su ID {user_session_id} jau yra sukurta treniravimo sesija")
                return user_session.training_session
            
            # Generuojame unikalų ID treniravimo sesijai
            unique_id = ensure_unique_id(
                self.session,
                TrainingSession,
                generate_hash_id,
                prefix="TRN"
            )
            
            if not unique_id:
                logger.error("Nepavyko sugeneruoti unikalaus treniravimo sesijos ID")
                return None
            
            # Pridedame sugeneruotą ID
            training_data['id'] = unique_id
            
            # Pridedame sesijos ID
            training_data['session_id'] = user_session_id
            
            # Pridedame sukūrimo ir atnaujinimo laikus
            current_time = datetime.now(timezone.utc)
            training_data['created_at'] = current_time
            training_data['updated_at'] = current_time
            
            # Sukuriame naują treniravimo sesijos objektą
            new_training_session = TrainingSession(**training_data)
            
            # Pridedame į duomenų bazę
            self.session.add(new_training_session)
            self.session.commit()
            
            logger.info(f"Sukurta nauja treniravimo sesija: {new_training_session.id} sesijai {user_session_id}")
            return new_training_session
            
        except SQLAlchemyError as e:
            # Atšaukiame transakciją, jei įvyko klaida
            self.session.rollback()
            logger.error(f"Klaida kuriant treniravimo sesiją: {str(e)}")
            return None
    
    def get_training_session(self, training_session_id: str) -> TrainingSession:
        """
        Grąžina treniravimo sesiją pagal ID.
        
        Args:
            training_session_id: Treniravimo sesijos ID
            
        Returns:
            TrainingSession: Treniravimo sesijos objektas arba None, jei sesija nerasta
        """
        try:
            training_session = self.session.query(TrainingSession).filter(TrainingSession.id == training_session_id).first()
            return training_session
        except SQLAlchemyError as e:
            logger.error(f"Klaida gaunant treniravimo sesiją: {str(e)}")
            return None
    
    def get_training_session_by_user_session(self, user_session_id: str) -> TrainingSession:
        """
        Grąžina treniravimo sesiją pagal naudotojo sesijos ID.
        
        Args:
            user_session_id: Naudotojo sesijos ID
            
        Returns:
            TrainingSession: Treniravimo sesijos objektas arba None, jei sesija nerasta
        """
        try:
            training_session = self.session.query(TrainingSession).filter(TrainingSession.session_id == user_session_id).first()
            return training_session
        except SQLAlchemyError as e:
            logger.error(f"Klaida gaunant treniravimo sesiją pagal naudotojo sesiją: {str(e)}")
            return None
    
    def list_training_sessions(self, model_id: str = None, status: str = None, limit: int = 100, offset: int = 0) -> list:
        """
        Grąžina treniravimo sesijų sąrašą.
        
        Args:
            model_id: Filtruoti pagal modelio ID (pasirinktinai)
            status: Filtruoti pagal būseną (pasirinktinai)
            limit: Maksimalus grąžinamų sesijų skaičius
            offset: Kiek sesijų praleisti (puslapis)
            
        Returns:
            list: Treniravimo sesijų objektų sąrašas
        """
        try:
            query = self.session.query(TrainingSession)
            
            if model_id:
                query = query.filter(TrainingSession.model_id == model_id)
            
            if status:
                query = query.filter(TrainingSession.training_status == status)
            
            query = query.order_by(TrainingSession.created_at.desc()).limit(limit).offset(offset)
            
            training_sessions = query.all()
            return training_sessions
        except SQLAlchemyError as e:
            logger.error(f"Klaida gaunant treniravimo sesijų sąrašą: {str(e)}")
            return []
    
    def update_training_session(self, training_session_id: str, update_data: dict) -> TrainingSession:
        """
        Atnaujina treniravimo sesijos duomenis.
        
        Args:
            training_session_id: Treniravimo sesijos ID
            update_data: Atnaujinami duomenys
            
        Returns:
            TrainingSession: Atnaujinta treniravimo sesija arba None, jei įvyko klaida
        """
        try:
            # Gauname treniravimo sesiją
            training_session = self.session.query(TrainingSession).filter(TrainingSession.id == training_session_id).first()
            
            if not training_session:
                logger.warning(f"Treniravimo sesija su ID {training_session_id} nerasta")
                return None
            
            # Atnaujinimo data
            update_data['updated_at'] = datetime.now(timezone.utc)
            
            # Atnaujiname atributus
            for key, value in update_data.items():
                if hasattr(training_session, key):
                    setattr(training_session, key, value)
            
            # Išsaugome pakeitimus
            self.session.commit()
            
            logger.info(f"Treniravimo sesija {training_session.id} atnaujinta")
            return training_session
            
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Klaida atnaujinant treniravimo sesiją: {str(e)}")
            return None
    
    def update_training_progress(self, training_session_id: str, current_epoch: int, status: str = None) -> TrainingSession:
        """
        Atnaujina treniravimo progresą.
        
        Args:
            training_session_id: Treniravimo sesijos ID
            current_epoch: Dabartinė epocha
            status: Nauja būsena (pasirinktinai)
            
        Returns:
            TrainingSession: Atnaujinta treniravimo sesija arba None, jei įvyko klaida
        """
        try:
            # Gauname treniravimo sesiją
            training_session = self.session.query(TrainingSession).filter(TrainingSession.id == training_session_id).first()
            
            if not training_session:
                logger.warning(f"Treniravimo sesija su ID {training_session_id} nerasta")
                return None
            
            # Atnaujiname progresą
            training_session.current_epoch = current_epoch
            
            # Atnaujiname būseną, jei pateikta
            if status:
                training_session.training_status = status
            
            # Atnaujiname laiką
            training_session.updated_at = datetime.now(timezone.utc)
            
            # Išsaugome pakeitimus
            self.session.commit()
            
            logger.info(f"Treniravimo sesijos {training_session.id} progresas atnaujintas: {current_epoch}/{training_session.total_epochs}")
            return training_session
            
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Klaida atnaujinant treniravimo progresą: {str(e)}")
            return None
    
    def complete_training(self, training_session_id: str) -> TrainingSession:
        """
        Pabaigia treniravimo sesiją.
        
        Args:
            training_session_id: Treniravimo sesijos ID
            
        Returns:
            TrainingSession: Atnaujinta treniravimo sesija arba None, jei įvyko klaida
        """
        try:
            # Gauname treniravimo sesiją
            training_session = self.session.query(TrainingSession).filter(TrainingSession.id == training_session_id).first()
            
            if not training_session:
                logger.warning(f"Treniravimo sesija su ID {training_session_id} nerasta")
                return None
            
            # Nustatome treniravimo būseną į "completed"
            training_session.training_status = "completed"
            
            # Jei nurodytas bendras epochų skaičius, nustatome dabartinę epochą į jį
            if training_session.total_epochs:
                training_session.current_epoch = training_session.total_epochs
            
            # Atnaujiname laiką
            training_session.updated_at = datetime.now(timezone.utc)
            
            # Išsaugome pakeitimus
            self.session.commit()
            
            # Uždarome susietą naudotojo sesiją
            if training_session.session.is_active:
                training_session.session.is_active = False
                training_session.session.end_time = datetime.now(timezone.utc)
                training_session.session.status = "completed"
                self.session.commit()
            
            logger.info(f"Treniravimo sesija {training_session.id} baigta")
            return training_session
            
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Klaida baigiant treniravimo sesiją: {str(e)}")
            return None