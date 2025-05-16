"""
Užsakymų vykdymo modulis
-----------------------------
Šis modulis realizuoja užsakymų vykdymo logiką, 
įskaitant komisinius mokesčius ir kainų praslydimą.
"""

import logging
import random
import numpy as np
from datetime import datetime
from database.models import Trade

logger = logging.getLogger(__name__)

class OrderExecutor:
    """
    Užsakymų vykdymo klasė, kuri simuliuoja užsakymų vykdymą 
    su komisiniu mokesčiu ir kainos praslydimu.
    """
    def __init__(self, db_session, fee_model='percentage', fee_percentage=0.001, 
                 slippage_model='random', slippage_range=(0.0001, 0.002)):
        """
        Inicializuoja užsakymų vykdytoją.
        
        Args:
            db_session: SQLAlchemy duomenų bazės sesija
            fee_model (str): Komisinių mokesčių modelis ('percentage', 'fixed', 'tiered', 'none')
            fee_percentage (float): Komisinio mokesčio procentas (0.001 = 0.1%)
            slippage_model (str): Praslydimo modelis ('random', 'fixed', 'proportional', 'none')
            slippage_range (tuple): Praslydimo diapazono ribos (min, max) procentiniu formatu
        """
        self.db_session = db_session
        
        # Komisiniai mokesčiai
        self.fee_model = fee_model
        self.fee_percentage = fee_percentage
        
        # Kainos praslydimas
        self.slippage_model = slippage_model
        self.slippage_range = slippage_range
        
        logger.info(f"Inicializuotas užsakymų vykdytojas: fee_model={fee_model}, fee_percentage={fee_percentage*100}%, "
                   f"slippage_model={slippage_model}, slippage_range={slippage_range}")
    
    def execute_order(self, portfolio, action, amount, target_price, timestamp, 
                     stop_loss=None, take_profit=None):
        """
        Vykdo prekybos užsakymą su mokesčiais ir praslydimu.
        
        Args:
            portfolio: Portfelio objektas
            action (str): Užsakymo veiksmas ('buy' arba 'sell')
            amount (float): BTC kiekis
            target_price (float): Norima įvykdymo kaina
            timestamp: Užsakymo laikas
            stop_loss (float, optional): Stop-loss kaina
            take_profit (float, optional): Take-profit kaina
        
        Returns:
            dict: Užsakymo vykdymo rezultatas
        """
        try:
            # Apskaičiuojame kainą su praslydimu
            execution_price = self._apply_slippage(target_price, action)
            
            # Apskaičiuojame mokesčius
            fees = self._calculate_fees(amount, execution_price)
            
            # Apskaičiuojame bendrą užsakymo vertę
            trade_value = amount * execution_price
            
            # Vykdome užsakymą pagal veiksmą
            if action == 'buy':
                # Patikriname, ar užtenka lėšų
                total_cost = trade_value + fees
                
                if portfolio.balance < total_cost:
                    logger.warning(f"Nepakanka lėšų: turima ${portfolio.balance:.2f}, reikia ${total_cost:.2f}")
                    return {
                        'status': 'error',
                        'message': 'Insufficient funds',
                        'required': total_cost,
                        'available': portfolio.balance
                    }
                
                # Atliekame pirkimo operaciją
                portfolio.balance -= total_cost
                portfolio.btc_amount += amount
                
                # Išsaugome į log
                logger.info(f"Įvykdytas PIRKIMO užsakymas: {amount:.6f} BTC po ${execution_price:.2f} "
                           f"(praslydimas: ${execution_price-target_price:.2f}, mokesčiai: ${fees:.2f})")
                
            elif action == 'sell':
                # Patikriname, ar užtenka BTC
                if portfolio.btc_amount < amount:
                    logger.warning(f"Nepakanka BTC: turima {portfolio.btc_amount:.6f}, reikia {amount:.6f}")
                    return {
                        'status': 'error',
                        'message': 'Insufficient BTC',
                        'required': amount,
                        'available': portfolio.btc_amount
                    }
                
                # Atliekame pardavimo operaciją
                portfolio.btc_amount -= amount
                portfolio.balance += (trade_value - fees)
                
                # Išsaugome į log
                logger.info(f"Įvykdytas PARDAVIMO užsakymas: {amount:.6f} BTC po ${execution_price:.2f} "
                           f"(praslydimas: ${target_price-execution_price:.2f}, mokesčiai: ${fees:.2f})")
                
            else:
                logger.error(f"Nežinomas veiksmas: {action}")
                return {
                    'status': 'error',
                    'message': f'Unknown action: {action}'
                }
            
            # Atnaujiname portfelio atnaujinimo laiką
            portfolio.update_time = datetime.now()
            
            # Sukuriame prekybos operacijos įrašą
            trade = Trade(
                portfolio_id=portfolio.id,
                trade_type=action,
                btc_amount=amount,
                price=execution_price,
                value=trade_value,
                fees=fees,
                slippage=abs(execution_price - target_price),
                stop_loss=stop_loss,
                take_profit=take_profit,
                timestamp=timestamp
            )
            
            # Išsaugome operaciją duomenų bazėje
            self.db_session.add(trade)
            self.db_session.commit()
            
            # Grąžiname sėkmės rezultatą
            return {
                'status': 'success',
                'action': action,
                'amount': amount,
                'target_price': target_price,
                'execution_price': execution_price,
                'value': trade_value,
                'fees': fees,
                'slippage': abs(execution_price - target_price),
                'slippage_percentage': abs(execution_price - target_price) / target_price * 100,
                'trade_id': trade.id
            }
            
        except Exception as e:
            logger.error(f"Klaida vykdant užsakymą: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def _apply_slippage(self, target_price, action):
        """
        Pritaiko kainos praslydimą prie tikslinės kainos.
        
        Args:
            target_price (float): Norima įvykdymo kaina
            action (str): Užsakymo veiksmas ('buy' arba 'sell')
        
        Returns:
            float: Kaina su pritaikytu praslydimu
        """
        if self.slippage_model == 'none':
            return target_price
        
        slippage_percentage = 0.0
        
        if self.slippage_model == 'fixed':
            # Fiksuotas praslydimas
            slippage_percentage = self.slippage_range[0]
            
        elif self.slippage_model == 'random':
            # Atsitiktinis praslydimas nurodytame diapazone
            slippage_percentage = random.uniform(self.slippage_range[0], self.slippage_range[1])
            
        elif self.slippage_model == 'proportional':
            # Praslydimas proporcingas kainai (didesnis praslydimas, kai kaina aukštesnė)
            base_slippage = np.mean(self.slippage_range)
            volatility_factor = min(1.0, target_price / 10000)  # Paprastas volatility modelis
            slippage_percentage = base_slippage * (1 + volatility_factor)
        
        # Perkant kaina yra didesnė, parduodant - mažesnė
        if action == 'buy':
            execution_price = target_price * (1 + slippage_percentage)
        else:  # sell
            execution_price = target_price * (1 - slippage_percentage)
        
        return execution_price
    
    def _calculate_fees(self, amount, execution_price):
        """
        Apskaičiuoja užsakymo mokesčius.
        
        Args:
            amount (float): BTC kiekis
            execution_price (float): Įvykdymo kaina
        
        Returns:
            float: Mokesčių suma
        """
        if self.fee_model == 'none':
            return 0.0
        
        trade_value = amount * execution_price
        
        if self.fee_model == 'percentage':
            # Procentiniai mokesčiai
            return trade_value * self.fee_percentage
            
        elif self.fee_model == 'fixed':
            # Fiksuotas mokestis
            return 5.0  # Pavyzdžiui, $5 fiksuotas mokestis
            
        elif self.fee_model == 'tiered':
            # Pakopiniai mokesčiai pagal prekybos vertę
            if trade_value < 1000:
                return trade_value * 0.002  # 0.2% iki $1,000
            elif trade_value < 10000:
                return trade_value * 0.001  # 0.1% nuo $1,000 iki $10,000
            else:
                return trade_value * 0.0005  # 0.05% virš $10,000
        
        # Numatytasis - procentiniai mokesčiai
        return trade_value * self.fee_percentage