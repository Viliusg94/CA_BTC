import pandas as pd
from datetime import datetime, timedelta
from database import db
from database.models.model_models import Model
from database.models.results_models import Prediction, Trade, Metric

class AnalysisService:
    def get_bitcoin_price_data(self, timeframe='1y'):
        """Gauna Bitcoin kainos duomenis"""
        # Čia reiktų gauti duomenis iš duomenų bazės arba API
        # Pavyzdinio kodo dalis:
        
        end_date = datetime.now()
        
        if timeframe == '1m':
            start_date = end_date - timedelta(days=30)
        elif timeframe == '3m':
            start_date = end_date - timedelta(days=90)
        elif timeframe == '6m':
            start_date = end_date - timedelta(days=180)
        else:  # 1y default
            start_date = end_date - timedelta(days=365)
        
        # Čia sukuriame pavyzdinius duomenis, bet realiame projekte 
        # šie duomenys turėtų būti gaunami iš duomenų bazės
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        prices = [30000 + i * 100 for i in range(len(dates))]
        
        return {
            'dates': [d.strftime('%Y-%m-%d') for d in dates],
            'prices': prices
        }
    
    def get_trained_models(self):
        """Gauna visus apmokytus modelius"""
        # Reikėtų gauti modelius iš duomenų bazės
        models = db.query(Model).filter_by(trained=True).all()
        return models
    
    def get_graph_data(self, graph_type='price', timeframe='1y', model_id=None):
        """
        Gauna duomenis grafiko piešimui
        
        :param graph_type: Grafiko tipas (price, prediction, performance)
        :param timeframe: Laiko intervalo filtras (1m, 3m, 6m, 1y, all)
        :param model_id: Modelio ID, jei reikia specifinio modelio duomenų
        :return: Duomenys grafiko piešimui
        """
        if graph_type == 'price':
            return self.get_bitcoin_price_data(timeframe)
        
        elif graph_type == 'prediction':
            if not model_id:
                return {'error': 'Model ID is required for prediction graphs'}
            
            # Gauti modelio prognozes
            predictions = db.query(Prediction).filter_by(simulation_id=model_id).all()
            
            dates = [p.date.strftime('%Y-%m-%d') for p in predictions]
            actual_prices = [p.price for p in predictions]
            predicted_values = [1 if p.prediction == 'kils' else 0 for p in predictions]
            
            return {
                'dates': dates,
                'actual': actual_prices,
                'predicted': predicted_values
            }
        
        elif graph_type == 'performance':
            if not model_id:
                return {'error': 'Model ID is required for performance graphs'}
            
            # Gauti modelio prekybos rezultatus
            trades = db.query(Trade).filter_by(simulation_id=model_id).order_by(Trade.date).all()
            
            dates = [t.date.strftime('%Y-%m-%d') for t in trades]
            balances = [t.balance_after for t in trades]
            
            return {
                'dates': dates,
                'balances': balances
            }
        
        return {'error': 'Invalid graph type'}