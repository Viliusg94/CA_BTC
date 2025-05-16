"""
Simuliatoriaus variklis
-----------------------------
Šis modulis realizuoja prekybos simuliatoriaus variklio funkcionalumą,
kuris valdo virtualų balansą, portfelį ir laiko juostą.
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
import os
from simulator.engine.portfolio import Portfolio

# Sukuriame logerį
logger = logging.getLogger(__name__)

class SimulatorEngine:
    """
    Simuliatoriaus variklio klasė, kuri valdo prekybos simuliaciją.
    """
    def __init__(self, data, initial_balance=10000.0, commission_rate=0.001, start_date=None, end_date=None):
        """
        Inicializuoja simuliatoriaus variklį.
        
        Args:
            data (pandas.DataFrame): Istoriniai duomenys su kainomis ir indikatoriais
            initial_balance (float): Pradinis balansas
            commission_rate (float): Komisinių mokesčių tarifas (0.001 = 0.1%)
            start_date (datetime, optional): Simuliacijos pradžios data
            end_date (datetime, optional): Simuliacijos pabaigos data
        """
        self.data = data.sort_index()  # Užtikriname, kad duomenys yra surikiuoti pagal laiką
        
        # Nustatome simuliacijos laiko rėžius
        if start_date is None:
            start_date = self.data.index[0]
        if end_date is None:
            end_date = self.data.index[-1]
            
        # Filtruojame duomenis pagal laiko rėžius
        self.data = self.data.loc[start_date:end_date]
        
        if self.data.empty:
            raise ValueError("Nėra duomenų nurodytame laiko intervale")
            
        # Inicializuojame simuliacijos būseną
        self.current_index = 0
        self.current_time = self.data.index[0]
        self.commission_rate = commission_rate
        
        # Sukuriame portfelį
        self.portfolio = Portfolio(initial_balance=initial_balance)
        
        # Sukuriame įrašų (logs) direktoriją
        self._setup_logging_directory()
        
        # Įvykių žurnalas
        self.events_log = []
        
        logger.info(f"Simuliatoriaus variklis inicializuotas. Pradinis balansas: {initial_balance}, "
                  f"Laiko rėžiai: {start_date} - {end_date}")
    
    def _setup_logging_directory(self):
        """
        Sukuria simuliacijos įrašų (logs) direktoriją.
        """
        log_dir = "logs/simulator"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Sukuriame failo tvarkytuvą simuliatoriaus įrašams
        handler = logging.FileHandler(f"{log_dir}/simulator_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        
        # Pridedame tvarkytuvą prie šio klasės logerio
        class_logger = logging.getLogger(__name__)
        class_logger.addHandler(handler)
    
    def step(self):
        """
        Vykdo vieną simuliacijos žingsnį.
        
        Returns:
            bool: True, jei simuliacija dar nesibaigė, False - jei jau baigėsi
        """
        if self.current_index >= len(self.data) - 1:
            logger.info("Simuliacija baigta")
            return False
        
        # Pereiti prie kito laiko taško
        self.current_index += 1
        self.current_time = self.data.index[self.current_index]
        
        # Atnaujiname portfelio būseną pagal naujas kainas
        self._update_portfolio_value()
        
        return True
    
    def _update_portfolio_value(self):
        """
        Atnaujina portfelio vertę pagal dabartines kainas.
        """
        current_price = self.get_current_price()
        
        # Atnaujiname BTC vertę portfelyje
        self.portfolio.update_btc_value(current_price)
        
        # Įrašome portfelio vertę į įvykių žurnalą
        self.log_event("portfolio_update", {
            "time": self.current_time,
            "balance": self.portfolio.balance,
            "btc_amount": self.portfolio.btc_amount,
            "btc_value": self.portfolio.btc_value,
            "total_value": self.portfolio.total_value
        })
    
    def reset(self):
        """
        Atstato simuliatorių į pradinę būseną.
        """
        self.current_index = 0
        self.current_time = self.data.index[0]
        self.portfolio.reset()
        self.events_log = []
        
        logger.info("Simuliatorius atstatytas į pradinę būseną")
    
    def run_full_simulation(self, strategy):
        """
        Vykdo pilną simuliaciją su nurodyta strategija.
        
        Args:
            strategy: Prekybos strategijos objektas
        
        Returns:
            pandas.DataFrame: Simuliacijos rezultatai
        """
        logger.info(f"Pradedama pilna simuliacija su strategija: {strategy.__class__.__name__}")
        
        # Atstatome simuliatorių
        self.reset()
        
        # Vykdome simuliaciją iki pabaigos
        while True:
            # Gauname dabartinę kainą ir indikatorius
            current_data = self.get_current_data()
            
            # Generuojame prekybos sprendimą pagal strategiją
            decision = strategy.generate_decision(current_data, self.portfolio, self.current_time)
            
            # Vykdome prekybos sprendimą
            if decision is not None and decision["action"] != "hold":
                self.execute_trade(decision)
            
            # Pereiname prie kito žingsnio
            if not self.step():
                break
        
        # Grąžiname simuliacijos rezultatus
        return self.get_results()
    
    def get_current_data(self):
        """
        Grąžina dabartinio laiko taško duomenis.
        
        Returns:
            pandas.Series: Dabartinio laiko taško duomenys
        """
        return self.data.iloc[self.current_index]
    
    def get_current_price(self):
        """
        Grąžina dabartinę kainą.
        
        Returns:
            float: Dabartinė kaina
        """
        return self.get_current_data()['Close']
    
    def execute_trade(self, decision):
        """
        Vykdo prekybos operaciją.
        
        Args:
            decision (dict): Prekybos sprendimas su tokiais raktais:
                - action: 'buy', 'sell' arba 'hold'
                - amount: BTC kiekis (jei None, naudojamas visas galimas kiekis)
                - price: Kaina (jei None, naudojama dabartinė rinkos kaina)
                - stop_loss: Stop-loss kaina (pasirinktinai)
                - take_profit: Take-profit kaina (pasirinktinai)
        
        Returns:
            bool: True, jei operacija sėkminga, False - jei ne
        """
        # Gauname dabartinę kainą, jei nenurodyta
        price = decision.get("price", self.get_current_price())
        
        # Gauname kiekį, jei nenurodyta
        action = decision["action"]
        
        if action == "buy":
            # Jei kiekis nenurodytas, naudojame visą galimą balansą
            if decision.get("amount") is None:
                # Investuojame 95% turimo balanso (palikdami 5% komisiniams)
                amount_to_invest = self.portfolio.balance * 0.95
                btc_amount = amount_to_invest / price
            else:
                btc_amount = decision["amount"]
            
            # Perkame BTC
            success = self.portfolio.buy(btc_amount, price, self.commission_rate)
            
            if success:
                # Įrašome operaciją į įvykių žurnalą
                self.log_event("trade", {
                    "time": self.current_time,
                    "action": "buy",
                    "btc_amount": btc_amount,
                    "price": price,
                    "value": btc_amount * price,
                    "commission": btc_amount * price * self.commission_rate,
                    "balance_after": self.portfolio.balance,
                    "btc_amount_after": self.portfolio.btc_amount,
                    "total_value_after": self.portfolio.total_value
                })
                
                logger.info(f"Įvykdyta pirkimo operacija: {btc_amount} BTC po {price}, "
                          f"vertė: {btc_amount * price}, komisiniai: {btc_amount * price * self.commission_rate}")
                
                return True
            else:
                logger.warning(f"Nepavyko įvykdyti pirkimo operacijos: nepakanka lėšų")
                return False
                
        elif action == "sell":
            # Jei kiekis nenurodytas, parduodame visą turimą BTC
            if decision.get("amount") is None:
                btc_amount = self.portfolio.btc_amount
            else:
                btc_amount = decision["amount"]
            
            # Parduodame BTC
            success = self.portfolio.sell(btc_amount, price, self.commission_rate)
            
            if success:
                # Įrašome operaciją į įvykių žurnalą
                self.log_event("trade", {
                    "time": self.current_time,
                    "action": "sell",
                    "btc_amount": btc_amount,
                    "price": price,
                    "value": btc_amount * price,
                    "commission": btc_amount * price * self.commission_rate,
                    "balance_after": self.portfolio.balance,
                    "btc_amount_after": self.portfolio.btc_amount,
                    "total_value_after": self.portfolio.total_value
                })
                
                logger.info(f"Įvykdyta pardavimo operacija: {btc_amount} BTC po {price}, "
                          f"vertė: {btc_amount * price}, komisiniai: {btc_amount * price * self.commission_rate}")
                
                return True
            else:
                logger.warning(f"Nepavyko įvykdyti pardavimo operacijos: nepakanka BTC")
                return False
        
        else:
            logger.warning(f"Nežinomas operacijos tipas: {action}")
            return False
    
    def log_event(self, event_type, event_data):
        """
        Įrašo įvykį į žurnalą.
        
        Args:
            event_type (str): Įvykio tipas
            event_data (dict): Įvykio duomenys
        """
        event = {
            "event_type": event_type,
            "timestamp": datetime.now(),
            "simulation_time": self.current_time,
            "data": event_data
        }
        
        self.events_log.append(event)
    
    def get_results(self):
        """
        Grąžina simuliacijos rezultatus.
        
        Returns:
            pandas.DataFrame: Simuliacijos rezultatų DataFrame
        """
        # Filtruojame tik portfelio atnaujinimo įvykius
        portfolio_events = [event for event in self.events_log if event["event_type"] == "portfolio_update"]
        
        # Konvertuojame į DataFrame
        if not portfolio_events:
            return pd.DataFrame()
            
        results_data = []
        for event in portfolio_events:
            data = event["data"]
            results_data.append({
                "time": data["time"],
                "balance": data["balance"],
                "btc_amount": data["btc_amount"],
                "btc_value": data["btc_value"],
                "total_value": data["total_value"]
            })
        
        results_df = pd.DataFrame(results_data)
        
        # Nustatome time kaip indeksą
        if "time" in results_df.columns:
            results_df.set_index("time", inplace=True)
        
        # Pridedame kainos duomenis
        price_data = self.data[["Close"]].copy()
        price_data.columns = ["price"]
        
        # Sujungiame duomenis
        final_results = pd.merge(
            results_df,
            price_data,
            left_index=True,
            right_index=True,
            how="left"
        )
        
        # Apskaičiuojame pradinę ir galutinę portfelio vertę
        initial_value = final_results["total_value"].iloc[0]
        final_value = final_results["total_value"].iloc[-1]
        
        # Apskaičiuojame bendrus metrikus
        total_return = (final_value / initial_value) - 1
        
        # Apskaičiuojame Buy & Hold strategijos grąžą
        initial_price = self.data["Close"].iloc[0]
        final_price = self.data["Close"].iloc[-1]
        buy_hold_return = (final_price / initial_price) - 1
        
        # Pridedame metrikus prie rezultatų
        final_results.attrs["initial_value"] = initial_value
        final_results.attrs["final_value"] = final_value
        final_results.attrs["total_return"] = total_return
        final_results.attrs["buy_hold_return"] = buy_hold_return
        final_results.attrs["excess_return"] = total_return - buy_hold_return
        
        logger.info(f"Simuliacijos rezultatai: pradinė vertė = {initial_value}, galutinė vertė = {final_value}, "
                  f"grąža = {total_return*100:.2f}%, Buy & Hold grąža = {buy_hold_return*100:.2f}%, "
                  f"papildoma grąža = {(total_return-buy_hold_return)*100:.2f}%")
        
        return final_results