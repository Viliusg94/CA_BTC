import requests
import logging
import random
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def get_real_bitcoin_price():
    """Get current Bitcoin price from CoinGecko API"""
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            price = data['bitcoin']['usd']
            logger.info(f"Fetched Bitcoin price: ${price}")
            return float(price)
        else:
            logger.warning(f"CoinGecko API returned status {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"Error fetching Bitcoin price: {str(e)}")
        return None

def get_bitcoin_price_history(days=30):
    """Get Bitcoin price history from CoinGecko"""
    try:
        url = f"https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days={days}"
        response = requests.get(url, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            prices = []
            dates = []
            volumes = []
            
            for price_point in data['prices']:
                timestamp = price_point[0] / 1000  # Convert from milliseconds
                price = price_point[1]
                date = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
                
                dates.append(date)
                prices.append(price)
            
            for volume_point in data['total_volumes']:
                volume = volume_point[1]
                volumes.append(volume)
            
            logger.info(f"Fetched {len(prices)} price points for {days} days")
            
            return {
                'dates': dates,
                'prices': prices,
                'close': prices,  # Close same as price for this API
                'volumes': volumes,
                'success': True
            }
        else:
            logger.warning(f"Price history API returned status {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"Error fetching price history: {str(e)}")
        return None

def generate_mock_bitcoin_data(days=30):
    """Generate mock Bitcoin data for testing"""
    logger.info(f"Generating mock Bitcoin data for {days} days")
    
    # Get current real price as baseline
    current_price = get_real_bitcoin_price()
    if not current_price:
        current_price = 45000  # Fallback price
    
    dates = []
    prices = []
    volumes = []
    
    # Generate data for the past 'days' days
    for i in range(days, 0, -1):
        date = (datetime.now() - timedelta(days=i-1)).strftime('%Y-%m-%d')
        
        # Simulate price movement with trend and volatility
        if i == 1:  # Today - use current price
            price = current_price
        else:
            # Generate price with some randomness
            daily_change = random.uniform(-0.05, 0.05)  # ±5% daily change
            trend = 0.001 * (days - i)  # Small upward trend
            price = current_price * (1 + daily_change + trend)
        
        # Generate volume
        volume = random.randint(1000000, 5000000)  # Mock volume
        
        dates.append(date)
        prices.append(round(price, 2))
        volumes.append(volume)
    
    return {
        'dates': dates,
        'prices': prices,
        'close': prices,
        'volumes': volumes,
        'success': True
    }
