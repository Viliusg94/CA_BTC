"""
Skydelių maršrutai
----------------
Šis modulis apibrėžia skydelių maršrutus (endpoints).
"""

from flask import Blueprint, render_template

# Sukuriame Blueprint objektą
dashboard = Blueprint('dashboard', __name__)

@dashboard.route('/')
@dashboard.route('/index')
def index():
    """Pagrindinis skydelis"""
    # Čia galima pridėti logiką duomenų gavimui
    btc_price = 50000  # Pavyzdinis BTC kursas
    portfolio_value = 15000  # Pavyzdinis portfelio vertė
    
    # Grąžiname šabloną su duomenimis
    return render_template(
        'dashboard/index.html',
        title='Skydelis',
        btc_price=btc_price,
        portfolio_value=portfolio_value
    )