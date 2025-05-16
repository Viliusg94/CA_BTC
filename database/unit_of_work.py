"""
UnitOfWork šablonas
-----------------------------
Šis modulis įgyvendina UnitOfWork šabloną, kuris koordinuoja repozitorijų darbą
vienos transakcijos kontekste ir užtikrina duomenų vientisumą.
"""

from sqlalchemy.exc import SQLAlchemyError
import logging
from database.repositories import (
    BtcPriceRepository, 
    TechnicalIndicatorRepository, 
    AdvancedFeatureRepository,
    PredictionRepository,
    TradingRepository,
    PortfolioRepository,
    TradingSignalRepository
)

# Sukuriame logerį
logger = logging.getLogger(__name__)

class UnitOfWork:
    """
    UnitOfWork šablonas, kuris koordinuoja repozitorijų darbą vienos transakcijos kontekste.
    """
    def __init__(self, session):
        """
        Inicializuoja UnitOfWork su sesija.
        
        Args:
            session: SQLAlchemy sesija
        """
        self.session = session
        self._repositories = {}
        
        # Inicializuojame repozitorijas
        self._btc_prices = None
        self._indicators = None
        self._features = None
        self._predictions = None
        self._trading = None
        self._portfolio = None
        self._trading_signals = None
        self._portfolios = None
        self._trades = None
    
    @property
    def btc_prices(self):
        """BtcPriceRepository repozitorija."""
        if self._btc_prices is None:
            self._btc_prices = BtcPriceRepository(self.session)
        return self._btc_prices
    
    @property
    def indicators(self):
        """TechnicalIndicatorRepository repozitorija."""
        if self._indicators is None:
            self._indicators = TechnicalIndicatorRepository(self.session)
        return self._indicators
    
    @property
    def features(self):
        """AdvancedFeatureRepository repozitorija."""
        if self._features is None:
            self._features = AdvancedFeatureRepository(self.session)
        return self._features
    
    @property
    def predictions(self):
        """PredictionRepository repozitorija."""
        if self._predictions is None:
            self._predictions = PredictionRepository(self.session)
        return self._predictions
    
    @property
    def trading(self):
        """TradingRepository repozitorija."""
        if self._trading is None:
            self._trading = TradingRepository(self.session)
        return self._trading
    
    @property
    def portfolio(self):
        """PortfolioRepository repozitorija."""
        if self._portfolio is None:
            self._portfolio = PortfolioRepository(self.session)
        return self._portfolio
    
    @property
    def trading_signals(self):
        """TradingSignalRepository repozitorija."""
        if self._trading_signals is None:
            self._trading_signals = TradingSignalRepository(self.session)
        return self._trading_signals
    
    @property
    def portfolios(self):
        """PortfolioRepository repozitorija."""
        if self._portfolios is None:
            self._portfolios = PortfolioRepository(self.session)
        return self._portfolios
    
    def __enter__(self):
        """
        Konteksto valdytojas - pradeda transakciją.
        
        Returns:
            UnitOfWork: Šis UnitOfWork objektas
        """
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Konteksto valdytojas - baigia transakciją. Jei įvyko klaida, atšaukia (rollback).
        
        Args:
            exc_type: Išimties tipas
            exc_val: Išimties reikšmė
            exc_tb: Išimties stack trace
        """
        if exc_type is not None:
            self.rollback()
            logger.error(f"Transakcija atšaukta dėl klaidos: {exc_val}")
        else:
            self.commit()
    
    def commit(self):
        """
        Patvirtina transakciją.
        """
        try:
            self.session.commit()
            logger.debug("Transakcija patvirtinta.")
        except SQLAlchemyError as e:
            self.rollback()
            logger.error(f"Klaida patvirtinant transakciją: {e}")
            raise
    
    def rollback(self):
        """
        Atšaukia transakciją.
        """
        self.session.rollback()
        logger.debug("Transakcija atšaukta.")
    
    def execute(self, callback, *args, **kwargs):
        """
        Vykdo callbacką transakcijos kontekste.
        
        Args:
            callback: Funkcija, kuri bus vykdoma
            *args, **kwargs: Argumentai callback funkcijai
        
        Returns:
            Grąžinamą callback funkcijos rezultatą
        """
        try:
            result = callback(*args, **kwargs)
            self.commit()
            return result
        except Exception as e:
            self.rollback()
            logger.error(f"Klaida vykdant transakciją: {e}")
            raise