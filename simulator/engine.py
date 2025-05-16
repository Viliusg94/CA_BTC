"""
Prekybos simuliatoriaus variklis
-----------------------------
Šis modulis realizuoja pagrindinį prekybos simuliatoriaus variklį,
kuris koordinuoja visus simuliatoriaus komponentus.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import json
import os
from database.models import Portfolio, Trade
from simulator.risk.risk_manager import RiskManager
from simulator.risk.dynamic_risk_adjuster import DynamicRiskAdjuster
from simulator.execution.order_executor import OrderExecutor
from simulator.execution.trading_statistics import TradingStatistics
from simulator.utils.data_diagnostics import check_required_columns, diagnose_data, add_test_signals

logger = logging.getLogger(__name__)

class SimulatorEngine:
    """
    Pagrindinis simuliatoriaus variklis, kuris koordinuoja visus komponentus.
    """
    def __init__(self, db_session, initial_balance=10000.0, portfolio_name="Simulator Portfolio"):
        """
        Inicializuoja simuliatoriaus variklį.
        
        Args:
            db_session: SQLAlchemy duomenų bazės sesija
            initial_balance (float): Pradinis balansas
            portfolio_name (str): Portfelio pavadinimas
        """
        self.db_session = db_session
        self.initial_balance = initial_balance
        self.portfolio_name = portfolio_name
        
        # Inicializuojame komponentus
        self.risk_manager = RiskManager()
        self.dynamic_risk_adjuster = DynamicRiskAdjuster()
        self.order_executor = OrderExecutor(db_session)
        self.trading_statistics = TradingStatistics()
        self.stats = self.trading_statistics
        
        # Sukuriame arba gauname portfelį
        self.portfolio = self._get_or_create_portfolio()
        
        # Simuliacijos būsena
        self.current_time = None
        self.data = None
        self.is_running = False
        self.active_positions = {}  # symbol -> position_info
        
        # Simuliacijos rezultatai
        self.results = {
            "trades": [],
            "portfolio_values": [],
            "metrics": {}
        }
        
        logger.info(f"Inicializuotas simuliatoriaus variklis. Pradinis balansas: {initial_balance}")
    
    def _get_or_create_portfolio(self):
        """
        Gauna arba sukuria portfelį duomenų bazėje.
        
        Returns:
            Portfolio: Portfelio objektas
        """
        # Bandome rasti portfelį pagal pavadinimą
        portfolio = self.db_session.query(Portfolio).filter_by(name=self.portfolio_name).first()
        
        # Jei nerastas, sukuriame naują
        if not portfolio:
            portfolio = Portfolio(
                name=self.portfolio_name,
                balance=self.initial_balance,
                btc_amount=0.0,
                description="Prekybos simuliatoriaus portfelis",
                create_time=datetime.now(),
                update_time=datetime.now()
            )
            self.db_session.add(portfolio)
            self.db_session.commit()
            logger.info(f"Sukurtas naujas portfelis: {self.portfolio_name}")
        else:
            # Atnaujiname portfelio būseną
            portfolio.balance = self.initial_balance
            portfolio.btc_amount = 0.0
            portfolio.update_time = datetime.now()
            self.db_session.commit()
            logger.info(f"Atnaujintas esamas portfelis: {self.portfolio_name}")
        
        return portfolio
    
    def load_data(self, data):
        """
        Įkelia duomenis į simuliatorių.
        
        Args:
            data (pandas.DataFrame): Duomenų rinkinys su kainomis ir indikatoriais
        
        Returns:
            bool: True, jei duomenys sėkmingai įkelti
        """
        if data is None or data.empty:
            logger.error("Bandoma įkelti tuščius duomenis")
            return False
        
        # Įsitikiname, kad duomenys surikiuoti pagal datą
        if not isinstance(data.index, pd.DatetimeIndex):
            logger.error("Duomenų indeksas nėra DatetimeIndex tipo")
            return False
        
        # PATOBULINIMAS: Atliekame duomenų diagnostiką
        logger.info("Atliekama duomenų diagnostika...")
        diagnostics_results = diagnose_data(data)
        
        # PATOBULINIMAS: Patikriname, ar yra reikalingi stulpeliai
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        if not check_required_columns(data, required_columns):
            logger.warning("Trūksta kai kurių pagrindinių kainų stulpelių")
        
        # PATOBULINIMAS: Tikriname, ar yra techniniai indikatoriai ir ML prognozės
        has_indicators = any(col.endswith('_Signal') for col in data.columns)
        has_predictions = 'predicted_direction' in data.columns and 'confidence' in data.columns
        
        # PATOBULINIMAS: Jei trūksta indikatorių ar prognozių, pridedame testinius
        if not has_indicators or not has_predictions:
            logger.warning("Duomenyse trūksta techninių indikatorių arba ML prognozių")
            logger.info("Pridedami testiniai signalai ir prognozės simuliacijos testavimui")
            data = add_test_signals(data)
        
        self.data = data.sort_index()
        self.current_time = self.data.index[0]
        logger.info(f"Įkelti duomenys nuo {self.data.index[0]} iki {self.data.index[-1]} ({len(self.data)} eilutės)")
        
        return True
    
    def add_strategy(self, strategy):
        """
        Prideda prekybos strategiją.
        
        Args:
            strategy: Prekybos strategijos objektas
        """
        self.strategy = strategy
        logger.info(f"Pridėta strategija: {strategy.name}")
    
    def reset(self):
        """
        Atstato simuliatoriaus būseną į pradinę.
        """
        # Atstatome portfelio būseną
        self.portfolio.balance = self.initial_balance
        self.portfolio.btc_amount = 0.0
        self.portfolio.update_time = datetime.now()
        self.db_session.commit()
        
        # Atstatome simuliacijos būseną
        self.current_time = self.data.index[0] if self.data is not None else None
        self.current_timestamp = self.current_time  # Užtikriname, kad yra abi laiko kintamųjų versijos
        self.is_running = False
        self.active_positions = {}  # Išvalome aktyvias pozicijas
        
        # Išvalome simuliacijos rezultatus
        self.results = {
            "trades": [],
            "portfolio_values": [],
            "metrics": {}
        }
        
        # Išvalome prekybos istoriją
        self.trade_history = []
        
        # Atstatome prekybos statistiką
        self.trading_statistics = TradingStatistics()
        
        logger.info("Simuliatoriaus būsena atstatyta į pradinę")
    
    def run_simulation(self, generators=None, strategy_list=None, risk_params=None):
        """
        Vykdo pilną simuliaciją nuo pradžios iki pabaigos.
        
        Args:
            generators (list): SignalGenerator objektų sąrašas
            strategy_list (list): TradingStrategy objektų sąrašas
            risk_params (dict, optional): Rizikos parametrai
        
        Returns:
            dict: Simuliacijos rezultatai
        """
        # Parengiame parametrus
        signal_generators = generators or []
        strategies = strategy_list or []
        risk_parameters = risk_params or {}
        
        if self.data is None or len(self.data) == 0:
            logger.error("Nėra įkeltų duomenų. Naudokite load_data() prieš vykdydami simuliaciją.")
            return {'error': 'No data loaded'}
        
        # Atstata simuliatoriaus būseną
        self.reset()
        
        # Saugome portfelio vertės istoriją
        portfolio_values = []
        
        # Vykdome žingsnius per visus duomenis
        results = []
        
        logger.info(f"Pradedama simuliacija su {len(self.data)} įrašais")
        
        # Vykdome simuliaciją per visus duomenis
        step_count = 0
        while True:
            step_result = self.step(signal_generators, strategies, risk_parameters)
            
            if step_result is None:
                logger.error("step_result yra None - kažkas rimtai blogai su step metodu")
                break
            elif 'error' in step_result or step_result.get('status') == 'finished':
                break
            
            # Pridedame portfelio vertę į istoriją
            portfolio_values.append({
                'timestamp': self.current_timestamp,
                'portfolio_value': step_result['portfolio_value']
            })
            
            results.append(step_result)
            step_count += 1
        
        # Sukuriame portfelio vertės DataFrame
        portfolio_df = pd.DataFrame(portfolio_values)
        if not portfolio_df.empty:
            portfolio_df.set_index('timestamp', inplace=True)
        
        # PATAISYMAS: Naudojame trading_statistics vietoj stats
        try:
            self.performance_metrics = self.trading_statistics.calculate_metrics()
        except AttributeError:
            logger.error("Nerastas trading_statistics atributas")
            self.performance_metrics = {}
        
        # Išsaugome rezultatus į failą
        self._save_simulation_results(results, self.performance_metrics)
        
        logger.info(f"Simuliacija baigta. Įvykdyta {step_count} žingsnių, {len(self.trade_history)} sandorių.")
        
        return {
            'results': results,
            'portfolio_history': portfolio_df,
            'trade_history': self.trade_history,
            'performance_metrics': self.performance_metrics
        }
    
    def step(self, signal_generators, strategies, risk_parameters=None):
        """
        Vykdo vieną simuliacijos žingsnį.
        
        Args:
            signal_generators (list): SignalGenerator objektų sąrašas
            strategies (list): TradingStrategy objektų sąrašas
            risk_parameters (dict, optional): Rizikos parametrai
        
        Returns:
            dict: Žingsnio rezultatai
        """
        # Pradinis rezultato žodynas, kuris visada bus grąžintas
        step_result = {
            'status': 'active',
            'signals': [],
            'decisions': []
        }
        
        try:
            if self.current_time is None:
                logger.error("Nenustatytas current_time. Patikrinkite, ar įkelti duomenys.")
                step_result['error'] = 'No current time'
                step_result['status'] = 'finished'
                return step_result
            
            # Užtikriname, kad current_time yra Timestamp tipo
            if not isinstance(self.current_time, pd.Timestamp):
                self.current_time = pd.Timestamp(self.current_time)
            
            # Tiesiogiai gauname sekančią laiko žymą be .tolist() konvertavimo
            try:
                # Randame visas laiko žymas po einamojo laiko
                future_times = self.data.index[self.data.index > self.current_time]
                
                # Jei nėra laiko žymų po einamojo laiko, baigėme simuliaciją
                if len(future_times) == 0:
                    logger.info("Pasiekta duomenų pabaiga.")
                    step_result['status'] = 'finished'
                    return step_result
                
                # Gauname pirmą laiko žymą po einamojo laiko
                self.current_timestamp = future_times[0]
                self.current_time = self.current_timestamp  # Sinchronizuojame abu laiko kintamuosius
                
            except Exception as e:
                logger.error(f"Klaida ieškant sekančios laiko žymos: {e}")
                step_result['error'] = f'Error finding next timestamp: {e}'
                step_result['status'] = 'finished'
                return step_result
            
            # Gauname dabartinius duomenis pagal laiko žymą
            try:
                current_data = self.data.loc[self.current_timestamp]
            except KeyError:
                logger.warning(f"Nėra duomenų laiko žymai {self.current_timestamp}")
                step_result['error'] = f'No data for timestamp {self.current_timestamp}'
                return step_result
            
            # Pridedame laiko žymą ir kainą į rezultatą
            step_result['timestamp'] = self.current_timestamp
            step_result['btc_price'] = current_data.get('Close', 0)
            
            # Gauname istorinius duomenis
            historical_data = self.data.loc[:self.current_timestamp].tail(100)  # Paskutinės 100 eilučių
            
            # Generuojame signalus
            signals = []
            for generator in signal_generators:
                try:
                    signal = generator.generate_signal(current_data, historical_data, self.current_timestamp)
                    if signal:  # Pridedame tik jei signalas nėra None
                        signals.append(signal)
                except Exception as e:
                    logger.error(f"Klaida generuojant signalą: {e}")
                    # Nepridedame signal į sąrašą jei kyla klaida, bet tęsiame darbą
            
            step_result['signals'] = signals
            
            # Generuojame prekybos sprendimus
            decisions = []
            for strategy in strategies:
                try:
                    decision = strategy.generate_decision(signals, current_data, self.portfolio, self.current_timestamp)
                    if decision and decision.get('action') in ['buy', 'sell']:
                        decisions.append(decision)
                except Exception as e:
                    logger.error(f"Klaida generuojant prekybos sprendimą: {e}")
                    # Nepridedame decision į sąrašą jei kyla klaida, bet tęsiame darbą
            
            step_result['decisions'] = decisions
            
            try:
                # Atnaujiname aktyvias pozicijas
                self._update_active_positions(current_data)
                
                # Vykdome sprendimus
                for decision in decisions:
                    self._execute_trade_decision(decision, current_data)
                
                # Apskaičiuojame portfelio vertę
                btc_price = current_data.get('Close', 0)
                portfolio_value = self.portfolio.balance + (self.portfolio.btc_amount * btc_price)
                
                # Papildome rezultatus
                step_result['portfolio_value'] = portfolio_value
                step_result['balance'] = self.portfolio.balance
                step_result['btc_amount'] = self.portfolio.btc_amount
            except Exception as e:
                logger.error(f"Klaida vykdant simuliacijos žingsnį: {e}")
                step_result['error'] = str(e)
            
        except Exception as e:
            logger.error(f"Netikėta klaida žingsnyje: {e}")
            step_result['error'] = str(e)
        
        return step_result
    
    def _update_active_positions(self, current_data):
        """
        Atnaujina aktyvias pozicijas, tikrina stop-loss ir take-profit sąlygas.
        
        Args:
            current_data (pandas.Series): Dabartinė kainų ir indikatorių eilutė
        """
        if not self.active_positions:
            return
        
        positions_to_close = []
        current_price = current_data["Close"]
        
        # Tikriname kiekvieną aktyvią poziciją
        for symbol, position in self.active_positions.items():
            # Tikriname, ar reikia atnaujinti trailing stop
            if position["trailing_stop_enabled"] and position["position_type"] == "long":
                # Ilgoji pozicija: jei kaina pakilo, atnaujiname trailing stop
                if current_price > position["entry_price"] and current_price > position["highest_price"]:
                    position["highest_price"] = current_price
                    # Atnaujiname trailing stop kainą
                    new_stop_loss = current_price * (1 - position["trailing_stop_percent"])
                    if new_stop_loss > position["stop_loss"]:
                        position["stop_loss"] = new_stop_loss
                        logger.info(f"Atnaujintas trailing stop: {position['stop_loss']}")
            
            # Tikriname stop-loss sąlygą ilgajai pozicijai
            if position["position_type"] == "long" and current_price <= position["stop_loss"]:
                logger.info(f"Aktyvuotas stop-loss ({position['stop_loss']}) ilgajai pozicijai")
                positions_to_close.append((symbol, "stop_loss", position["stop_loss"]))
            
            # Tikriname take-profit sąlygą ilgajai pozicijai
            elif position["position_type"] == "long" and current_price >= position["take_profit"]:
                logger.info(f"Aktyvuotas take-profit ({position['take_profit']}) ilgajai pozicijai")
                positions_to_close.append((symbol, "take_profit", position["take_profit"]))
        
        # Uždarome pozicijas, kurios pasiekė stop-loss arba take-profit
        for symbol, reason, price in positions_to_close:
            position = self.active_positions[symbol]
            self._close_position(symbol, price, reason)
    
    def _close_position(self, symbol, price, reason):
        """
        Uždaro aktyvią poziciją.
        
        Args:
            symbol (str): Prekybos simbolis
            price (float): Pozicijos uždarymo kaina
            reason (str): Pozicijos uždarymo priežastis
        """
        if symbol not in self.active_positions:
            logger.warning(f"Bandoma uždaryti neegzistuojančią poziciją: {symbol}")
            return
        
        position = self.active_positions[symbol]
        
        # Sukuriame prekybos operaciją
        trade_decision = {
            "action": "sell" if position["position_type"] == "long" else "buy",
            "symbol": symbol,
            "price": price,
            "amount": position["amount"],
            "reason": reason
        }
        
        # Vykdome prekybos operaciją
        self._execute_trade_decision(trade_decision, None)
        
        # Pašaliname poziciją iš aktyvių
        del self.active_positions[symbol]
    
    def _execute_trade_decision(self, decision, current_data):
        """
        Vykdo prekybos sprendimą.
        
        Args:
            decision (dict): Prekybos sprendimo informacija
            current_data (pandas.Series): Dabartinė kainų ir indikatorių eilutė
        """
        action = decision["action"]
        symbol = decision.get("symbol", "BTC")
        price = decision.get("price", current_data["Close"] if current_data is not None else None)
        
        if price is None:
            logger.error("Nenurodyta prekybos kaina ir nėra dabartinių duomenų")
            return
        
        if action == "buy":
            # Skaičiuojame pozicijos dydį
            amount_to_spend = self.portfolio.balance * self.risk_manager.risk_per_trade
            amount_to_spend = min(amount_to_spend, self.portfolio.balance * 0.95)  # Neišleidžiame daugiau nei 95% balanso
            
            # Skaičiuojame stop-loss ir take-profit
            stop_loss, take_profit = self.risk_manager.calculate_stop_loss_take_profit(
                price, "long", current_data.get("ATR_14", None)
            )
            
            # Skaičiuojame BTC kiekį
            btc_amount = amount_to_spend / price
            
            # Vykdome pirkimo operaciją
            trade_result = self.order_executor.execute_order(
                self.portfolio.id,
                "buy",
                btc_amount,
                price,
                self.current_time
            )
            
            if trade_result:
                # Atnaujiname portfelio būseną
                self.portfolio = trade_result["portfolio"]
                
                # Pridedame operaciją į rezultatus
                self.results["trades"].append(trade_result["trade_info"])
                
                # Sukuriame naują aktyvią poziciją
                self.active_positions[symbol] = {
                    "position_type": "long",
                    "entry_price": price,
                    "amount": btc_amount,
                    "stop_loss": stop_loss,
                    "take_profit": take_profit,
                    "entry_time": self.current_time,
                    "highest_price": price,
                    "trailing_stop_enabled": True,
                    "trailing_stop_percent": 0.02  # 2% nuo aukščiausios kainos
                }
                
                logger.info(f"Atidaryta ilgoji pozicija: {btc_amount} BTC po {price} (stop-loss: {stop_loss}, take-profit: {take_profit})")
        
        elif action == "sell":
            # Jei turime aktyvią poziciją, uždarome ją
            if symbol in self.active_positions:
                position = self.active_positions[symbol]
                btc_amount = position["amount"]
            else:
                # Parduodame visą turimą BTC
                btc_amount = self.portfolio.btc_amount
            
            if btc_amount <= 0:
                logger.warning("Bandoma parduoti, bet nėra BTC")
                return
            
            # Vykdome pardavimo operaciją
            trade_result = self.order_executor.execute_order(
                self.portfolio.id,
                "sell",
                btc_amount,
                price,
                self.current_time
            )
            
            if trade_result:
                # Atnaujiname portfelio būseną
                self.portfolio = trade_result["portfolio"]
                
                # Pridedame operaciją į rezultatus
                self.results["trades"].append(trade_result["trade_info"])
                
                # Jei buvo aktyvi pozicija, pašaliname ją
                if symbol in self.active_positions:
                    del self.active_positions[symbol]
                
                logger.info(f"Parduota: {btc_amount} BTC po {price}")
    
    def _calculate_performance_metrics(self):
        """
        Skaičiuoja veiklos rezultatų metrikas.
        """
        if not self.results["portfolio_values"]:
            logger.warning("Nėra portfelio verčių metrikų skaičiavimui")
            return
        
        # Sukuriame DataFrame su portfelio vertėmis
        df = pd.DataFrame(self.results["portfolio_values"])
        df.set_index("timestamp", inplace=True)
        
        # Skaičiuojame metrikos
        initial_value = df["portfolio_value"].iloc[0]
        final_value = df["portfolio_value"].iloc[-1]
        returns = (final_value / initial_value) - 1
        
        # Skaičiuojame dieninį pelną/nuostolį
        df["daily_return"] = df["portfolio_value"].pct_change()
        
        # Skaičiuojame Sharpe rodiklį (jei turime pakankamai duomenų)
        sharpe_ratio = None
        if len(df) > 1:
            risk_free_rate = 0.02 / 365  # 2% metinis nerizikingos investicijos pelnas
            excess_returns = df["daily_return"] - risk_free_rate
            sharpe_ratio = np.sqrt(252) * excess_returns.mean() / excess_returns.std()
        
        # Skaičiuojame maksimalų kritimą (drawdown)
        df["cumulative_return"] = (1 + df["daily_return"]).cumprod()
        df["cumulative_max"] = df["cumulative_return"].cummax()
        df["drawdown"] = (df["cumulative_return"] / df["cumulative_max"]) - 1
        max_drawdown = df["drawdown"].min()
        
        # Skaičiuojame prekybos metrikos
        trades_df = pd.DataFrame(self.results["trades"])
        winning_trades = 0
        losing_trades = 0
        
        if not trades_df.empty and "profit" in trades_df.columns:
            winning_trades = len(trades_df[trades_df["profit"] > 0])
            losing_trades = len(trades_df[trades_df["profit"] < 0])
        
        total_trades = winning_trades + losing_trades
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        # Išsaugome metrikas
        self.results["metrics"] = {
            "initial_value": initial_value,
            "final_value": final_value,
            "total_return": returns,
            "total_return_pct": returns * 100,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_drawdown,
            "max_drawdown_pct": max_drawdown * 100,
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": win_rate,
            "win_rate_pct": win_rate * 100
        }
        
        logger.info(f"Apskaičiuotos veiklos metrikos: pelnas: {returns*100:.2f}%, win rate: {win_rate*100:.2f}%")
    
    def _save_simulation_results(self, results, metrics):
        """
        Išsaugo simuliacijos rezultatus.
        
        Args:
            results (list): Simuliacijos rezultatų sąrašas
            metrics (dict): Veiklos metrikos
        """
        # Sukuriame rezultatų katalogą, jei jo nėra
        os.makedirs("data/simulation", exist_ok=True)
        
        # Sukuriame rezultatų dataframe
        if results:
            df_results = pd.DataFrame(results)
            df_results.to_csv("data/simulation/simulation_results.csv", index=False)
        
        # Išsaugome metrikas į JSON
        with open("data/simulation/metrics.json", "w") as f:
            json.dump(metrics, f, indent=4)
        
        logger.info("Simuliacijos rezultatai išsaugoti data/simulation/ kataloge")
    
    def plot_results(self):
        """
        Atvaizduoja simuliacijos rezultatus grafiškai.
        
        Returns:
            matplotlib.figure.Figure: Rezultatų grafikas
        """
        if not self.results["portfolio_values"]:
            logger.warning("Nėra duomenų grafikui")
            return None
        
        try:
            import matplotlib.pyplot as plt
            import matplotlib.dates as mdates
            
            # Sukuriame DataFrame su portfelio vertėmis
            df = pd.DataFrame(self.results["portfolio_values"])
            df.set_index("timestamp", inplace=True)
            
            # Sukuriame grafiką
            fig, axes = plt.subplots(2, 1, figsize=(12, 10), gridspec_kw={"height_ratios": [3, 1]})
            
            # Viršutinis grafikas: portfelio vertė ir BTC kaina
            ax1 = axes[0]
            ax1.plot(df.index, df["portfolio_value"], label="Portfelio vertė", color="blue")
            
            # Pridedame antrą y ašį BTC kainai
            ax2 = ax1.twinx()
            ax2.plot(df.index, df["btc_price"], label="BTC kaina", color="orange", alpha=0.7)
            
            # Pridedame pirkimo ir pardavimo taškus
            trades_df = pd.DataFrame(self.results["trades"])
            if not trades_df.empty:
                trades_df["timestamp"] = pd.to_datetime(trades_df["timestamp"])
                buys = trades_df[trades_df["trade_type"] == "buy"]
                sells = trades_df[trades_df["trade_type"] == "sell"]
                
                if not buys.empty:
                    ax2.scatter(buys["timestamp"], buys["price"], color="green", marker="^", s=100, label="Pirkimas")
                if not sells.empty:
                    ax2.scatter(sells["timestamp"], sells["price"], color="red", marker="v", s=100, label="Pardavimas")
            
            # Apatinis grafikas: portfelio pelnas/nuostolis
            ax3 = axes[1]
            initial_value = df["portfolio_value"].iloc[0]
            df["portfolio_return"] = (df["portfolio_value"] / initial_value - 1) * 100
            df["btc_return"] = (df["btc_price"] / df["btc_price"].iloc[0] - 1) * 100
            
            ax3.plot(df.index, df["portfolio_return"], label="Portfelio pelnas", color="blue")
            ax3.plot(df.index, df["btc_return"], label="BTC pelnas", color="orange", alpha=0.7)
            ax3.axhline(y=0, color="gray", linestyle="--")
            
            # Nustatome ašių formaterius
            for ax in [ax1, ax2, ax3]:
                ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
                ax.xaxis.set_major_locator(mdates.MonthLocator())
                ax.grid(True, alpha=0.3)
            
            # Pridedame legendas
            ax1.legend(loc="upper left")
            ax2.legend(loc="upper right")
            ax3.legend(loc="upper left")
            
            # Pridedame antraštes
            ax1.set_title("Prekybos simuliacijos rezultatai")
            ax1.set_ylabel("Portfelio vertė ($)")
            ax2.set_ylabel("BTC kaina ($)")
            ax3.set_ylabel("Pelnas/nuostolis (%)")
            ax3.set_xlabel("Data")
            
            # Pridedame metrikas teksto forma
            metrics = self.results["metrics"]
            metrics_text = (
                f"Pradinis kapitalas: ${metrics['initial_value']:.2f}\n"
                f"Galutinė vertė: ${metrics['final_value']:.2f}\n"
                f"Bendras pelnas: {metrics['total_return_pct']:.2f}%\n"
                f"Sharpe rodiklis: {metrics['sharpe_ratio']:.2f}\n"
                f"Maks. kritimas: {metrics['max_drawdown_pct']:.2f}%\n"
                f"Sandorių skaičius: {metrics['total_trades']}\n"
                f"Sėkmės rodiklis: {metrics['win_rate_pct']:.2f}%"
            )
            
            # Pridedame metrikas viršutinio grafiko kampe
            ax1.text(
                0.02, 0.98, metrics_text,
                transform=ax1.transAxes,
                verticalalignment="top",
                bbox=dict(boxstyle="round", facecolor="white", alpha=0.8)
            )
            
            plt.tight_layout()
            
            # Išsaugome grafiką
            results_dir = "data/simulation_results"
            os.makedirs(results_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            plt.savefig(f"{results_dir}/simulation_plot_{timestamp}.png")
            
            return fig
            
        except Exception as e:
            logger.error(f"Klaida kuriant grafiką: {e}")
            return None