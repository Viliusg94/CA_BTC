"""
Naudotojų valdymo servisas.
Šis modulis teikia metodus darbui su naudotojų duomenimis.
"""
import uuid
import logging
import hashlib
from datetime import datetime, timezone
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from database.models.user_models import User

# Sukonfigūruojame logerį
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UserService:
    """
    Servisas darbui su naudotojų duomenimis.
    Teikia metodus naudotojų CRUD operacijoms.
    """
    
    def __init__(self, session: Session):
        """
        Inicializuoja UserService objektą.
        
        Args:
            session: SQLAlchemy sesijos objektas duomenų bazės operacijoms
        """
        self.session = session
    
    def hash_password(self, password: str) -> str:
        """
        Užšifruoja slaptažodį naudojant SHA-256 algoritmą.
        Realioje sistemoje būtų naudojamas saugesnis algoritmas, pvz., bcrypt ar Argon2.
        
        Args:
            password: Neužšifruotas slaptažodis
            
        Returns:
            str: Užšifruotas slaptažodis
        """
        # Paprastas SHA-256 šifravimas (demonstraciniais tikslais)
        # Realioje sistemoje naudokite bcrypt, Argon2 ar kitą saugesnį algoritną
        return hashlib.sha256(password.encode()).hexdigest()
    
    def create_user(self, user_data: dict) -> User:
        """
        Sukuria naują naudotoją duomenų bazėje.
        
        Args:
            user_data: Naudotojo duomenys (username, email, password, ...)
            
        Returns:
            User: Sukurtas naudotojo objektas arba None, jei įvyko klaida
        """
        try:
            # Užšifruojame slaptažodį
            if 'password' in user_data:
                user_data['password_hash'] = self.hash_password(user_data['password'])
                del user_data['password']  # Pašaliname neužšifruotą slaptažodį
            
            # Sugeneruojame ID, jei jis nepateiktas
            if 'id' not in user_data:
                user_data['id'] = str(uuid.uuid4())
            
            # Pridedame sukūrimo ir atnaujinimo datas
            current_time = datetime.now(timezone.utc)
            user_data['created_at'] = current_time
            user_data['updated_at'] = current_time
            
            # Sukuriame naują naudotojo objektą
            new_user = User(**user_data)
            
            # Pridedame į duomenų bazę
            self.session.add(new_user)
            self.session.commit()
            
            logger.info(f"Sukurtas naujas naudotojas: {new_user.username}")
            return new_user
            
        except SQLAlchemyError as e:
            # Atšaukiame transakciją, jei įvyko klaida
            self.session.rollback()
            logger.error(f"Klaida kuriant naudotoją: {str(e)}")
            return None
    
    def get_user(self, user_id: str) -> User:
        """
        Grąžina naudotoją pagal ID.
        
        Args:
            user_id: Naudotojo ID
            
        Returns:
            User: Naudotojo objektas arba None, jei naudotojas nerastas
        """
        try:
            user = self.session.query(User).filter(User.id == user_id).first()
            return user
        except SQLAlchemyError as e:
            logger.error(f"Klaida gaunant naudotoją: {str(e)}")
            return None
    
    def get_user_by_username(self, username: str) -> User:
        """
        Grąžina naudotoją pagal vartotojo vardą.
        
        Args:
            username: Naudotojo vardas
            
        Returns:
            User: Naudotojo objektas arba None, jei naudotojas nerastas
        """
        try:
            user = self.session.query(User).filter(User.username == username).first()
            return user
        except SQLAlchemyError as e:
            logger.error(f"Klaida ieškant naudotojo pagal vardą: {str(e)}")
            return None
    
    def get_user_by_email(self, email: str) -> User:
        """
        Grąžina naudotoją pagal el. paštą.
        
        Args:
            email: Naudotojo el. paštas
            
        Returns:
            User: Naudotojo objektas arba None, jei naudotojas nerastas
        """
        try:
            user = self.session.query(User).filter(User.email == email).first()
            return user
        except SQLAlchemyError as e:
            logger.error(f"Klaida ieškant naudotojo pagal el. paštą: {str(e)}")
            return None
    
    def list_users(self, limit: int = 100, offset: int = 0) -> list:
        """
        Grąžina naudotojų sąrašą.
        
        Args:
            limit: Maksimalus grąžinamų naudotojų skaičius
            offset: Kiek naudotojų praleisti (puslapis)
            
        Returns:
            list: Naudotojų objektų sąrašas
        """
        try:
            users = self.session.query(User).limit(limit).offset(offset).all()
            return users
        except SQLAlchemyError as e:
            logger.error(f"Klaida gaunant naudotojų sąrašą: {str(e)}")
            return []
    
    def update_user(self, user_id: str, update_data: dict) -> User:
        """
        Atnaujina naudotojo duomenis.
        
        Args:
            user_id: Naudotojo ID
            update_data: Atnaujinami duomenys
            
        Returns:
            User: Atnaujintas naudotojo objektas arba None, jei įvyko klaida
        """
        try:
            # Gauname naudotoją
            user = self.session.query(User).filter(User.id == user_id).first()
            
            if not user:
                logger.warning(f"Naudotojas su ID {user_id} nerastas")
                return None
            
            # Užšifruojame slaptažodį, jei jis pateiktas
            if 'password' in update_data:
                update_data['password_hash'] = self.hash_password(update_data['password'])
                del update_data['password']
            
            # Atnaujinimo data
            update_data['updated_at'] = datetime.now(timezone.utc)
            
            # Atnaujiname atributus
            for key, value in update_data.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            
            # Išsaugome pakeitimus
            self.session.commit()
            
            logger.info(f"Naudotojas {user.username} atnaujintas")
            return user
            
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Klaida atnaujinant naudotoją: {str(e)}")
            return None
    
    def delete_user(self, user_id: str) -> bool:
        """
        Ištrina naudotoją.
        
        Args:
            user_id: Naudotojo ID
            
        Returns:
            bool: Ar naudotojas buvo sėkmingai ištrintas
        """
        try:
            # Gauname naudotoją
            user = self.session.query(User).filter(User.id == user_id).first()
            
            if not user:
                logger.warning(f"Naudotojas su ID {user_id} nerastas")
                return False
            
            # Ištriname naudotoją
            self.session.delete(user)
            self.session.commit()
            
            logger.info(f"Naudotojas {user.username} ištrintas")
            return True
            
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Klaida trinant naudotoją: {str(e)}")
            return False
    
    def validate_credentials(self, username: str, password: str) -> User:
        """
        Tikrina naudotojo prisijungimo duomenis.
        
        Args:
            username: Naudotojo vardas
            password: Naudotojo slaptažodis
            
        Returns:
            User: Naudotojo objektas, jei prisijungimo duomenys teisingi, arba None
        """
        try:
            # Gauname naudotoją pagal vardą
            user = self.get_user_by_username(username)
            
            if not user:
                logger.warning(f"Naudotojas {username} nerastas")
                return None
            
            # Tikriname slaptažodį
            if user.password_hash == self.hash_password(password):
                # Atnaujiname paskutinio prisijungimo laiką
                user.last_login = datetime.now(timezone.utc)
                self.session.commit()
                
                logger.info(f"Naudotojas {username} sėkmingai prisijungė")
                return user
            else:
                logger.warning(f"Neteisingas slaptažodis naudotojui {username}")
                return None
                
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Klaida tikrinant prisijungimo duomenis: {str(e)}")
            return None