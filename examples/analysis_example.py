"""
Simuliacijos rezultatų ir prekybos sandorių analizės pavyzdys.
"""
import sys
import os
import logging
from datetime import datetime, timezone, timedelta

# Pridedame pagrindinį projekto katalogą į kelią
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importuojame reikalingas bibliotekas
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

# Importuojame duomenų bazės prisijungimo URL
from database import SQLALCHEMY_DATABASE_URL
from services.simulation_service import SimulationService
from services.trade_service import TradeService

# Konfigūruojame žurnalą
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """
    Pagrindinis pavyzdžio vykdymo metodas.
    """
    # Prisijungiame prie duomenų bazės
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    session = Session(engine)
    
    try:
        # Inicializuojame servisus
        logger.info("Inicializuojami servisai")
        simulation_service = SimulationService(session)
        trade_service = TradeService(session)
        
        # Gaukime visų simuliacijų sąrašą
        logger.info("Gaunamas simuliacijų sąrašas")
        simulations = simulation_service.list_simulations()
        
        if not simulations:
            logger.error("Nėra simuliacijų duomenų bazėje! Pirmiausia sukurkite simuliaciją.")
            return
        
        # Pasirinkime pirmą simuliaciją analizei
        selected_simulation = simulations[0]
        logger.info(f"Analizuojama simuliacija: {selected_simulation.name} ({selected_simulation.id})")
        
        # Pagrindinė simuliacijos informacija
        logger.info("=== SIMULIACIJOS REZULTATAI ===")
        logger.info(f"Pradinis kapitalas: {selected_simulation.initial_capital} USD")
        logger.info(f"Galutinis balansas: {selected_simulation.final_balance} USD")
        logger.info(f"Bendras pelnas/nuostolis: {selected_simulation.profit_loss} USD")
        logger.info(f"Grąža (ROI): {selected_simulation.roi * 100:.2f}%")
        
        if selected_simulation.max_drawdown:
            logger.info(f"Maksimalus nuosmukis: {selected_simulation.max_drawdown * 100:.2f}%")
        
        if selected_simulation.total_trades and selected_simulation.total_trades > 0:
            logger.info(f"Sandorių skaičius: {selected_simulation.total_trades}")
            
            if selected_simulation.winning_trades is not None:
                win_percentage = selected_simulation.winning_trades / selected_simulation.total_trades * 100
                logger.info(f"Pelningų sandorių: {selected_simulation.winning_trades} ({win_percentage:.2f}%)")
            
            if selected_simulation.losing_trades is not None:
                lose_percentage = selected_simulation.losing_trades / selected_simulation.total_trades * 100
                logger.info(f"Nuostolingų sandorių: {selected_simulation.losing_trades} ({lose_percentage:.2f}%)")
        
        # Dabar sukurkime keletą prekybos sandorių šiai simuliacijai analizei, jei jų dar nėra
        simulation_trades = simulation_service.get_simulation_trades(selected_simulation.id)
        
        if not simulation_trades:
            logger.info("Kuriami pavyzdiniai prekybos sandoriai analizei")
            
            # Simuliacijos pradžios ir pabaigos datos
            start_date = selected_simulation.start_date
            end_date = selected_simulation.end_date
            
            # Laiko intervalai simuliacijos metu
            days_between = (end_date - start_date).days if end_date and start_date else 30
            if days_between <= 0:
                days_between = 30  # Naudokime numatytąją reikšmę, jei neteisinga
            
            # Sukurkime kelis pavyzdinius sandorius
            # Pirmasis sandoris - pirkimas
            buy_trade_data = {
                "portfolio_id": 1,
                "trade_type": "market",
                "btc_amount": 0.2,
                "price": 30000.0,
                "value": 6000.0,  # 0.2 BTC * 30000 USD = 6000 USD
                "timestamp": start_date + timedelta(days=1) if start_date else datetime.now(timezone.utc),
                "simulation_id": selected_simulation.id,
                "date": start_date + timedelta(days=1) if start_date else datetime.now(timezone.utc),
                "type": "buy",
                "amount": 0.2,
                "fee": 6.0,  # 0.1% nuo 6000 USD = 6 USD
                "created_at": datetime.now(timezone.utc)
            }
            
            buy_trade = trade_service.create_trade(buy_trade_data)
            if buy_trade:
                logger.info(f"Sukurtas pirkimo sandoris: ID = {buy_trade.id}, Kiekis = {buy_trade.btc_amount} BTC, Kaina = {buy_trade.price} USD")
            else:
                logger.error("Nepavyko sukurti pirkimo sandorio!")
            
            # Antrasis sandoris - pardavimas
            sell_trade_data = {
                "portfolio_id": 1,
                "trade_type": "market",
                "btc_amount": 0.2,
                "price": 32000.0,
                "value": 6400.0,  # 0.2 BTC * 32000 USD = 6400 USD
                "timestamp": start_date + timedelta(days=10) if start_date else datetime.now(timezone.utc) + timedelta(days=1),
                "simulation_id": selected_simulation.id,
                "date": start_date + timedelta(days=10) if start_date else datetime.now(timezone.utc) + timedelta(days=1),
                "type": "sell",
                "amount": 0.2,
                "fee": 6.4,  # 0.1% nuo 6400 USD = 6.4 USD
                "profit_loss": 387.6,  # (6400 - 6000) - (6 + 6.4) = 387.6 USD
                "created_at": datetime.now(timezone.utc)
            }
            
            sell_trade = trade_service.create_trade(sell_trade_data)
            if sell_trade:
                logger.info(f"Sukurtas pardavimo sandoris: ID = {sell_trade.id}, Kiekis = {sell_trade.btc_amount} BTC, Kaina = {sell_trade.price} USD")
            else:
                logger.error("Nepavyko sukurti pardavimo sandorio!")
        
        # Gaukime visus simuliacijos prekybos sandorius po sukūrimo
        simulation_trades = simulation_service.get_simulation_trades(selected_simulation.id)
        logger.info(f"=== PREKYBOS SANDORIAI (viso: {len(simulation_trades)}) ===")
        
        # Atspausdinkime sandorius
        total_profit = 0.0
        for i, trade in enumerate(simulation_trades, 1):
            profit_text = f", Pelnas/nuostolis: {trade.profit_loss} USD" if trade.profit_loss else ""
            trade_date = trade.date.strftime('%Y-%m-%d') if trade.date else "Nežinoma data"
            logger.info(f"{i}. {trade_date}: {trade.type.upper() if trade.type else 'NEŽINOMAS'} {trade.btc_amount} BTC @ {trade.price} USD{profit_text}")
            
            # Skaičiuojame bendrą pelną
            if trade.profit_loss:
                total_profit += trade.profit_loss
        
        logger.info(f"Bendras apskaičiuotas sandorių pelnas/nuostolis: {total_profit} USD")
        
        # Analizuokime pirkimo ir pardavimo kainas
        buy_trades = [t for t in simulation_trades if t.type == 'buy']
        sell_trades = [t for t in simulation_trades if t.type == 'sell']
        
        if buy_trades:
            avg_buy_price = sum(t.price for t in buy_trades) / len(buy_trades)
            logger.info(f"Vidutinė pirkimo kaina: {avg_buy_price:.2f} USD")
        else:
            logger.info("Nėra pirkimo sandorių analizei")
            avg_buy_price = 0
        
        if sell_trades:
            avg_sell_price = sum(t.price for t in sell_trades) / len(sell_trades)
            logger.info(f"Vidutinė pardavimo kaina: {avg_sell_price:.2f} USD")
        else:
            logger.info("Nėra pardavimo sandorių analizei")
            avg_sell_price = 0
        
        if buy_trades and sell_trades:
            price_diff = avg_sell_price - avg_buy_price
            price_diff_percent = (price_diff / avg_buy_price * 100) if avg_buy_price else 0
            logger.info(f"Kainų skirtumas: {price_diff:.2f} USD ({price_diff_percent:.2f}%)")
        
    except Exception as e:
        logger.error(f"Įvyko klaida vykdant pavyzdį: {str(e)}")
    finally:
        # Uždarome sesiją kai baigėme
        logger.info("Uždaroma duomenų bazės sesija")
        session.close()

if __name__ == "__main__":
    main()