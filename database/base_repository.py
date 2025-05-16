"""
Bazinė repozitorijos klasė
-----------------------------
Šis modulis apibrėžia universalią Repository klasę, kuri valdo bet kokį duomenų bazės modelį.
Jis įgyvendina pagrindinius CRUD (Create, Read, Update, Delete) metodus ir išimčių apdorojimą.
"""

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import desc, func
import logging

# Sukuriame logerį
logger = logging.getLogger(__name__)

class BaseRepository:
    """
    Bazinė repozitorijos klasė, kuri palaiko CRUD operacijas su bet kokiu modeliu.
    Naudoja SQLAlchemy ORM funkcionalumą.
    """
    def __init__(self, session, model):
        """
        Inicializuoja repozitoriją su sesija ir modeliu.
        
        Args:
            session: SQLAlchemy sesija
            model: SQLAlchemy modelio klasė
        """
        self.session = session
        self.model = model
    
    def add(self, entity):
        """
        Prideda naują įrašą į duomenų bazę.
        
        Args:
            entity: Modelio objektas
        
        Returns:
            entity: Pridėtas objektas arba None, jei įvyko klaida
        """
        try:
            self.session.add(entity)
            self.session.commit()
            return entity
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Klaida pridedant {self.model.__name__} įrašą: {e}")
            return None
    
    def add_all(self, entities):
        """
        Prideda kelis įrašus vienu metu.
        
        Args:
            entities: Modelio objektų sąrašas
        
        Returns:
            bool: True, jei operacija sėkminga, False - jei ne
        """
        try:
            self.session.add_all(entities)
            self.session.commit()
            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Klaida pridedant kelis {self.model.__name__} įrašus: {e}")
            return False
    
    def get_by_id(self, id):
        """
        Gauna įrašą pagal ID.
        
        Args:
            id: Įrašo ID
        
        Returns:
            entity: Modelio objektas arba None, jei nerastas
        """
        try:
            return self.session.query(self.model).filter_by(id=id).first()
        except SQLAlchemyError as e:
            logger.error(f"Klaida ieškant {self.model.__name__} įrašo pagal ID {id}: {e}")
            return None
    
    def get_all(self):
        """
        Gauna visus modelio įrašus.
        
        Returns:
            list: Modelio objektų sąrašas
        """
        try:
            return self.session.query(self.model).all()
        except SQLAlchemyError as e:
            logger.error(f"Klaida gaunant visus {self.model.__name__} įrašus: {e}")
            return []
    
    def update(self, entity):
        """
        Atnaujina esamą įrašą.
        
        Args:
            entity: Modelio objektas
        
        Returns:
            entity: Atnaujintas objektas arba None, jei įvyko klaida
        """
        try:
            self.session.merge(entity)
            self.session.commit()
            return entity
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Klaida atnaujinant {self.model.__name__} įrašą: {e}")
            return None
    
    def delete(self, entity):
        """
        Ištrina įrašą.
        
        Args:
            entity: Modelio objektas
        
        Returns:
            bool: True, jei operacija sėkminga, False - jei ne
        """
        try:
            self.session.delete(entity)
            self.session.commit()
            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Klaida ištrinant {self.model.__name__} įrašą: {e}")
            return False
    
    def delete_by_id(self, id):
        """
        Ištrina įrašą pagal ID.
        
        Args:
            id: Įrašo ID
        
        Returns:
            bool: True, jei operacija sėkminga, False - jei ne
        """
        entity = self.get_by_id(id)
        if entity:
            return self.delete(entity)
        return False
    
    def count(self):
        """
        Suskaičiuoja įrašų kiekį.
        
        Returns:
            int: Įrašų kiekis
        """
        try:
            return self.session.query(func.count(self.model.id)).scalar()
        except SQLAlchemyError as e:
            logger.error(f"Klaida skaičiuojant {self.model.__name__} įrašus: {e}")
            return 0
    
    def exists(self, **kwargs):
        """
        Patikrina, ar egzistuoja įrašas su nurodytais parametrais.
        
        Args:
            **kwargs: Paieškos parametrai
        
        Returns:
            bool: True, jei įrašas egzistuoja, False - jei ne
        """
        try:
            return self.session.query(
                self.session.query(self.model).filter_by(**kwargs).exists()
            ).scalar()
        except SQLAlchemyError as e:
            logger.error(f"Klaida tikrinant {self.model.__name__} įrašo egzistavimą: {e}")
            return False
    
    def execute_transaction(self, callback, *args, **kwargs):
        """
        Vykdo transakciją su nurodytu callback.
        
        Args:
            callback: Funkcija, kuri bus vykdoma transakcijos kontekste
            *args, **kwargs: Argumentai, perduodami callback funkcijai
        
        Returns:
            Callback funkcijos grąžinama reikšmė arba None, jei įvyko klaida
        """
        try:
            result = callback(*args, **kwargs)
            self.session.commit()
            return result
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Klaida vykdant transakciją: {e}")
            return None