import os
import sqlite3
import uuid
from datetime import datetime
import json

class PredictionResult:
    """
    Prognozių rezultatų lentelė - saugo modelio prognozes
    """
    def __init__(self, db_path):
        """
        Inicializuoja PredictionResult klasę
        
        Args:
            db_path (str): Kelias iki duomenų bazės failo
        """
        # Išsaugome duomenų bazės kelią
        self.db_path = db_path
        
        # Sukuriame lentelę, jei ji neegzistuoja
        self._create_table()
    
    def _create_table(self):
        """
        Sukuria predictions lentelę, jei ji neegzistuoja
        """
        # Prisijungiame prie duomenų bazės
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Sukuriame lentelę
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS predictions (
            id TEXT PRIMARY KEY,
            model_id TEXT NOT NULL,
            prediction_date TEXT NOT NULL,
            target_date TEXT NOT NULL,
            predicted_value REAL NOT NULL,
            actual_value REAL,
            interval TEXT NOT NULL,
            confidence REAL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (model_id) REFERENCES models (id)
        )
        ''')
        
        # Sukuriame indeksą pagreitinti paieškai pagal modelį
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_predictions_model_id ON predictions (model_id)
        ''')
        
        # Išsaugome pakeitimus ir uždarome prisijungimą
        conn.commit()
        conn.close()
    
    def save_prediction(self, prediction_data):
        """
        Išsaugo prognozės rezultatą duomenų bazėje
        
        Args:
            prediction_data (dict): Prognozės duomenys
            
        Returns:
            str: Prognozės ID
        """
        # Generuojame unikalų ID
        prediction_id = str(uuid.uuid4())
        
        # Prisijungiame prie duomenų bazės
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Įterpiame naują įrašą
            cursor.execute('''
            INSERT INTO predictions (
                id, model_id, prediction_date, target_date, 
                predicted_value, actual_value, interval, confidence, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                prediction_id,
                prediction_data.get('model_id'),
                prediction_data.get('prediction_date', datetime.now().isoformat()),
                prediction_data.get('target_date'),
                prediction_data.get('predicted_value'),
                prediction_data.get('actual_value'),
                prediction_data.get('interval', '1d'),
                prediction_data.get('confidence'),
                datetime.now().isoformat()
            ))
            
            # Išsaugome pakeitimus
            conn.commit()
            
            return prediction_id
        
        except Exception as e:
            # Atšaukiame pakeitimus klaidos atveju
            conn.rollback()
            print(f"Klaida išsaugant prognozę: {str(e)}")
            return None
        
        finally:
            # Uždarome prisijungimą
            conn.close()
    
    def get_model_predictions(self, model_id, limit=100):
        """
        Gauna modelio prognozes
        
        Args:
            model_id (str): Modelio ID
            limit (int): Maksimalus įrašų skaičius
            
        Returns:
            list: Prognozių sąrašas
        """
        # Prisijungiame prie duomenų bazės
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Kad rezultatai būtų grąžinami kaip žodynai
        cursor = conn.cursor()
        
        try:
            # Gauname prognozes
            cursor.execute('''
            SELECT * FROM predictions 
            WHERE model_id = ? 
            ORDER BY prediction_date DESC 
            LIMIT ?
            ''', (model_id, limit))
            
            # Grąžiname prognozes kaip žodynus
            predictions = [dict(row) for row in cursor.fetchall()]
            
            return predictions
        
        except Exception as e:
            print(f"Klaida gaunant prognozes: {str(e)}")
            return []
        
        finally:
            # Uždarome prisijungimą
            conn.close()


class SimulationResult:
    """
    Simuliacijų rezultatų lentelė - saugo prekybos strategijų simuliacijas
    """
    def __init__(self, db_path):
        """
        Inicializuoja SimulationResult klasę
        
        Args:
            db_path (str): Kelias iki duomenų bazės failo
        """
        # Išsaugome duomenų bazės kelią
        self.db_path = db_path
        
        # Sukuriame lenteles, jei jos neegzistuoja
        self._create_tables()
    
    def _create_tables(self):
        """
        Sukuria simulations ir trades lenteles, jei jos neegzistuoja
        """
        # Prisijungiame prie duomenų bazės
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Sukuriame simuliacijų lentelę
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS simulations (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            initial_capital REAL NOT NULL,
            fees REAL NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            strategy_type TEXT NOT NULL,
            strategy_params TEXT,
            final_balance REAL,
            profit_loss REAL,
            roi REAL,
            max_drawdown REAL,
            total_trades INTEGER DEFAULT 0,
            winning_trades INTEGER DEFAULT 0,
            losing_trades INTEGER DEFAULT 0,
            is_completed INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        ''')
        
        # Sukuriame sandorių lentelę
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS trades (
            id TEXT PRIMARY KEY,
            simulation_id TEXT NOT NULL,
            date TEXT NOT NULL,
            type TEXT NOT NULL,
            price REAL NOT NULL,
            amount REAL NOT NULL,
            value REAL NOT NULL,
            fee REAL NOT NULL,
            profit_loss REAL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (simulation_id) REFERENCES simulations (id)
        )
        ''')
        
        # Sukuriame indeksą pagreitinti paieškai pagal simuliaciją
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_trades_simulation_id ON trades (simulation_id)
        ''')
        
        # Išsaugome pakeitimus ir uždarome prisijungimą
        conn.commit()
        conn.close()
    
    def save_simulation(self, simulation_data):
        """
        Išsaugo simuliacijos rezultatą duomenų bazėje
        
        Args:
            simulation_data (dict): Simuliacijos duomenys
            
        Returns:
            str: Simuliacijos ID
        """
        # Generuojame unikalų ID
        simulation_id = str(uuid.uuid4())
        
        # Prisijungiame prie duomenų bazės
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Įterpiame naują įrašą
            now = datetime.now().isoformat()
            
            # Konvertuojame strategy_params į JSON, jei reikia
            strategy_params = simulation_data.get('strategy_params')
            if strategy_params and isinstance(strategy_params, dict):
                strategy_params = json.dumps(strategy_params)
            
            cursor.execute('''
            INSERT INTO simulations (
                id, name, initial_capital, fees, start_date, end_date,
                strategy_type, strategy_params, is_completed, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                simulation_id,
                simulation_data.get('name', 'Nenurodyta'),
                simulation_data.get('initial_capital', 1000.0),
                simulation_data.get('fees', 0.001),
                simulation_data.get('start_date'),
                simulation_data.get('end_date'),
                simulation_data.get('strategy_type', 'custom'),
                strategy_params,
                simulation_data.get('is_completed', 0),  # 0 = False, 1 = True
                now,
                now
            ))
            
            # Išsaugome pakeitimus
            conn.commit()
            
            return simulation_id
        
        except Exception as e:
            # Atšaukiame pakeitimus klaidos atveju
            conn.rollback()
            print(f"Klaida išsaugant simuliaciją: {str(e)}")
            return None
        
        finally:
            # Uždarome prisijungimą
            conn.close()
    
    def save_trade(self, trade_data):
        """
        Išsaugo prekybos sandorį duomenų bazėje
        
        Args:
            trade_data (dict): Sandorio duomenys
            
        Returns:
            str: Sandorio ID
        """
        # Generuojame unikalų ID
        trade_id = str(uuid.uuid4())
        
        # Prisijungiame prie duomenų bazės
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Įterpiame naują įrašą
            cursor.execute('''
            INSERT INTO trades (
                id, simulation_id, date, type, price, amount, value, fee, profit_loss, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                trade_id,
                trade_data.get('simulation_id'),
                trade_data.get('date'),
                trade_data.get('type'),  # 'buy' arba 'sell'
                trade_data.get('price'),
                trade_data.get('amount'),
                trade_data.get('value'),
                trade_data.get('fee'),
                trade_data.get('profit_loss'),
                datetime.now().isoformat()
            ))
            
            # Atnaujiname simuliacijos sandorių skaičių
            if trade_data.get('type') == 'buy' or trade_data.get('type') == 'sell':
                cursor.execute('''
                UPDATE simulations SET total_trades = total_trades + 1 WHERE id = ?
                ''', (trade_data.get('simulation_id'),))
                
                # Jei tai pardavimo sandoris ir turime pelno/nuostolio informaciją
                if trade_data.get('type') == 'sell' and trade_data.get('profit_loss') is not None:
                    if trade_data.get('profit_loss') > 0:
                        cursor.execute('''
                        UPDATE simulations SET winning_trades = winning_trades + 1 WHERE id = ?
                        ''', (trade_data.get('simulation_id'),))
                    else:
                        cursor.execute('''
                        UPDATE simulations SET losing_trades = losing_trades + 1 WHERE id = ?
                        ''', (trade_data.get('simulation_id'),))
            
            # Išsaugome pakeitimus
            conn.commit()
            
            return trade_id
        
        except Exception as e:
            # Atšaukiame pakeitimus klaidos atveju
            conn.rollback()
            print(f"Klaida išsaugant sandorį: {str(e)}")
            return None
        
        finally:
            # Uždarome prisijungimą
            conn.close()


