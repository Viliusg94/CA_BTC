# SUKURTI FAILĄ: d:\CA_BTC\database\db_init.py
"""
Šis modulis patikrina, ar visi reikalingi moduliai yra importuojami teisingai,
ir atnaujina duomenų bazės lentelių schemas.
"""
import sys
import os
import importlib
from sqlalchemy import inspect

# Pridedame projekto katalogą į Python kelią
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def validate_imports():
    """
    Patikrina visus reikalingus importus
    """
    print("Tikrinami modulių importai...")
    
    imports = [
        "sqlalchemy",
        "sqlalchemy.orm",
        "sqlalchemy.ext.declarative",
        "datetime",
        "uuid",
        "json",
        "logging",
    ]
    
    for module_name in imports:
        try:
            importlib.import_module(module_name)
            print(f"✓ Modulis {module_name} sėkmingai importuotas")
        except ImportError as e:
            print(f"✗ Klaida importuojant modulį {module_name}: {str(e)}")
            return False
    
    print("Visi pagrindiniai moduliai sėkmingai importuoti")
    
    # Tikriname projekto modulius
    project_modules = [
        "database.db_utils",
        "database.models.models",
        "database.models.results_models",
    ]
    
    for module_name in project_modules:
        try:
            importlib.import_module(module_name)
            print(f"✓ Projekto modulis {module_name} sėkmingai importuotas")
        except ImportError as e:
            print(f"✗ Klaida importuojant projekto modulį {module_name}: {str(e)}")
            return False
    
    print("Visi projekto moduliai sėkmingai importuoti")
    return True

def check_database_tables():
    """
    Patikrina duomenų bazės lenteles ir jų stulpelius
    """
    from database import SQLALCHEMY_DATABASE_URL
    from sqlalchemy import create_engine
    
    print("\nTikrinamos duomenų bazės lentelės...")
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    inspector = inspect(engine)
    
    expected_tables = ['models', 'simulations', 'trades', 'predictions', 'metrics']
    
    for table in expected_tables:
        if table in inspector.get_table_names():
            print(f"✓ Lentelė {table} egzistuoja")
            
            # Patikrinam stulpelius
            columns = inspector.get_columns(table)
            column_names = [col['name'] for col in columns]
            print(f"  Stulpeliai: {', '.join(column_names)}")
        else:
            print(f"✗ Lentelė {table} neegzistuoja!")
    
    return True

if __name__ == "__main__":
    print("Inicializuojama duomenų bazė...\n")
    
    # Patikriname importus
    if validate_imports():
        print("\nVisi importai sėkmingai patikrinti.")
    else:
        print("\nKai kurie importai nepavyko. Patikrinkite klaidas aukščiau.")
        sys.exit(1)
    
    # Patikriname duomenų bazės lenteles
    if check_database_tables():
        print("\nDuomenų bazės lentelės sėkmingai patikrintos.")
    else:
        print("\nKai kurios duomenų bazės lentelės nebuvo rastos. Paleiskite migracijas.")