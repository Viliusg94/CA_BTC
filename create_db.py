import sqlite3
import os

def create_models_database():
    db_path = os.path.join(os.path.dirname(__file__), 'models.db')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS models (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_type TEXT NOT NULL,
            r2 REAL,
            mae REAL,
            rmse REAL,
            epochs INTEGER,
            timestamp TEXT,
            is_active BOOLEAN DEFAULT 0,
            file_path TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"Database created at: {db_path}")

if __name__ == "__main__":
    create_models_database()
