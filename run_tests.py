import os
import sys
import importlib

# Pirmiausia įkelti importavimo nustatymus
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from setup_imports import setup_path

# Nustatome kelią
setup_path()

# Išvalome modulių cache, kad užtikrintume švarų importavimą
if 'database.models.results_models' in sys.modules:
    del sys.modules['database.models.results_models']
if 'database.repositories.results_repository' in sys.modules:
    del sys.modules['database.repositories.results_repository']

# Patikriname, ar galima importuoti probleminius modulius
try:
    import database.models.results_models
    print("✓ database.models.results_models importuotas sėkmingai")
except ImportError as e:
    print(f"✗ Nepavyko importuoti database.models.results_models: {e}")

try:
    import database.repository.results_repository
    print("✓ database.repositories.results_repository importuotas sėkmingai")
except ImportError as e:
    print(f"✗ Nepavyko importuoti database.repositories.results_repository: {e}")

# Importuojame ir paleidžiame testus
try:
    print("Bandoma paleisti testus...")
    from app.tests import run_tests
    run_tests.main()
except Exception as e:
    print(f"Klaida paleidžiant testus: {e}")