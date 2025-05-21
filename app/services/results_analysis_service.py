import logging
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
from app.services.results_data_service import ResultsDataService

logger = logging.getLogger(__name__)

class ResultsAnalysisService:
    """
    Servisas rezultatų analizei
    Teikia metodus duomenų filtravimui, grupavimui, agregavimui ir analizei
    """
    
    def __init__(self):
        """
        Inicializuoja ResultsAnalysisService
        """
        # Inicializuojame ResultsDataService duomenų prieigai
        self.data_service = ResultsDataService()
        
    # ============================
    # FILTRAVIMO FUNKCIJOS
    # ============================
    
    def filter_by_date_range(self, predictions, start_date, end_date):
        """
        Filtruoja prognozes pagal datų intervalą
        
        Args:
            predictions (list): Prognozių sąrašas
            start_date (datetime): Pradžios data
            end_date (datetime): Pabaigos data
            
        Returns:
            list: Filtruotos prognozės
        """
        # Konvertuojame string datas į datetime objektus, jei reikia
        if isinstance(start_date, str):
            start_date = datetime.fromisoformat(start_date)
        if isinstance(end_date, str):
            end_date = datetime.fromisoformat(end_date)
            
        # Filtruojame pagal target_date (prognozuojamą datą)
        filtered_predictions = []
        for pred in predictions:
            # Konvertuojame string datą į datetime, jei reikia
            pred_date = pred.get('target_date')
            if isinstance(pred_date, str):
                pred_date = datetime.fromisoformat(pred_date)
                
            # Tikriname, ar data patenka į intervalą
            if start_date <= pred_date <= end_date:
                filtered_predictions.append(pred)
                
        return filtered_predictions
    
    def filter_by_accuracy(self, predictions, min_accuracy=None, max_accuracy=None):
        """
        Filtruoja prognozes pagal tikslumą
        
        Args:
            predictions (list): Prognozių sąrašas
            min_accuracy (float): Minimalus tikslumas (procentais)
            max_accuracy (float): Maksimalus tikslumas (procentais)
            
        Returns:
            list: Filtruotos prognozės
        """
        # Jei nepateikti abu parametrai, grąžiname visas prognozes
        if min_accuracy is None and max_accuracy is None:
            return predictions
            
        filtered_predictions = []
        for pred in predictions:
            # Tikriname, ar yra faktinė vertė
            if pred.get('actual_value') is None:
                continue
                
            # Skaičiuojame tikslumą (paklaida procentais)
            predicted = pred.get('predicted_value')
            actual = pred.get('actual_value')
            error_percent = abs((predicted - actual) / actual * 100)
            accuracy = 100 - error_percent
            
            # Tikriname, ar tikslumas atitinka kriterijus
            meets_criteria = True
            if min_accuracy is not None and accuracy < min_accuracy:
                meets_criteria = False
            if max_accuracy is not None and accuracy > max_accuracy:
                meets_criteria = False
                
            if meets_criteria:
                filtered_predictions.append(pred)
                
        return filtered_predictions
    
    def filter_by_confidence(self, predictions, min_confidence=0.0):
        """
        Filtruoja prognozes pagal pasitikėjimo lygį
        
        Args:
            predictions (list): Prognozių sąrašas
            min_confidence (float): Minimalus pasitikėjimo lygis (0-1)
            
        Returns:
            list: Filtruotos prognozės
        """
        # Filtruojame prognozes, kurių confidence >= min_confidence
        return [p for p in predictions if p.get('confidence', 0) >= min_confidence]
    
    def filter_simulations_by_performance(self, simulations, min_roi=None, max_drawdown=None):
        """
        Filtruoja simuliacijas pagal našumo rodiklius
        
        Args:
            simulations (list): Simuliacijų sąrašas
            min_roi (float): Minimalus ROI (procentais)
            max_drawdown (float): Maksimalus nuosmukis (procentais)
            
        Returns:
            list: Filtruotos simuliacijos
        """
        filtered_simulations = []
        for sim in simulations:
            # Tikriname ROI, jei nustatytas min_roi
            if min_roi is not None:
                if sim.get('roi') is None or sim.get('roi') < min_roi:
                    continue
                    
            # Tikriname nuosmukį, jei nustatytas max_drawdown
            if max_drawdown is not None:
                if sim.get('max_drawdown') is None or sim.get('max_drawdown') > max_drawdown:
                    continue
                    
            # Jei atitiko visus kriterijus, pridedame į sąrašą
            filtered_simulations.append(sim)
            
        return filtered_simulations
    
    # ============================
    # GRUPAVIMO IR AGREGAVIMO FUNKCIJOS
    # ============================
    
    def group_models_by_accuracy(self, days=30):
        """
        Grupuoja modelius pagal tikslumą
        
        Args:
            days (int): Dienų skaičius atgal
            
        Returns:
            dict: Modeliai sugrupuoti pagal tikslumą
        """
        # Gauname visų modelių tikslumą
        accuracy_metrics = self.data_service.get_prediction_accuracy(days=days)
        
        # Grupuojame modelius pagal tikslumą
        accuracy_groups = {
            'high': [],    # Aukštas tikslumas (>90%)
            'medium': [],  # Vidutinis tikslumas (70-90%)
            'low': []      # Žemas tikslumas (<70%)
        }
        
        for metric in accuracy_metrics:
            accuracy = metric.get('accuracy')
            if accuracy is None:
                continue
                
            if accuracy > 90:
                accuracy_groups['high'].append(metric)
            elif accuracy > 70:
                accuracy_groups['medium'].append(metric)
            else:
                accuracy_groups['low'].append(metric)
                
        return accuracy_groups
    
    def group_simulations_by_strategy(self, simulations):
        """
        Grupuoja simuliacijas pagal strategijos tipą
        
        Args:
            simulations (list): Simuliacijų sąrašas
            
        Returns:
            dict: Simuliacijos sugrupuotos pagal strategijos tipą
        """
        # Inicializuojame grupių žodyną
        strategy_groups = {}
        
        # Grupuojame simuliacijas
        for sim in simulations:
            strategy_type = sim.get('strategy_type')
            
            # Jei dar nėra tokios grupės, sukuriame ją
            if strategy_type not in strategy_groups:
                strategy_groups[strategy_type] = []
                
            # Pridedame simuliaciją į grupę
            strategy_groups[strategy_type].append(sim)
            
        return strategy_groups
    
    def aggregate_predictions_by_time(self, predictions, interval='day'):
        """
        Agreguoja prognozes pagal laiko intervalą
        
        Args:
            predictions (list): Prognozių sąrašas
            interval (str): Agregavimo intervalas ('day', 'week', 'month')
            
        Returns:
            dict: Agreguotos prognozės
        """
        # Inicializuojame agreguotų prognozių žodyną
        aggregated = {}
        
        for pred in predictions:
            # Gauname datą ir konvertuojame į string pagal intervalą
            pred_date = pred.get('target_date')
            if isinstance(pred_date, str):
                pred_date = datetime.fromisoformat(pred_date)
                
            # Formatuojame datą pagal pasirinktą intervalą
            if interval == 'day':
                date_key = pred_date.strftime('%Y-%m-%d')
            elif interval == 'week':
                # Savaitės numeris (ISO)
                date_key = f"{pred_date.year}-W{pred_date.isocalendar()[1]}"
            elif interval == 'month':
                date_key = pred_date.strftime('%Y-%m')
            else:
                # Jei netinkamas intervalas, naudojame dieną
                date_key = pred_date.strftime('%Y-%m-%d')
                
            # Jei dar nėra tokio intervalo, sukuriame jį
            if date_key not in aggregated:
                aggregated[date_key] = {
                    'count': 0,
                    'sum_predicted': 0,
                    'sum_actual': 0,
                    'predictions': []
                }
                
            # Pridedame prognozės duomenis į agregavimą
            aggregated[date_key]['count'] += 1
            aggregated[date_key]['sum_predicted'] += pred.get('predicted_value', 0)
            if pred.get('actual_value') is not None:
                aggregated[date_key]['sum_actual'] += pred.get('actual_value', 0)
            aggregated[date_key]['predictions'].append(pred)
        
        # Skaičiuojame vidurkius kiekvienam intervalui
        for date_key in aggregated:
            count = aggregated[date_key]['count']
            if count > 0:
                aggregated[date_key]['avg_predicted'] = aggregated[date_key]['sum_predicted'] / count
                if aggregated[date_key]['sum_actual'] > 0:
                    aggregated[date_key]['avg_actual'] = aggregated[date_key]['sum_actual'] / count
                
        return aggregated
    
    def calculate_statistics(self, data_list, field_name):
        """
        Skaičiuoja statistinius rodiklius duomenų sąrašui
        
        Args:
            data_list (list): Duomenų sąrašas
            field_name (str): Lauko pavadinimas, kuriam skaičiuoti statistiką
            
        Returns:
            dict: Statistiniai rodikliai
        """
        # Ištraukiame reikšmes iš sąrašo
        values = [item.get(field_name) for item in data_list if item.get(field_name) is not None]
        
        # Jei nėra reikšmių, grąžiname tuščią statistiką
        if not values:
            return {
                'count': 0,
                'min': None,
                'max': None,
                'mean': None,
                'median': None,
                'std': None
            }
            
        # Skaičiuojame statistinius rodiklius
        return {
            'count': len(values),
            'min': min(values),
            'max': max(values),
            'mean': sum(values) / len(values),
            'median': sorted(values)[len(values) // 2],
            'std': np.std(values) if len(values) > 1 else 0
        }
    
    # ============================
    # DUOMENŲ KONVERTAVIMO FUNKCIJOS
    # ============================
    
    def to_dataframe(self, data_list):
        """
        Konvertuoja duomenų sąrašą į pandas DataFrame
        
        Args:
            data_list (list): Duomenų sąrašas
            
        Returns:
            pandas.DataFrame: DataFrame objektas
        """
        # Jei sąrašas tuščias, grąžiname tuščią DataFrame
        if not data_list:
            return pd.DataFrame()
            
        # Konvertuojame sąrašą į DataFrame
        return pd.DataFrame(data_list)
    
    def to_visualization_json(self, data, chart_type='line'):
        """
        Konvertuoja duomenis į JSON formatą, tinkamą vizualizacijai
        
        Args:
            data: Duomenys (gali būti sąrašas, žodynas arba DataFrame)
            chart_type (str): Grafiko tipas ('line', 'bar', 'scatter', ir t.t.)
            
        Returns:
            str: JSON eilutė
        """
        # Jei duomenys yra DataFrame, konvertuojame į žodyną
        if isinstance(data, pd.DataFrame):
            data_dict = data.to_dict(orient='records')
        else:
            data_dict = data
            
        # Sukuriame vizualizacijos duomenų struktūrą
        visualization_data = {
            'chart_type': chart_type,
            'data': data_dict
        }
        
        # Konvertuojame į JSON
        return json.dumps(visualization_data)
    
    def export_to_csv(self, data, filename):
        """
        Eksportuoja duomenis į CSV failą
        
        Args:
            data: Duomenys (gali būti sąrašas arba DataFrame)
            filename (str): Failo pavadinimas
            
        Returns:
            bool: True jei sėkmingai, False jei nepavyko
        """
        try:
            # Konvertuojame į DataFrame, jei reikia
            if not isinstance(data, pd.DataFrame):
                df = pd.DataFrame(data)
            else:
                df = data
                
            # Eksportuojame į CSV
            df.to_csv(filename, index=False)
            return True
        except Exception as e:
            logger.error(f"Klaida eksportuojant į CSV: {str(e)}")
            return False
    
    # ============================
    # STATISTINĖS ANALIZĖS METODAI
    # ============================
    
    def compare_model_accuracy(self, model_ids, days=30):
        """
        Palygina modelių tikslumą
        
        Args:
            model_ids (list): Modelių ID sąrašas
            days (int): Dienų skaičius atgal
            
        Returns:
            dict: Modelių tikslumo palyginimas
        """
        # Inicializuojame rezultatų žodyną
        comparison = {}
        
        # Gauname kiekvieno modelio tikslumą
        for model_id in model_ids:
            accuracy_metrics = self.data_service.get_prediction_accuracy(model_id=model_id, days=days)
            
            # Jei yra metrikos, įtraukiame į palyginimą
            if accuracy_metrics:
                comparison[model_id] = accuracy_metrics[0]
            else:
                comparison[model_id] = {
                    'model_id': model_id,
                    'total_predictions': 0,
                    'accuracy': None,
                    'avg_error_percent': None
                }
                
        # Rūšiuojame modelius pagal tikslumą (jei yra)
        sorted_models = sorted(
            [model for model in comparison.values() if model['accuracy'] is not None],
            key=lambda x: x['accuracy'],
            reverse=True
        )
        
        return {
            'models': comparison,
            'sorted_models': sorted_models
        }
    
    def analyze_prediction_trends(self, model_id, days=90):
        """
        Analizuoja prognozių tendencijas
        
        Args:
            model_id (str): Modelio ID
            days (int): Dienų skaičius atgal
            
        Returns:
            dict: Tendencijų analizės rezultatai
        """
        # Gauname modelio prognozes
        predictions = self.data_service.get_model_predictions(model_id)
        
        # Filtruojame tik prognozes su faktinėmis vertėmis
        predictions_with_actual = [p for p in predictions if p.get('actual_value') is not None]
        
        # Jei nėra pakankamai duomenų, grąžiname tuščią analizę
        if len(predictions_with_actual) < 2:
            return {
                'model_id': model_id,
                'trend': 'unknown',
                'accuracy_trend': 'unknown',
                'data_points': len(predictions_with_actual)
            }
            
        # Konvertuojame į DataFrame analizei
        df = pd.DataFrame(predictions_with_actual)
        
        # Konvertuojame datas į datetime
        for date_col in ['prediction_date', 'target_date']:
            if date_col in df.columns:
                df[date_col] = pd.to_datetime(df[date_col])
                
        # Rūšiuojame pagal datą
        df = df.sort_values('target_date')
        
        # Skaičiuojame klaidos procentą
        df['error_percent'] = abs((df['predicted_value'] - df['actual_value']) / df['actual_value'] * 100)
        df['accuracy'] = 100 - df['error_percent']
        
        # Skaičiuojame slankųjį vidurkį tikslumo tendencijai nustatyti
        if len(df) >= 5:
            df['accuracy_ma'] = df['accuracy'].rolling(window=5).mean()
            
            # Nustatome tikslumo tendenciją
            first_valid_ma = df['accuracy_ma'].dropna().iloc[0]
            last_valid_ma = df['accuracy_ma'].dropna().iloc[-1]
            
            if last_valid_ma > first_valid_ma * 1.05:  # 5% pagerėjimas
                accuracy_trend = 'improving'
            elif last_valid_ma < first_valid_ma * 0.95:  # 5% pablogėjimas
                accuracy_trend = 'declining'
            else:
                accuracy_trend = 'stable'
        else:
            accuracy_trend = 'insufficient_data'
            
        # Analizuojame prognozes
        first_predicted = df['predicted_value'].iloc[0]
        last_predicted = df['predicted_value'].iloc[-1]
        
        if last_predicted > first_predicted * 1.05:  # 5% augimas
            price_trend = 'rising'
        elif last_predicted < first_predicted * 0.95:  # 5% kritimas
            price_trend = 'falling'
        else:
            price_trend = 'stable'
            
        return {
            'model_id': model_id,
            'price_trend': price_trend,
            'accuracy_trend': accuracy_trend,
            'avg_accuracy': df['accuracy'].mean(),
            'first_date': df['target_date'].iloc[0].isoformat(),
            'last_date': df['target_date'].iloc[-1].isoformat(),
            'data_points': len(df)
        }
    
    # ============================
    # VIZUALIZACIJOS PAGALBINĖS FUNKCIJOS
    # ============================
    
    def prepare_prediction_chart_data(self, model_id, limit=100):
        """
        Paruošia prognozių grafiko duomenis
        
        Args:
            model_id (str): Modelio ID
            limit (int): Maksimalus taškų skaičius
            
        Returns:
            dict: Grafiko duomenys
        """
        # Gauname modelio prognozes
        predictions = self.data_service.get_model_predictions(model_id, limit)
        
        # Inicializuojame duomenų masyvus
        dates = []
        predicted_values = []
        actual_values = []
        
        # Užpildome duomenų masyvus
        for pred in predictions:
            # Konvertuojame datą į tinkamą formatą
            target_date = pred.get('target_date')
            if isinstance(target_date, str):
                target_date = datetime.fromisoformat(target_date)
                
            # Pridedame datą ir reikšmes
            dates.append(target_date.strftime('%Y-%m-%d'))
            predicted_values.append(pred.get('predicted_value'))
            actual_values.append(pred.get('actual_value'))
                
        # Formuojame grafiko duomenis
        return {
            'model_id': model_id,
            'labels': dates,
            'datasets': [
                {
                    'label': 'Prognozuojamos vertės',
                    'data': predicted_values,
                    'borderColor': 'rgba(54, 162, 235, 1)',
                    'backgroundColor': 'rgba(54, 162, 235, 0.2)'
                },
                {
                    'label': 'Faktinės vertės',
                    'data': actual_values,
                    'borderColor': 'rgba(255, 99, 132, 1)',
                    'backgroundColor': 'rgba(255, 99, 132, 0.2)'
                }
            ]
        }
    
    def prepare_trading_chart_data(self, simulation_id):
        """
        Paruošia prekybos rezultatų grafiko duomenis
        
        Args:
            simulation_id (str): Simuliacijos ID
            
        Returns:
            dict: Grafiko duomenys
        """
        # Gauname simuliacijos duomenis
        simulation = self.data_service.get_simulation(simulation_id)
        
        # Jei simuliacija nerasta, grąžiname tuščius duomenis
        if not simulation:
            return {
                'simulation_id': simulation_id,
                'error': 'Simuliacija nerasta'
            }
            
        # Gauname simuliacijos sandorius
        trades = self.data_service.get_simulation_trades(simulation_id)
        
        # Inicializuojame duomenų masyvus
        dates = []
        balances = []
        buy_points = []
        sell_points = []
        
        # Pradinis balansas
        current_balance = simulation.get('initial_capital', 0)
        balances.append(current_balance)
        
        # Pridedame pradžios datą
        start_date = simulation.get('start_date')
        if isinstance(start_date, str):
            start_date = datetime.fromisoformat(start_date)
        dates.append(start_date.strftime('%Y-%m-%d'))
        
        # Rūšiuojame sandorius pagal datą
        sorted_trades = sorted(trades, key=lambda x: x.get('date', ''))
        
        # Užpildome duomenų masyvus
        for trade in sorted_trades:
            # Pridedame sandorio datą
            trade_date = trade.get('date')
            if isinstance(trade_date, str):
                trade_date = datetime.fromisoformat(trade_date)
            dates.append(trade_date.strftime('%Y-%m-%d'))
            
            # Atnaujiname balansą
            if trade.get('type') == 'buy':
                # Pirkimo atveju balansas sumažėja
                current_balance -= trade.get('value', 0)
                buy_points.append(current_balance)
                sell_points.append(None)
            else:
                # Pardavimo atveju balansas padidėja
                current_balance += trade.get('value', 0)
                if trade.get('profit_loss') is not None:
                    current_balance += trade.get('profit_loss', 0)
                sell_points.append(current_balance)
                buy_points.append(None)
                
            balances.append(current_balance)
            
        # Formuojame grafiko duomenis
        return {
            'simulation_id': simulation_id,
            'simulation_name': simulation.get('name', 'Nenurodyta'),
            'labels': dates,
            'datasets': [
                {
                    'label': 'Balansas',
                    'data': balances,
                    'borderColor': 'rgba(75, 192, 192, 1)',
                    'backgroundColor': 'rgba(75, 192, 192, 0.2)',
                    'fill': True
                },
                {
                    'label': 'Pirkimai',
                    'data': buy_points,
                    'pointRadius': 5,
                    'pointBackgroundColor': 'rgba(54, 162, 235, 1)'
                },
                {
                    'label': 'Pardavimai',
                    'data': sell_points,
                    'pointRadius': 5,
                    'pointBackgroundColor': 'rgba(255, 99, 132, 1)'
                }
            ]
        }