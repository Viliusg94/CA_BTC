import sys
import os
from sqlalchemy import create_engine, inspect

# Pridedame projekto katalogą į Python kelią
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SQLALCHEMY_DATABASE_URL

def inspect_database():
    """
    Patikrina duomenų bazės schemą ir parodo visas lenteles bei jų stulpelius
    """
    print("Tikrinama duomenų bazės schema...")
    
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    inspector = inspect(engine)
    
    # Gauname visų lentelių sąrašą
    tables = inspector.get_table_names()
    
    if not tables:
        print("Duomenų bazėje nėra lentelių.")
        return
    
    print(f"Lentelių skaičius: {len(tables)}")
    
    # Einame per visas lenteles ir parodome jų struktūrą
    for table in tables:
        print(f"\nLentelė: {table}")
        
        # Gauname visus stulpelius
        columns = inspector.get_columns(table)
        print(f"  Stulpelių skaičius: {len(columns)}")
        
        # Rodome informaciją apie kiekvieną stulpelį
        for column in columns:
            nullable = "NULL" if column['nullable'] else "NOT NULL"
            default = f"DEFAULT {column['default']}" if column['default'] is not None else ""
            print(f"    {column['name']} {column['type']} {nullable} {default}")
        
        # Gauname visus indeksus
        indices = inspector.get_indexes(table)
        if indices:
            print(f"  Indeksų skaičius: {len(indices)}")
            for index in indices:
                unique = "UNIQUE" if index['unique'] else ""
                columns_str = ', '.join(index['column_names'])
                print(f"    {index['name']} {unique} ({columns_str})")
        
        # Gauname visus foreign keys
        fks = inspector.get_foreign_keys(table)
        if fks:
            print(f"  Foreign keys skaičius: {len(fks)}")
            for fk in fks:
                columns_str = ', '.join(fk['constrained_columns'])
                referred_columns_str = ', '.join(fk['referred_columns'])
                print(f"    {fk.get('name', 'Unnamed')} {columns_str} -> {fk['referred_table']}.{referred_columns_str}")

if __name__ == "__main__":
    inspect_database()