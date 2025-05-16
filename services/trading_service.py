"""
Prekybos servisas
-----------------------------
Šis modulis apibrėžia TradingService klasę, kuri generuoja prekybos signalus,
valdo prekybos strategijas ir skaičiuoja portfelio rezultatus.
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from database.unit_of_work import UnitOfWork
from database.models import BtcPriceData, TechnicalIndicator, TradingSignal, Portfolio, Trade
from services.data_service import DataService

# Sukuriame logerį
logger = logging.getLogger(__name__)

class TradingService:
    """
    Prekybos servisas, kuris generuoja prekybos signalus ir strategijas.
    """
    def __init__(self, session):
        """
        Inicializuoja prekybos servisą su sesija.
        
        Args:
            session: SQLAlchemy sesija
        """
        self.session = session
        self.data_service = DataService(session)
        self.uow = UnitOfWork(session)
    
    def generate_trading_signals(self, method='combined'):
        """
        Generuoja prekybos signalus pagal nurodytą metodą.
        
        Args:
            method: Signalų generavimo metodas:
                - 'combined' - indikatorių kombinacija
                - 'sma_crossover' - SMA kryžiavimasis
                - 'rsi' - RSI indikatorius
                - 'macd' - MACD indikatorius
                - 'bollinger' - Bollinger juostos
                - 'ml' - mašininio mokymosi prognozės
        
        Returns:
            pandas.DataFrame: Duomenys su prekybos signalais
        """
        try:
            # Gauname duomenis analizei
            df = self.data_service.get_data_for_analysis()
            
            if df.empty:
                logger.warning("Nerasti duomenys signalų generavimui.")
                return df
            
            # Generuojame signalus pagal nurodytą metodą
            if method == 'sma_crossover':
                return self._generate_sma_crossover_signals(df)
            elif method == 'rsi':
                return self._generate_rsi_signals(df)
            elif method == 'macd':
                return self._generate_macd_signals(df)
            elif method == 'bollinger':
                return self._generate_bollinger_signals(df)
            elif method == 'ml':
                return self._generate_ml_signals(df)
            elif method == 'combined':
                return self._generate_combined_signals(df)
            else:
                logger.warning(f"Neteisingas signalų generavimo metodas: {method}. Naudojama 'combined'.")
                return self._generate_combined_signals(df)
                
        except Exception as e:
            logger.error(f"Klaida generuojant prekybos signalus: {e}")
            return pd.DataFrame()
    
    def _generate_sma_crossover_signals(self, df, short_period=7, long_period=25):
        """
        Generuoja signalus pagal SMA kryžiavimąsi.
        
        Args:
            df: DataFrame su duomenimis
            short_period: Trumpojo SMA periodas
            long_period: Ilgojo SMA periodas
        
        Returns:
            pandas.DataFrame: Duomenys su signalais
        """
        try:
            data = df.copy()
            
            # Tikriname, ar yra reikalingi stulpeliai
            short_col = f'SMA_{short_period}'
            long_col = f'SMA_{long_period}'
            
            if short_col not in data.columns or long_col not in data.columns:
                logger.warning(f"Nerasti SMA stulpeliai: {short_col} ir/arba {long_col}")
                return data
            
            # Skaičiuojame kryžiavimosi signalus
            data['SMA_Crossover'] = data[short_col] - data[long_col]
            data['SMA_Signal'] = 0
            
            # Nustatome signalus pagal kryžiavimąsi
            # 1 = pirkti (trumpasis > ilgasis), -1 = parduoti (trumpasis < ilgasis)
            for i in range(1, len(data)):
                if data['SMA_Crossover'].iloc[i-1] < 0 and data['SMA_Crossover'].iloc[i] > 0:
                    data.loc[data.index[i], 'SMA_Signal'] = 1  # Pirkimo signalas
                elif data['SMA_Crossover'].iloc[i-1] > 0 and data['SMA_Crossover'].iloc[i] < 0:
                    data.loc[data.index[i], 'SMA_Signal'] = -1  # Pardavimo signalas
            
            return data
        
        except Exception as e:
            logger.error(f"Klaida generuojant SMA kryžiavimosi signalus: {e}")
            return df
    
    def _generate_rsi_signals(self, df, rsi_period=14, oversold=30, overbought=70):
        """
        Generuoja signalus pagal RSI indikatorių.
        
        Args:
            df: DataFrame su duomenimis
            rsi_period: RSI periodas
            oversold: Perparduotumo lygis
            overbought: Perpirktumo lygis
        
        Returns:
            pandas.DataFrame: Duomenys su signalais
        """
        try:
            data = df.copy()
            
            # Tikriname, ar yra reikalingi stulpeliai
            rsi_col = f'RSI_{rsi_period}'
            
            if rsi_col not in data.columns:
                logger.warning(f"Nerastas RSI stulpelis: {rsi_col}")
                return data
            
            # Inicializuojame signalų stulpelį
            data['RSI_Signal'] = 0
            
            # Nustatome signalus pagal RSI
            # 1 = pirkti (RSI < oversold), -1 = parduoti (RSI > overbought)
            for i in range(1, len(data)):
                # Pirkimo signalas: RSI buvo žemiau perparduotumo lygio ir dabar kyla virš jo
                if data[rsi_col].iloc[i-1] < oversold and data[rsi_col].iloc[i] > oversold:
                    data.loc[data.index[i], 'RSI_Signal'] = 1
                # Pardavimo signalas: RSI buvo aukščiau perpirktumo lygio ir dabar krenta žemiau jo
                elif data[rsi_col].iloc[i-1] > overbought and data[rsi_col].iloc[i] < overbought:
                    data.loc[data.index[i], 'RSI_Signal'] = -1
            
            return data
        
        except Exception as e:
            logger.error(f"Klaida generuojant RSI signalus: {e}")
            return df
    
    def _generate_macd_signals(self, df):
        """
        Generuoja signalus pagal MACD indikatorių.
        
        Args:
            df: DataFrame su duomenimis
        
        Returns:
            pandas.DataFrame: Duomenys su signalais
        """
        try:
            data = df.copy()
            
            # Tikriname, ar yra reikalingi stulpeliai
            if 'MACD' not in data.columns or 'MACD_signal' not in data.columns:
                logger.warning("Nerasti MACD stulpeliai: MACD ir/arba MACD_signal")
                return data
            
            # Inicializuojame signalų stulpelį
            data['MACD_Signal'] = 0
            
            # Nustatome signalus pagal MACD kryžiavimąsi
            # 1 = pirkti (MACD kerta signalo liniją iš apačios), -1 = parduoti (MACD kerta signalo liniją iš viršaus)
            for i in range(1, len(data)):
                # Pirkimo signalas: MACD kerta signalo liniją iš apačios
                if data['MACD'].iloc[i-1] < data['MACD_signal'].iloc[i-1] and data['MACD'].iloc[i] > data['MACD_signal'].iloc[i]:
                    data.loc[data.index[i], 'MACD_Signal'] = 1
                # Pardavimo signalas: MACD kerta signalo liniją iš viršaus
                elif data['MACD'].iloc[i-1] > data['MACD_signal'].iloc[i-1] and data['MACD'].iloc[i] < data['MACD_signal'].iloc[i]:
                    data.loc[data.index[i], 'MACD_Signal'] = -1
            
            return data
        
        except Exception as e:
            logger.error(f"Klaida generuojant MACD signalus: {e}")
            return df
    
    def _generate_bollinger_signals(self, df):
        """
        Generuoja signalus pagal Bollinger juostas.
        
        Args:
            df: DataFrame su duomenimis
        
        Returns:
            pandas.DataFrame: Duomenys su signalais
        """
        try:
            data = df.copy()
            
            # Tikriname, ar yra reikalingi stulpeliai
            if 'Bollinger_upper' not in data.columns or 'Bollinger_lower' not in data.columns:
                logger.warning("Nerasti Bollinger juostų stulpeliai: Bollinger_upper ir/arba Bollinger_lower")
                return data
            
            # Inicializuojame signalų stulpelį
            data['Bollinger_Signal'] = 0
            
            # Nustatome signalus pagal Bollinger juostas
            # 1 = pirkti (kaina žemiau apatinės juostos), -1 = parduoti (kaina viršija viršutinę juostą)
            for i in range(1, len(data)):
                # Pirkimo signalas: kaina buvo žemiau apatinės juostos ir dabar kyla virš jos
                if data['Close'].iloc[i-1] < data['Bollinger_lower'].iloc[i-1] and data['Close'].iloc[i] > data['Bollinger_lower'].iloc[i]:
                    data.loc[data.index[i], 'Bollinger_Signal'] = 1
                # Pardavimo signalas: kaina buvo virš viršutinės juostos ir dabar krenta žemiau jos
                elif data['Close'].iloc[i-1] > data['Bollinger_upper'].iloc[i-1] and data['Close'].iloc[i] < data['Bollinger_upper'].iloc[i]:
                    data.loc[data.index[i], 'Bollinger_Signal'] = -1
            
            return data
        
        except Exception as e:
            logger.error(f"Klaida generuojant Bollinger juostų signalus: {e}")
            return df
    
    def _generate_ml_signals(self, df):
        """
        Generuoja signalus pagal mašininio mokymosi prognozes.
        
        Args:
            df: DataFrame su duomenimis
        
        Returns:
            pandas.DataFrame: Duomenys su signalais
        """
        try:
            data = df.copy()
            
            # Patikriname, ar turime prognozes
            with self.uow:
                # Gauname naujausias prognozes
                predictions = self.uow.predictions.get_latest_predictions(horizon=1, limit=30)
                
                if not predictions:
                    logger.warning("Nerasta prognozių ML signalams generuoti.")
                    return data
                
                # Sukuriame prognozių DataFrame
                pred_data = []
                for pred in predictions:
                    pred_data.append({
                        'timestamp': pred.timestamp,
                        'predicted_direction': pred.predicted_direction,
                        'confidence': pred.confidence
                    })
                
                if not pred_data:
                    return data
                
                pred_df = pd.DataFrame(pred_data)
                pred_df.set_index('timestamp', inplace=True)
                
                # Sujungiame su originaliais duomenimis
                merged = pd.merge_asof(
                    data.sort_index(),
                    pred_df.sort_index(),
                    left_index=True,
                    right_index=True,
                    direction='nearest'
                )
                
                # Sukuriame ML signalų stulpelį
                # Jei predicted_direction yra 1 (kils) ir confidence > 0.7, generuojame pirkimo signalą
                # Jei predicted_direction yra 0 (kris) ir confidence > 0.7, generuojame pardavimo signalą
                merged['ML_Signal'] = 0
                merged.loc[(merged['predicted_direction'] == 1) & (merged['confidence'] > 0.7), 'ML_Signal'] = 1
                merged.loc[(merged['predicted_direction'] == 0) & (merged['confidence'] > 0.7), 'ML_Signal'] = -1
                
                # Išsaugome ML_Signal stulpelį originaliame DataFrame
                data['ML_Signal'] = merged['ML_Signal']
                
                return data
                
        except Exception as e:
            logger.error(f"Klaida generuojant ML signalus: {e}")
            return df
    
    def _generate_combined_signals(self, df):
        """
        Generuoja bendrus signalus pagal visus indikatorius.
        
        Args:
            df: DataFrame su duomenimis
        
        Returns:
            pandas.DataFrame: Duomenys su signalais
        """
        try:
            # Generuojame signalus pagal kiekvieną indikatorių
            data = self._generate_sma_crossover_signals(df)
            data = self._generate_rsi_signals(data)
            data = self._generate_macd_signals(data)
            data = self._generate_bollinger_signals(data)
            
            # Patikriname, ar yra ML modelio prognozės ir pridedame jas
            try:
                data = self._generate_ml_signals(data)
            except Exception as e:
                logger.warning(f"ML signalai nepridėti: {e}")
                data['ML_Signal'] = 0
            
            # Sukuriame Combined_Signal stulpelį
            data['Combined_Signal'] = 0
            
            # Sujungiame visus signalus į vieną
            # Skaičiuojame signalų sumą
            signal_columns = ['SMA_Signal', 'RSI_Signal', 'MACD_Signal', 'Bollinger_Signal', 'ML_Signal']
            available_columns = [col for col in signal_columns if col in data.columns]
            
            if available_columns:
                # Skaičiuojame bendrą signalą kaip svorių sumą
                # ML signalui duodame didesnį svorį (2)
                signal_weights = {
                    'SMA_Signal': 1,
                    'RSI_Signal': 1,
                    'MACD_Signal': 1,
                    'Bollinger_Signal': 1,
                    'ML_Signal': 2
                }
                
                # Inicializuojame svoriais pasvertą signalų sumą
                data['Signal_Sum'] = 0
                
                # Pridedame kiekvieno signalo indėlį
                for col in available_columns:
                    if col in data.columns:
                        data['Signal_Sum'] += data[col] * signal_weights.get(col, 1)
                
                # Nustatome bendrus signalus
                # Jei suma > 2, generuojame pirkimo signalą
                # Jei suma < -2, generuojame pardavimo signalą
                data.loc[data['Signal_Sum'] >= 2, 'Combined_Signal'] = 1
                data.loc[data['Signal_Sum'] <= -2, 'Combined_Signal'] = -1
            
            # Išsaugome signalus duomenų bazėje
            self._save_signals_to_db(data)
            
            return data
                
        except Exception as e:
            logger.error(f"Klaida generuojant bendrus signalus: {e}")
            return df
    
    def _save_signals_to_db(self, df):
        """
        Išsaugo sugeneruotus signalus duomenų bazėje.
        
        Args:
            df: DataFrame su signalais
        """
        try:
            # Išsaugome tik naujausius signalus (paskutines 30 dienų)
            latest_data = df.iloc[-30:]
            
            with self.uow:
                for idx, row in latest_data.iterrows():
                    # Tikriname, ar yra reikalingi signalų stulpeliai
                    sma_signal = row.get('SMA_Signal', 0)
                    rsi_signal = row.get('RSI_Signal', 0)
                    macd_signal = row.get('MACD_Signal', 0)
                    bollinger_signal = row.get('Bollinger_Signal', 0)
                    ml_signal = row.get('ML_Signal', 0)
                    combined_signal = row.get('Combined_Signal', 0)
                    
                    # Gauname atitinkamą kainos įrašą pagal timestamp
                    timestamp = idx
                    price_data = self.uow.btc_prices.session.query(BtcPriceData).filter(
                        BtcPriceData.timestamp == timestamp
                    ).first()
                    
                    if not price_data:
                        continue
                    
                    # Tikriname, ar jau yra signalo įrašas šiai datai
                    existing_signal = self.uow.session.query(TradingSignal).filter(
                        TradingSignal.timestamp == timestamp
                    ).first()
                    
                    if existing_signal:
                        # Atnaujiname esamą signalą
                        existing_signal.sma_signal = sma_signal
                        existing_signal.rsi_signal = rsi_signal
                        existing_signal.macd_signal = macd_signal
                        existing_signal.bollinger_signal = bollinger_signal
                        existing_signal.ml_signal = ml_signal
                        existing_signal.combined_signal = combined_signal
                        existing_signal.price_id = price_data.id
                        existing_signal.update_time = datetime.now()
                    else:
                        # Sukuriame naują signalo įrašą
                        new_signal = TradingSignal(
                            timestamp=timestamp,
                            price_id=price_data.id,
                            sma_signal=sma_signal,
                            rsi_signal=rsi_signal,
                            macd_signal=macd_signal,
                            bollinger_signal=bollinger_signal,
                            ml_signal=ml_signal,
                            combined_signal=combined_signal,
                            create_time=datetime.now(),
                            update_time=datetime.now()
                        )
                        self.uow.session.add(new_signal)
                
                # Išsaugome CSV failą analizei
                signals_path = "data/analysis/signals.csv"
                os.makedirs(os.path.dirname(signals_path), exist_ok=True)
                df.to_csv(signals_path)
                logger.info(f"Signalai išsaugoti: {signals_path}")
                
        except Exception as e:
            logger.error(f"Klaida išsaugant signalus duomenų bazėje: {e}")
    
    def backtest_strategy(self, start_date=None, end_date=None, initial_capital=10000, signal_type='Combined_Signal'):
        """
        Atlieka strategijos testavimą istoriniuose duomenyse.
        
        Args:
            start_date: Pradžios data
            end_date: Pabaigos data
            initial_capital: Pradinis kapitalas
            signal_type: Signalo tipas ('Combined_Signal', 'SMA_Signal', 'RSI_Signal', 'MACD_Signal', 'Bollinger_Signal', 'ML_Signal')
        
        Returns:
            pandas.DataFrame: Backtesting rezultatai
        """
        try:
            # Gauname duomenis su signalais
            signals_df = self.generate_trading_signals(method='combined')
            
            if signals_df.empty:
                logger.warning("Nerasti duomenys strategijos testavimui.")
                return pd.DataFrame()
            
            # Filtruojame pagal datų intervalą
            if start_date:
                signals_df = signals_df[signals_df.index >= pd.to_datetime(start_date)]
            if end_date:
                signals_df = signals_df[signals_df.index <= pd.to_datetime(end_date)]
            
            # Inicializuojame portfelio stulpelius
            signals_df['Position'] = 0  # 0 = nėra pozicijos, 1 = ilgoji pozicija
            signals_df['Portfolio_Value'] = 0.0
            signals_df['Cash'] = initial_capital
            signals_df['BTC_Holdings'] = 0.0
            signals_df['Trade_Price'] = 0.0
            signals_df['Trade_Size'] = 0.0
            
            # Inicializuojame portfelio metrikas
            current_position = 0
            cash = initial_capital
            btc_holdings = 0.0
            
            # Simuliuojame prekybą pagal signalus
            for i in range(len(signals_df)):
                # Gauname signalą ir kainą
                date = signals_df.index[i]
                price = signals_df['Close'].iloc[i]
                signal = signals_df[signal_type].iloc[i] if signal_type in signals_df.columns else 0
                
                # Nustatome poziciją ir simuliuojame prekybą
                if current_position == 0 and signal == 1:  # Perkame
                    # Investuojame 95% turimų pinigų (paliekame 5% komisiniams)
                    trade_size = cash * 0.95
                    btc_to_buy = trade_size / price
                    
                    # Atnaujiname būseną
                    btc_holdings = btc_to_buy
                    cash -= trade_size
                    current_position = 1
                    
                    # Įrašome sandorį
                    signals_df.loc[date, 'Trade_Price'] = price
                    signals_df.loc[date, 'Trade_Size'] = trade_size
                    
                elif current_position == 1 and signal == -1:  # Parduodame
                    # Parduodame visus turimus BTC
                    trade_size = btc_holdings * price
                    
                    # Atnaujiname būseną
                    cash += trade_size
                    btc_holdings = 0
                    current_position = 0
                    
                    # Įrašome sandorį
                    signals_df.loc[date, 'Trade_Price'] = price
                    signals_df.loc[date, 'Trade_Size'] = trade_size
                
                # Atnaujiname portfelio būseną
                signals_df.loc[date, 'Position'] = current_position
                signals_df.loc[date, 'BTC_Holdings'] = btc_holdings
                signals_df.loc[date, 'Cash'] = cash
                signals_df.loc[date, 'Portfolio_Value'] = cash + (btc_holdings * price)
            
            # Apskaičiuojame veiklos rezultatų metrikas
            initial_value = signals_df['Portfolio_Value'].iloc[0]
            final_value = signals_df['Portfolio_Value'].iloc[-1]
            
            holding_return = (signals_df['Close'].iloc[-1] / signals_df['Close'].iloc[0]) - 1
            strategy_return = (final_value / initial_capital) - 1
            
            outperformance = strategy_return - holding_return
            
            # Skaičiuojame Sharpe rodiklį
            daily_returns = signals_df['Portfolio_Value'].pct_change().dropna()
            sharpe_ratio = (daily_returns.mean() / daily_returns.std()) * np.sqrt(252)  # Anualizuotas
            
            # Sukuriame metrikos DataFrame
            metrics = {
                'Initial_Capital': initial_capital,
                'Final_Value': final_value,
                'Total_Return': strategy_return * 100,
                'Holding_Return': holding_return * 100,
                'Outperformance': outperformance * 100,
                'Sharpe_Ratio': sharpe_ratio,
                'Trade_Count': len(signals_df[signals_df['Trade_Size'] > 0]),
                'Win_Rate': None,  # Reikia papildomų skaičiavimų
            }
            
            # Išsaugome rezultatus CSV faile
            backtest_path = "data/analysis/backtest_results.csv"
            os.makedirs(os.path.dirname(backtest_path), exist_ok=True)
            signals_df.to_csv(backtest_path)
            
            metrics_df = pd.DataFrame([metrics])
            metrics_path = "data/analysis/backtest_metrics.csv"
            metrics_df.to_csv(metrics_path, index=False)
            
            logger.info(f"Strategijos testavimo rezultatai išsaugoti: {backtest_path}")
            logger.info(f"Strategijos testavimo metrikos išsaugotos: {metrics_path}")
            
            return signals_df
            
        except Exception as e:
            logger.error(f"Klaida testuojant strategiją: {e}")
            return pd.DataFrame()
    
    def create_portfolio(self, name, initial_balance=10000.0, description=""):
        """
        Sukuria naują prekybos portfelį.
        
        Args:
            name: Portfelio pavadinimas
            initial_balance: Pradinis balansas
            description: Portfelio aprašymas
        
        Returns:
            Portfolio: Naujas portfelis arba None, jei įvyko klaida
        """
        try:
            with self.uow:
                # Sukuriame naują portfelį
                portfolio = Portfolio(
                    name=name,
                    balance=initial_balance,
                    btc_amount=0.0,
                    description=description,
                    create_time=datetime.now(),
                    update_time=datetime.now()
                )
                
                # Išsaugome portfelį duomenų bazėje
                self.uow.session.add(portfolio)
                self.uow.commit()
                
                logger.info(f"Sukurtas naujas portfelis: {name}")
                
                return portfolio
                
        except Exception as e:
            logger.error(f"Klaida kuriant portfelį: {e}")
            return None
    
    def execute_trade(self, portfolio_id, trade_type, btc_amount, price=None):
        """
        Vykdo prekybos operaciją.
        
        Args:
            portfolio_id: Portfelio ID
            trade_type: Operacijos tipas ('buy' arba 'sell')
            btc_amount: BTC kiekis
            price: Kaina (jei nenurodyta, naudojama dabartinė rinkos kaina)
        
        Returns:
            Trade: Nauja prekybos operacija arba None, jei įvyko klaida
        """
        try:
            with self.uow:
                # Gauname portfelį
                portfolio = self.uow.session.query(Portfolio).filter_by(id=portfolio_id).first()
                
                if not portfolio:
                    logger.warning(f"Nerastas portfelis su ID: {portfolio_id}")
                    return None
                
                # Gauname dabartinę kainą, jei ji nenurodyta
                current_price = price
                if not current_price:
                    # Gauname naujausią kainą iš duomenų bazės
                    latest_price = self.uow.btc_prices.get_latest(1)
                    if not latest_price:
                        logger.warning("Nerasta kainos duomenų operacijai vykdyti.")
                        return None
                    
                    current_price = latest_price[0].close
                
                # Skaičiuojame operacijos sumą
                trade_value = btc_amount * current_price
                
                # Vykdome operaciją
                if trade_type.lower() == 'buy':
                    # Tikriname, ar užtenka lėšų
                    if portfolio.balance < trade_value:
                        logger.warning(f"Nepakanka lėšų operacijai. Turima: {portfolio.balance}, Reikia: {trade_value}")
                        return None
                    
                    # Atnaujiname portfelio būseną
                    portfolio.balance -= trade_value
                    portfolio.btc_amount += btc_amount
                    
                elif trade_type.lower() == 'sell':
                    # Tikriname, ar užtenka BTC
                    if portfolio.btc_amount < btc_amount:
                        logger.warning(f"Nepakanka BTC operacijai. Turima: {portfolio.btc_amount}, Reikia: {btc_amount}")
                        return None
                    
                    # Atnaujiname portfelio būseną
                    portfolio.balance += trade_value
                    portfolio.btc_amount -= btc_amount
                    
                else:
                    logger.warning(f"Neteisingas operacijos tipas: {trade_type}")
                    return None
                
                # Atnaujiname portfelio atnaujinimo laiką
                portfolio.update_time = datetime.now()
                
                # Sukuriame naują prekybos operacijos įrašą
                trade = Trade(
                    portfolio_id=portfolio_id,
                    trade_type=trade_type.lower(),
                    btc_amount=btc_amount,
                    price=current_price,
                    value=trade_value,
                    timestamp=datetime.now()
                )
                
                # Išsaugome operaciją duomenų bazėje
                self.uow.session.add(trade)
                self.uow.commit()
                
                logger.info(f"Įvykdyta prekybos operacija: {trade_type} {btc_amount} BTC po {current_price}")
                
                return trade
                
        except Exception as e:
            logger.error(f"Klaida vykdant prekybos operaciją: {e}")
            return None