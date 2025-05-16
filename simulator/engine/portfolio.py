"""
Prekybos portfelis
-----------------------------
Šis modulis realizuoja virtualaus prekybos portfelio funkcionalumą,
kuris valdo balansą, kriprovaliutos kiekį ir prekybos operacijas.
"""

class Portfolio:
    """
    Virtualaus prekybos portfelio klasė.
    """
    def __init__(self, initial_balance=10000.0):
        """
        Inicializuoja portfelį.
        
        Args:
            initial_balance (float): Pradinis balansas
        """
        self.initial_balance = initial_balance
        self.balance = initial_balance  # USD balansas
        self.btc_amount = 0.0  # BTC kiekis
        self.btc_value = 0.0  # BTC vertė USD
        self.total_value = initial_balance  # Bendra portfelio vertė (balansas + BTC vertė)
    
    def reset(self):
        """
        Atstato portfelį į pradinę būseną.
        """
        self.balance = self.initial_balance
        self.btc_amount = 0.0
        self.btc_value = 0.0
        self.total_value = self.initial_balance
    
    def update_btc_value(self, current_price):
        """
        Atnaujina BTC vertę pagal dabartinę kainą.
        
        Args:
            current_price (float): Dabartinė BTC kaina
        """
        self.btc_value = self.btc_amount * current_price
        self.total_value = self.balance + self.btc_value
    
    def buy(self, btc_amount, price, commission_rate=0.001):
        """
        Perka BTC už nurodytą kainą.
        
        Args:
            btc_amount (float): BTC kiekis
            price (float): Kaina už vieną BTC
            commission_rate (float): Komisinių mokesčių tarifas (0.001 = 0.1%)
        
        Returns:
            bool: True, jei operacija sėkminga, False - jei ne
        """
        # Apskaičiuojame operacijos vertę su komisiniais
        trade_value = btc_amount * price
        commission = trade_value * commission_rate
        total_cost = trade_value + commission
        
        # Tikriname, ar pakanka lėšų
        if total_cost > self.balance:
            return False
        
        # Vykdome operaciją
        self.balance -= total_cost
        self.btc_amount += btc_amount
        self.update_btc_value(price)
        
        return True
    
    def sell(self, btc_amount, price, commission_rate=0.001):
        """
        Parduoda BTC už nurodytą kainą.
        
        Args:
            btc_amount (float): BTC kiekis
            price (float): Kaina už vieną BTC
            commission_rate (float): Komisinių mokesčių tarifas (0.001 = 0.1%)
        
        Returns:
            bool: True, jei operacija sėkminga, False - jei ne
        """
        # Tikriname, ar pakanka BTC
        if btc_amount > self.btc_amount:
            return False
        
        # Apskaičiuojame operacijos vertę ir komisinius
        trade_value = btc_amount * price
        commission = trade_value * commission_rate
        net_value = trade_value - commission
        
        # Vykdome operaciją
        self.balance += net_value
        self.btc_amount -= btc_amount
        self.update_btc_value(price)
        
        return True