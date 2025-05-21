import os
import sqlite3
import logging

# Importuojame modelius
from app.models.results import PredictionResult, SimulationResult, MetricResult

# Nustatome kelią iki duomenų bazės failo
DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'results.db')
DB_DIR = os.path.dirname(DB_PATH)

# Rezultatų lentelių objektai
prediction_result = None
simulation_result = None
metric_result = None

def init_db():
    """
    Inicializuoja duomenų bazę - sukuria lenteles, jei jų nėra
    """
    global prediction_result, simulation_result, metric_result
    
    try:
        # Sukuriame duomenų katalogą, jei jo nėra
        if not os.path.exists(DB_DIR):
            os.makedirs(DB_DIR)
        
        # Sukuriame rezultatų lentelių objektus
        prediction_result = PredictionResult(DB_PATH)
        simulation_result = SimulationResult(DB_PATH)
        metric_result = MetricResult(DB_PATH)
        
        # Sukuriame models lentelę, jei jos nėra (kad veiktų foreign key ryšiai)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Sukuriame models lentelę
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS models (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            description TEXT,
            parameters TEXT,
            file_path TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        ''')
        
        # Uždarome prisijungimą
        conn.commit()
        conn.close()
        
        logging.info(f"Duomenų bazė inicializuota: {DB_PATH}")
        
    except Exception as e:
        logging.error(f"Klaida inicializuojant duomenų bazę: {str(e)}")

# Gauti rezultatų objektus
def get_prediction_result():
    """
    Grąžina PredictionResult objektą darbui su prognozėmis
    """
    global prediction_result
    if prediction_result is None:
        init_db()
    return prediction_result

def get_simulation_result():
    """
    Grąžina SimulationResult objektą darbui su simuliacijomis
    """
    global simulation_result
    if simulation_result is None:
        init_db()
    return simulation_result

def get_metric_result():
    """
    Grąžina MetricResult objektą darbui su metrikomis
    """
    global metric_result
    if metric_result is None:
        init_db()
    return metric_result