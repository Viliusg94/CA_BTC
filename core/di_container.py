"""
Priklausomybių injekcijos konteineris
-----------------------------
Šis modulis įgyvendina Dependency Injection šabloną, kuris padeda valdyti
komponentų priklausomybes ir palengvina jų pakartotinį naudojimą bei testavimą.
"""

import logging
from sqlalchemy.orm import sessionmaker
from database.models import init_db
from database.unit_of_work import UnitOfWork
from services.data_service import DataService
from services.trading_service import TradingService

# Sukuriame logerį
logger = logging.getLogger(__name__)

class DIContainer:
    """
    Dependency Injection konteineris, kuris valdo priklausomybes.
    """
    def __init__(self):
        """
        Inicializuoja DI konteinerį.
        """
        self._instances = {}
        self._factories = {}
        
        # Inicializuojame duomenų bazės ryšį ir sesijas
        self._engine, self._session = None, None
        self._session_factory = None
        
        # Registruojame gamyklas
        self._register_factories()
    
    def _register_factories(self):
        """
        Registruoja komponentų gamyklos metodus.
        """
        # Registruojame duomenų bazės gamyklas
        self._factories['engine'] = self._create_engine
        self._factories['session'] = self._create_session
        self._factories['session_factory'] = self._create_session_factory
        
        # Registruojame repozitorijų gamyklas
        self._factories['unit_of_work'] = self._create_unit_of_work
        
        # Registruojame servisų gamyklas
        self._factories['data_service'] = self._create_data_service
        self._factories['trading_service'] = self._create_trading_service
    
    def _create_engine(self):
        """
        Sukuria SQLAlchemy variklį.
        
        Returns:
            sqlalchemy.engine.Engine: SQLAlchemy variklis
        """
        if not self._engine:
            self._engine, _ = init_db()
        return self._engine
    
    def _create_session_factory(self):
        """
        Sukuria SQLAlchemy sesijos gamyklą.
        
        Returns:
            sqlalchemy.orm.sessionmaker: Sesijos gamykla
        """
        if not self._session_factory:
            engine = self.get('engine')
            self._session_factory = sessionmaker(bind=engine)
        return self._session_factory
    
    def _create_session(self):
        """
        Sukuria naują SQLAlchemy sesiją.
        
        Returns:
            sqlalchemy.orm.Session: SQLAlchemy sesija
        """
        session_factory = self.get('session_factory')
        return session_factory()
    
    def _create_unit_of_work(self):
        """
        Sukuria naują UnitOfWork objektą.
        
        Returns:
            UnitOfWork: UnitOfWork objektas
        """
        session = self.get('session')
        return UnitOfWork(session)
    
    def _create_data_service(self):
        """
        Sukuria naują DataService objektą.
        
        Returns:
            DataService: DataService objektas
        """
        session = self.get('session')
        return DataService(session)
    
    def _create_trading_service(self):
        """
        Sukuria naują TradingService objektą.
        
        Returns:
            TradingService: TradingService objektas
        """
        session = self.get('session')
        return TradingService(session)
    
    def get(self, name):
        """
        Gauna arba sukuria komponentą pagal pavadinimą.
        
        Args:
            name: Komponento pavadinimas
        
        Returns:
            object: Komponento objektas
        """
        # Jei komponento dar nėra sukurto, sukuriame jį
        if name not in self._instances:
            if name not in self._factories:
                raise ValueError(f"Nežinomas komponentas: {name}")
            
            # Sukuriame komponentą naudodami gamyklos metodą
            self._instances[name] = self._factories[name]()
        
        return self._instances[name]
    
    def get_session(self):
        """
        Grąžina naują SQLAlchemy sesiją.
        Šis metodas visada grąžina naują sesiją, o ne pakartotinai naudoja esamą.
        
        Returns:
            sqlalchemy.orm.Session: SQLAlchemy sesija
        """
        return self._create_session()
    
    def cleanup(self):
        """
        Išvalo visus sukurtus komponentus.
        """
        # Uždarome sesijas
        if 'session' in self._instances:
            self._instances['session'].close()
        
        # Išvalome visas instancijas
        self._instances.clear()