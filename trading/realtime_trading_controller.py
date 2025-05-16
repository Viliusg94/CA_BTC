"""
Realaus laiko prekybos valdiklis
-----------------------------
Šis modulis valdo realaus laiko prekybą, sujungdamas
simuliatorių su kriptovaliutų biržos API.
"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime
import time
import threading
import json
import os

from api.exchange_client import ExchangeClient
from api.realtime_data_processor import RealtimeDataProcessor
from simulator.engine import SimulatorEngine
from simulator.signals.technical_indicator_signal_generator import TechnicalIndicatorSignalGenerator
from simulator.signals.model_prediction_signal_generator import ModelPredictionSignalGenerator
from simulator.signals.hybrid_signal_generator import HybridSignalGenerator
from simulator.strategies.trend_following_strategy import TrendFollowingStrategy
from simulator.strategies.mean_reversion_strategy import MeanReversionStrategy

logger = logging.getLogger(__name__)

class RealtimeTradingController:
    """
    Realaus laiko prekybos valdiklis, kuris jungia simuliatorių
    su kriptovaliutų biržos API.
    """
    def __init__(self, api_key=None, api_secret=None, exchange="binance", 
                 db_session=None, config_file=None):
        """
        Inicializuoja realaus laiko prekybos valdiklį.
        
        Args:
            api_key (str): API raktas
            api_secret (str): API slaptas raktas
            exchange (str): Biržos pavadinimas
            db_session: Duomenų bazės sesija
            config_file (str): Konfigūracijos failo kelias
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.exchange = exchange
        self.db_session = db_session
        
        # Numatytoji konfigūracija
        self.config = {
            'symbol': 'BTCUSDT',
            'interval': '5m',
            'initial_balance': 10000.0,
            'trade_enabled': False,  # Pradžioje prekyba išjungta
            'trading_mode': 'paper',  # 'paper' arba 'live'
            'strategies': ['trend', 'mean_reversion'],
            'risk_params': {
                'max_position_size_usd': 1000,
                'stop_loss_percentage': 0.05,
                'take_profit_percentage': 0.1
            }
        }
        
        # Įkrauname konfigūraciją jei nurodyta
        if config_file and os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    loaded_config = json.load(f)
                    self.config.update(loaded_config)
                logger.info(f"Konfigūracija įkrauta iš {config_file}")
            except Exception as e:
                logger.error(f"Klaida įkraunant konfigūraciją: {e}")
        
        # Inicializuojame kompnentus
        self.exchange_client = ExchangeClient(api_key, api_secret, exchange)
        self.data_processor = None
        self.simulator = None
        
        # Simuliacijos metaduomenys
        self.symbol = self.config['symbol']
        self.interval = self.config['interval']
        self.trade_enabled = self.config['trade_enabled']
        self.trading_mode = self.config['trading_mode']
        
        # Papildomi kintamieji
        self.running = False
        self.last_action = None
        self.last_price = None
        self.last_signal = None
        self.last_decision = None
        
        logger.info(f"Inicializuotas realaus laiko prekybos valdiklis: {exchange}, simbolis={self.symbol}")
    
    def start(self):
        """
        Pradeda realaus laiko prekybos valdiklį.
        """
        if self.running:
            logger.warning("Prekybos valdiklis jau veikia")
            return
        
        # Inicializuojame duomenų procesorių
        self.data_processor = RealtimeDataProcessor(self.exchange_client)
        
        # Inicializuojame simuliatorių
        self.simulator = SimulatorEngine(self.db_session, initial_balance=self.config['initial_balance'])
        
        # Pradedame duomenų apdorojimą
        self.data_processor.start(self.symbol, self.interval)
        
        # Pridedame duomenų įvykių apdorojimą
        self.data_processor.add_data_event_handler(self._handle_new_data)
        
        # Nustatome pradinį buferį simuliatoriui
        initial_data = self.data_processor.get_historical_buffer()
        if not initial_data.empty:
            self.simulator.load_data(initial_data)
        
        self.running = True
        logger.info("Prekybos valdiklis pradėtas")
    
    def stop(self):
        """
        Sustabdo realaus laiko prekybos valdiklį.
        """
        if not self.running:
            return
        
        self.running = False
        
        # Sustabdome duomenų procesorių
        if self.data_processor:
            self.data_processor.stop()
        
        logger.info("Prekybos valdiklis sustabdytas")
    
    def enable_trading(self, enabled=True):
        """
        Įjungia arba išjungia prekybą.
        
        Args:
            enabled (bool): Ar prekyba įjungta
        """
        self.trade_enabled = enabled
        logger.info(f"Prekyba {'įjungta' if enabled else 'išjungta'}")
    
    def set_trading_mode(self, mode):
        """
        Nustato prekybos režimą.
        
        Args:
            mode (str): Režimas ('paper' arba 'live')
        """
        if mode not in ['paper', 'live']:
            logger.error(f"Neteisingas prekybos režimas: {mode}")
            return
        
        self.trading_mode = mode
        logger.info(f"Nustatytas prekybos režimas: {mode}")
    
    def get_status(self):
        """
        Grąžina dabartinę valdiklio būseną.
        
        Returns:
            dict: Būsenos informacija
        """
        status = {
            'running': self.running,
            'trade_enabled': self.trade_enabled,
            'trading_mode': self.trading_mode,
            'symbol': self.symbol,
            'last_price': self.last_price,
            'last_action': self.last_action,
            'last_signal': self.last_signal,
            'last_decision': self.last_decision
        }
        
        # Pridedame portfelio informaciją
        if self.simulator:
            status['portfolio'] = {
                'balance': self.simulator.portfolio.balance,
                'btc_amount': self.simulator.portfolio.btc_amount
            }
        
        return status
    
    def _handle_new_data(self, data):
        """
        Apdoroja naujus duomenis ir generuoja prekybos signalus.
        
        Args:
            data (pandas.Series): Naujausi duomenys
        """
        if not self.running or not self.simulator:
            return
        
        try:
            # Gauname duomenų buferį
            historical_data = self.data_processor.get_historical_buffer()
            
            # Atnaujinkime simuliatoriaus duomenis
            self.simulator.data = historical_data
            
            # Nustatome dabartinę kainą
            self.last_price = data['close']
            
            # Paruošiame signalų generatorius
            ti_generator = TechnicalIndicatorSignalGenerator()
            ml_generator = ModelPredictionSignalGenerator(prediction_col='predicted_direction', confidence_col='confidence')
            hybrid_generator = HybridSignalGenerator([ti_generator, ml_generator])
            
            # Paruošiame prekybos strategijas
            strategies = []
            
            if 'trend' in self.config['strategies']:
                strategies.append(TrendFollowingStrategy())
            
            if 'mean_reversion' in self.config['strategies']:
                strategies.append(MeanReversionStrategy())
            
            # Gauname signalą
            current_time = pd.Timestamp.now()
            signals = []
            
            for generator in [hybrid_generator]:
                try:
                    signal = generator.generate_signal(data, historical_data, current_time)
                    if signal:
                        signals.append(signal)
                        self.last_signal = signal
                except Exception as e:
                    logger.error(f"Klaida generuojant signalą: {e}")
            
            # Gauname prekybos sprendimą
            decisions = []
            
            for strategy in strategies:
                try:
                    decision = strategy.generate_decision(signals, data, self.simulator.portfolio, current_time)
                    if decision and decision.get('action') in ['buy', 'sell']:
                        decisions.append(decision)
                        self.last_decision = decision
                except Exception as e:
                    logger.error(f"Klaida generuojant prekybos sprendimą: {e}")
            
            # Jei yra prekybos sprendimai ir prekyba įjungta, vykdome prekybą
            if decisions and self.trade_enabled:
                for decision in decisions:
                    self._execute_trade(decision)
            
            logger.debug(f"Apdoroti nauji duomenys: {current_time}, price={self.last_price}, signals={len(signals)}, decisions={len(decisions)}")
            
        except Exception as e:
            logger.error(f"Klaida apdorojant naujus duomenis: {e}")
    
    def _execute_trade(self, decision):
        """
        Vykdo prekybos sprendimą.
        
        Args:
            decision (dict): Prekybos sprendimas
        """
        action = decision.get('action')
        amount = decision.get('amount', 0)
        price = self.last_price
        
        if not action or not amount or not price:
            logger.warning("Negalima įvykdyti prekybos dėl trūkstamų duomenų")
            return
        
        # Registruojame veiksmą
        self.last_action = {
            'action': action,
            'amount': amount,
            'price': price,
            'timestamp': pd.Timestamp.now()
        }
        
        logger.info(f"Prekybos sprendimas: {action} {amount} po kainą {price}")
        
        # Jei esame realios prekybos režime, vykdome prekybą per API
        if self.trading_mode == 'live':
            side = 'BUY' if action == 'buy' else 'SELL'
            
            # Tikriname rizikos parametrus
            max_position_size_usd = self.config['risk_params']['max_position_size_usd']
            trade_value_usd = amount * price
            
            if trade_value_usd > max_position_size_usd:
                # Sumažiname kiekį pagal maksimalų pozicijos dydį
                adjusted_amount = max_position_size_usd / price
                logger.warning(f"Sumažintas prekybos kiekis dėl rizikos: {amount} -> {adjusted_amount}")
                amount = adjusted_amount
            
            # Vykdome prekybą per API
            order_result = self.exchange_client.place_order(
                symbol=self.symbol,
                side=side,
                quantity=amount,
                price=None,  # Naudojame rinkos kainą
                order_type="MARKET"
            )
            
            if order_result:
                logger.info(f"Užsakymas įvykdytas: {order_result}")
            else:
                logger.error("Nepavyko pateikti užsakymo")
        
        # Simuliatoriaus portfelio atnaujinimas (tiek "paper", tiek "live" režimams)
        if action == 'buy':
            # Simuliuojame pirkimą
            if self.simulator.portfolio.balance >= amount * price:
                self.simulator.portfolio.balance -= amount * price
                self.simulator.portfolio.btc_amount += amount
                logger.info(f"Simuliuotas pirkimas: {amount} BTC po {price}, balansas: {self.simulator.portfolio.balance}")
            else:
                logger.warning("Nepakanka lėšų simuliuotam pirkimui")
        elif action == 'sell':
            # Simuliuojame pardavimą
            if self.simulator.portfolio.btc_amount >= amount:
                self.simulator.portfolio.balance += amount * price
                self.simulator.portfolio.btc_amount -= amount
                logger.info(f"Simuliuotas pardavimas: {amount} BTC po {price}, balansas: {self.simulator.portfolio.balance}")
            else:
                logger.warning("Nepakanka BTC simuliuotam pardavimui")