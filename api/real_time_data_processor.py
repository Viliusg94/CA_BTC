"""
Realaus laiko duomenų procesorius
-----------------------------
Šis modulis apdoroja realaus laiko duomenis ir paruošia juos
naudojimui prekybos simuliatoriuje.
"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import threading
import time
import queue

logger = logging.getLogger(__name__)

class RealtimeDataProcessor:
    """
    Realaus laiko duomenų apdorojimo klasė, kuri transformuoja 
    WebSocket duomenų srautą į simuliatoriui tinkamą formatą.
    """
    def __init__(self, exchange_client, buffer_size=100):
        """
        Inicializuoja realaus laiko duomenų procesorių.
        
        Args:
            exchange_client (ExchangeClient): Biržos API klientas
            buffer_size (int): Duomenų buferio dydis
        """
        self.exchange_client = exchange_client
        self.buffer_size = buffer_size
        
        # Duomenų buferiai
        self.price_buffer = pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        self.ticks_buffer = queue.Queue(maxsize=buffer_size * 5)  # Didesnis buferis tick duomenims
        
        # Techninių indikatorių skaičiavimo buferiai
        self.sma_short_period = 20
        self.sma_long_period = 50
        self.rsi_period = 14
        
        # Laiko agregavimo nustatymai
        self.candle_interval = '1m'  # 1 minutė pagal nutylėjimą
        self.last_candle_time = None
        
        # Naujausių duomenų kintamieji
        self.current_price = None
        self.current_data = None
        
        # Nauji duomenys įvykių apdorojimui
        self.data_events = []
        
        # Žymė, ar procesorius veikia
        self.running = False
        self.aggregation_thread = None
        
        logger.info("Inicializuotas realaus laiko duomenų procesorius")
    
    def start(self, symbol, interval='1m'):
        """
        Pradeda realaus laiko duomenų apdorojimą.
        
        Args:
            symbol (str): Kriptovaliutos simbolis
            interval (str): Žvakių intervalo agregavimas ('1m', '5m', '15m', '1h')
        """
        self.symbol = symbol
        self.candle_interval = interval
        self.running = True
        
        # Pradžiai užpildome buferį istoriniais duomenimis
        self._initialize_buffer()
        
        # Prisijungiame prie WebSocket srauto
        self.exchange_client.start_websocket(symbol, self._process_tick)
        
        # Paleidžiame atskirą giją duomenų agregavimui
        self.aggregation_thread = threading.Thread(target=self._aggregate_data_loop)
        self.aggregation_thread.daemon = True
        self.aggregation_thread.start()
        
        logger.info(f"Pradėtas realaus laiko duomenų apdorojimas simboliui {symbol}, intervalas {interval}")
    
    def stop(self):
        """
        Sustabdo realaus laiko duomenų apdorojimą.
        """
        self.running = False
        self.exchange_client.stop_websocket()
        logger.info("Sustabdytas realaus laiko duomenų apdorojimas")
    
    def get_current_data(self):
        """
        Grąžina naujausius duomenis su techniniais indikatoriais.
        
        Returns:
            pandas.Series: Naujausi duomenys
        """
        return self.current_data
    
    def get_historical_buffer(self):
        """
        Grąžina istorinių duomenų buferį.
        
        Returns:
            pandas.DataFrame: Istorinių duomenų buferis
        """
        return self.price_buffer
    
    def add_data_event_handler(self, handler):
        """
        Prideda naujų duomenų įvykių apdorojimo funkciją.
        
        Args:
            handler (function): Funkcija, kuri bus iškviesta gavus naujus duomenis
        """
        self.data_events.append(handler)
    
    def _initialize_buffer(self):
        """
        Inicializuoja duomenų buferį istoriniais duomenimis.
        """
        # Gauname istorinius duomenis
        historical_data = self.exchange_client.get_historical_data(
            symbol=self.symbol,
            interval=self.candle_interval,
            limit=self.buffer_size
        )
        
        if historical_data.empty:
            logger.warning("Nepavyko gauti istorinių duomenų buferio inicializavimui")
            return
        
        # Išsaugome duomenis buferyje
        self.price_buffer = historical_data
        
        # Nustatome paskutinės žvakės laiką
        self.last_candle_time = self.price_buffer.index[-1]
        
        # Apskaičiuojame techninius indikatorius
        self._calculate_indicators()
        
        # Nustatome dabartinę kainą
        last_row = self.price_buffer.iloc[-1]
        self.current_price = last_row['close']
        self.current_data = last_row
        
        logger.info(f"Buferis inicializuotas su {len(self.price_buffer)} istorinių įrašų")
    
    def _process_tick(self, tick_data):
        """
        Apdoroja naują tick iš WebSocket.
        
        Args:
            tick_data (dict): Tick duomenys iš WebSocket
        """
        try:
            # Skirtingos biržos siunčia skirtingo formato duomenis
            if self.exchange_client.exchange == "binance":
                if 'e' in tick_data and tick_data['e'] == '24hrTicker':
                    price = float(tick_data['c'])  # Uždarymų kaina
                    timestamp = pd.Timestamp.fromtimestamp(tick_data['E'] / 1000)
                    volume = float(tick_data.get('v', 0))  # Volume
                elif 'p' in tick_data:  # Kitas Binance formatas
                    price = float(tick_data['p'])
                    timestamp = pd.Timestamp.fromtimestamp(int(time.time()))
                    volume = float(tick_data.get('q', 0))
                else:
                    return
            elif self.exchange_client.exchange == "coinbase":
                price = float(tick_data.get('price', 0))
                timestamp = pd.Timestamp.fromtimestamp(int(time.time()))
                volume = float(tick_data.get('volume_24h', 0))
            else:  # kraken
                if isinstance(tick_data, list) and len(tick_data) > 1 and 'c' in tick_data[1]:
                    price = float(tick_data[1]['c'][0])
                    timestamp = pd.Timestamp.fromtimestamp(int(time.time()))
                    volume = float(tick_data[1].get('v', [0, 0])[1])  # 24h volume
                else:
                    return
            
            # Atnaujiname dabartinę kainą
            self.current_price = price
            
            # Pridedame tick į buferį
            tick = {'timestamp': timestamp, 'price': price, 'volume': volume}
            
            if self.ticks_buffer.full():
                self.ticks_buffer.get()  # Pašaliname seniausią tick, jei buferis pilnas
            
            self.ticks_buffer.put(tick)
            
        except Exception as e:
            logger.error(f"Klaida apdorojant tick duomenis: {e}")
    
    def _aggregate_data_loop(self):
        """
        Pagrindinė duomenų agregavimo ciklo funkcija.
        Veikia atskirame gije ir periodiškai agreguoja tick duomenis į žvakes.
        """
        while self.running:
            try:
                # Nustatome, kiek laiko praėjo nuo paskutinės žvakės
                now = pd.Timestamp.now()
                
                # Jei paskutinės žvakės laikas nenustatytas, nustatome jį
                if self.last_candle_time is None:
                    self.last_candle_time = now
                
                # Apskaičiuojame, kada turi būti sukurta nauja žvakė
                interval_seconds = {
                    '1m': 60, '5m': 300, '15m': 900, '1h': 3600
                }.get(self.candle_interval, 60)
                
                next_candle_time = (self.last_candle_time + 
                                   pd.Timedelta(seconds=interval_seconds))
                
                # Jei atėjo laikas naujai žvakei
                if now >= next_candle_time:
                    self._create_new_candle()
                    self.last_candle_time = next_candle_time
                
                # Miegame 1 sekundę prieš kitą patikrinimą
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Klaida duomenų agregavimo cikle: {e}")
                time.sleep(5)  # Ilgesnis laukimas po klaidos
    
    def _create_new_candle(self):
        """
        Sukuria naują kainų žvakę iš sukauptų tick duomenų.
        """
        # Ištraukiame visus tick duomenis iš buferio
        ticks = []
        while not self.ticks_buffer.empty():
            ticks.append(self.ticks_buffer.get())
        
        if not ticks:
            logger.warning("Nėra tick duomenų naujai žvakei sukurti")
            return
        
        # Konvertuojame į DataFrame
        ticks_df = pd.DataFrame(ticks)
        
        # Išrenkame tik aktualius duomenis pagal laiko intervalą
        if self.last_candle_time:
            start_time = self.last_candle_time
            ticks_df = ticks_df[ticks_df['timestamp'] >= start_time]
        
        if ticks_df.empty:
            logger.warning("Nėra tinkamų tick duomenų šiam laiko intervalui")
            return
        
        # Sukuriame naują žvakę
        candle = {
            'timestamp': self.last_candle_time,
            'open': ticks_df.iloc[0]['price'],
            'high': ticks_df['price'].max(),
            'low': ticks_df['price'].min(),
            'close': ticks_df.iloc[-1]['price'],
            'volume': ticks_df['volume'].sum()
        }
        
        # Pridedame naują žvakę į buferį
        new_candle = pd.DataFrame([candle]).set_index('timestamp')
        self.price_buffer = pd.concat([self.price_buffer, new_candle])
        
        # Išlaikome buferio dydį
        if len(self.price_buffer) > self.buffer_size:
            self.price_buffer = self.price_buffer.iloc[-self.buffer_size:]
        
        # Apskaičiuojame techninius indikatorius
        self._calculate_indicators()
        
        # Nustatome naujausių duomenų objektą
        self.current_data = self.price_buffer.iloc[-1]
        
        # Sukuriame įvykius apie naujus duomenis
        for handler in self.data_events:
            try:
                handler(self.current_data)
            except Exception as e:
                logger.error(f"Klaida apdorojant duomenų įvykį: {e}")
        
        logger.debug(f"Sukurta nauja žvakė: {candle}")
    
    def _calculate_indicators(self):
        """
        Apskaičiuoja techninius indikatorius dabartiniams duomenims.
        """
        # Trumpalaikis ir ilgalaikis SMA
        self.price_buffer['SMA_short'] = self.price_buffer['close'].rolling(window=self.sma_short_period).mean()
        self.price_buffer['SMA_long'] = self.price_buffer['close'].rolling(window=self.sma_long_period).mean()
        
        # RSI
        delta = self.price_buffer['close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.rolling(window=self.rsi_period).mean()
        avg_loss = loss.rolling(window=self.rsi_period).mean()
        
        rs = avg_gain / avg_loss
        self.price_buffer['RSI_14'] = 100 - (100 / (1 + rs))
        
        # MACD
        self.price_buffer['EMA_12'] = self.price_buffer['close'].ewm(span=12, adjust=False).mean()
        self.price_buffer['EMA_26'] = self.price_buffer['close'].ewm(span=26, adjust=False).mean()
        self.price_buffer['MACD'] = self.price_buffer['EMA_12'] - self.price_buffer['EMA_26']
        self.price_buffer['MACD_Signal'] = self.price_buffer['MACD'].ewm(span=9, adjust=False).mean()
        
        # Pridedame signalų stulpelius, panašiai kaip simuliatoriaus duomenyse
        self.price_buffer['SMA_Signal'] = np.where(self.price_buffer['SMA_short'] > self.price_buffer['SMA_long'], 0.5, -0.5)
        self.price_buffer['RSI_Signal'] = np.where(self.price_buffer['RSI_14'] < 30, 0.7, 
                                            np.where(self.price_buffer['RSI_14'] > 70, -0.7, 0))
        self.price_buffer['MACD_Signal_Value'] = np.where(self.price_buffer['MACD'] > self.price_buffer['MACD_Signal'], 0.6, -0.6)
        
        # Dirbtinis ML signalų stulpelis testavimui realiu laiku
        close_pct_change = self.price_buffer['close'].pct_change(3)
        self.price_buffer['predicted_direction'] = np.where(close_pct_change > 0, 1, -1)
        self.price_buffer['confidence'] = np.minimum(np.abs(close_pct_change) * 10, 1.0)