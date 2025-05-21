"""
SQLite duomenų bazės taisymo įrankiai.
Naudoja tiesiogines SQL užklausas, kad apeiti SQLAlchemy problemas.
"""
import sqlite3
import os
import logging

# Žurnalo konfigūracija
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Duomenų bazės failo lokacija
DB_FILE = "ca_btc.db"
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), DB_FILE)

def create_tables_directly():
    """
    Sukuria duomenų bazės lenteles naudojant tiesiogines SQL užklausas.
    Tai apeis SQLAlchemy užsienio raktų problemą.
    """
    logger.info(f"Bandoma sukurti duomenų bazės lenteles tiesiogiai: {DB_PATH}")
    
    # Tikriname, ar duomenų bazės failas jau egzistuoja
    if os.path.exists(DB_PATH):
        logger.info("Duomenų bazės failas jau egzistuoja. Naikinamas...")
        os.remove(DB_PATH)
    
    # Sukuriame ryšį su SQLite duomenų baze
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Įjungiame užsienio raktų palaikymą
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    try:
        # 1. Sukuriame users lentelę
        logger.info("Kuriama users lentelė...")
        cursor.execute('''
        CREATE TABLE users (
            id VARCHAR(36) PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(128) NOT NULL,
            full_name VARCHAR(100),
            is_active BOOLEAN DEFAULT 1,
            is_admin BOOLEAN DEFAULT 0,
            last_login TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        ''')
        
        # 2. Sukuriame user_sessions lentelę
        logger.info("Kuriama user_sessions lentelė...")
        cursor.execute('''
        CREATE TABLE user_sessions (
            id VARCHAR(36) PRIMARY KEY,
            user_id VARCHAR(36) NOT NULL,
            session_token VARCHAR(255) NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ip_address VARCHAR(45),
            user_agent VARCHAR(255),
            is_active BOOLEAN DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        ''')
        
        # 3. Sukuriame models lentelę
        logger.info("Kuriama models lentelė...")
        cursor.execute('''
        CREATE TABLE models (
            id VARCHAR(36) PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            type VARCHAR(50) NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            creator_id VARCHAR(36),
            is_active BOOLEAN DEFAULT 1,
            trained BOOLEAN DEFAULT 0,
            hyperparameters TEXT,
            file_path VARCHAR(255),
            FOREIGN KEY (creator_id) REFERENCES users(id) ON DELETE SET NULL
        );
        ''')
        
        # 4. Sukuriame metrics lenteles
        logger.info("Kuriama user_metrics lentelė...")
        cursor.execute('''
        CREATE TABLE user_metrics (
            id VARCHAR(36) PRIMARY KEY,
            user_id VARCHAR(36) NOT NULL,
            metric_type VARCHAR(50) NOT NULL,
            metric_name VARCHAR(100) NOT NULL,
            numeric_value FLOAT,
            string_value VARCHAR(255),
            time_period VARCHAR(20),
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metric_metadata JSON,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        ''')
        
        logger.info("Kuriama model_metrics lentelė...")
        cursor.execute('''
        CREATE TABLE model_metrics (
            id VARCHAR(36) PRIMARY KEY,
            model_id VARCHAR(36) NOT NULL,
            metric_type VARCHAR(50) NOT NULL,
            metric_name VARCHAR(100) NOT NULL,
            numeric_value FLOAT,
            string_value VARCHAR(255),
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metric_metadata JSON,
            FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE CASCADE
        );
        ''')
        
        logger.info("Kuriama session_metrics lentelė...")
        cursor.execute('''
        CREATE TABLE session_metrics (
            id VARCHAR(36) PRIMARY KEY,
            session_id VARCHAR(36) NOT NULL,
            metric_type VARCHAR(50) NOT NULL,
            metric_name VARCHAR(100) NOT NULL,
            numeric_value FLOAT,
            string_value VARCHAR(255),
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metric_metadata JSON,
            FOREIGN KEY (session_id) REFERENCES user_sessions(id) ON DELETE CASCADE
        );
        ''')
        
        # 5. Sukuriame experiments lenteles
        logger.info("Kuriama experiments lentelė...")
        cursor.execute('''
        CREATE TABLE experiments (
            id VARCHAR(36) PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            model_id VARCHAR(36),
            creator_id VARCHAR(36),
            start_time TIMESTAMP,
            end_time TIMESTAMP,
            status VARCHAR(20) DEFAULT 'created',
            parameters TEXT,
            experiment_metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE SET NULL,
            FOREIGN KEY (creator_id) REFERENCES users(id) ON DELETE SET NULL
        );
        ''')
        
        logger.info("Kuriama experiment_results lentelė...")
        cursor.execute('''
        CREATE TABLE experiment_results (
            id VARCHAR(36) PRIMARY KEY,
            experiment_id VARCHAR(36) NOT NULL,
            metric_name VARCHAR(100) NOT NULL,
            metric_value FLOAT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            result_metadata TEXT,
            FOREIGN KEY (experiment_id) REFERENCES experiments(id) ON DELETE CASCADE
        );
        ''')
        
        # Fiksuojame pakeitimus
        conn.commit()
        logger.info("Visos lentelės sukurtos sėkmingai")
        return True
        
    except Exception as e:
        # Atšaukiame transakciją, jei įvyko klaida
        conn.rollback()
        logger.error(f"Klaida kuriant lenteles: {e}")
        return False
        
    finally:
        # Uždarome ryšį
        conn.close()

if __name__ == "__main__":
    create_tables_directly()