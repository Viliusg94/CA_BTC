import sqlite3
import os
import sys

# Add the parent directory to Python path to fix import issues
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

db_path = os.path.join('data', 'models.db')
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print('Tables in database:', tables)
    if tables:
        for table in tables:
            print(f'\nTable: {table[0]}')
            cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
            count = cursor.fetchone()[0]
            print(f'  Records: {count}')
            if count > 0:
                cursor.execute(f"SELECT * FROM {table[0]} LIMIT 3")
                rows = cursor.fetchall()
                print(f'  Sample records: {rows}')
    conn.close()
else:
    print('Database file not found at:', db_path)