class MetricResult:
    """
    Metrikų lentelė - saugo įvairias modelių ir simuliacijų metrikas
    """
    def __init__(self, db_path):
        """
        Inicializuoja MetricResult klasę
        
        Args:
            db_path (str): Kelias iki duomenų bazės failo
        """
        # Išsaugome duomenų bazės kelią
        self.db_path = db_path
        
        # Sukuriame lentelę, jei ji neegzistuoja
        self._create_table()
    
    def _create_table(self):
        """
        Sukuria metrics lentelę, jei ji neegzistuoja
        """
        # Prisijungiame prie duomenų bazės
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Sukuriame lentelę
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS metrics (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            value REAL NOT NULL,
            model_id TEXT,
            simulation_id TEXT,
            period TEXT,
            date TEXT NOT NULL,
            description TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (model_id) REFERENCES models (id),
            FOREIGN KEY (simulation_id) REFERENCES simulations (id)
        )
        ''')
        
        # Sukuriame indeksus pagreitinti paieškai
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_metrics_model_id ON metrics (model_id)
        ''')
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_metrics_simulation_id ON metrics (simulation_id)
        ''')
        
        # Išsaugome pakeitimus ir uždarome prisijungimą
        conn.commit()
        conn.close()
    
    def save_metric(self, metric_data):
        """
        Išsaugo metriką duomenų bazėje
        
        Args:
            metric_data (dict): Metrikos duomenys
            
        Returns:
            str: Metrikos ID
        """
        # Generuojame unikalų ID
        metric_id = str(uuid.uuid4())
        
        # Prisijungiame prie duomenų bazės
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Įterpiame naują įrašą
            cursor.execute('''
            INSERT INTO metrics (
                id, name, value, model_id, simulation_id, period, date, description, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                metric_id,
                metric_data.get('name'),
                metric_data.get('value'),
                metric_data.get('model_id'),
                metric_data.get('simulation_id'),
                metric_data.get('period'),
                metric_data.get('date', datetime.now().isoformat()),
                metric_data.get('description'),
                datetime.now().isoformat()
            ))
            
            # Išsaugome pakeitimus
            conn.commit()
            
            return metric_id
        
        except Exception as e:
            # Atšaukiame pakeitimus klaidos atveju
            conn.rollback()
            print(f"Klaida išsaugant metriką: {str(e)}")
            return None
        
        finally:
            # Uždarome prisijungimą
            conn.close()