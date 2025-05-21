"""
Testų paleidimo skriptas, kuris surinks visus testus, juos įvykdys
ir pateiks rezultatus.
"""
import unittest
import logging
import sys
import os
from datetime import datetime

# Pridedame projekto katalogą į Python kelią
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Konfigūruojame logerį
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(__file__), "test_results.log")),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def run_tests():
    """
    Suranda ir paleidžia visus testus direktorijoje.
    Generuoja rezultatų ataskaitą.
    """
    # Pažymime testavimo pradžią
    logger.info("=" * 50)
    logger.info(f"Testavimas pradėtas: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 50)
    
    # Surandame visus testus
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover(os.path.dirname(__file__), pattern="test_*.py")
    
    # Sukuriame testavimo rezultatų objektą ir paleidžiame testus
    test_result = unittest.TextTestRunner(verbosity=2).run(test_suite)
    
    # Spausdiname rezultatus
    logger.info("=" * 50)
    logger.info(f"Testavimas baigtas: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Vykdyta testų: {test_result.testsRun}")
    logger.info(f"Sėkmingų testų: {test_result.testsRun - len(test_result.errors) - len(test_result.failures)}")
    logger.info(f"Nesėkmingų testų: {len(test_result.failures)}")
    logger.info(f"Klaidų: {len(test_result.errors)}")
    logger.info("=" * 50)
    
    # Spausdiname detalią nesėkmingų testų informaciją
    if test_result.failures:
        logger.info("NESĖKMINGI TESTAI:")
        for failure in test_result.failures:
            logger.info(f"- {failure[0]}")
            logger.info(f"  Klaida: {failure[1]}")
    
    # Spausdiname detalią klaidų informaciją
    if test_result.errors:
        logger.info("TESTŲ KLAIDOS:")
        for error in test_result.errors:
            logger.info(f"- {error[0]}")
            logger.info(f"  Klaida: {error[1]}")
    
    # Grąžiname ar visi testai pavyko
    return len(test_result.failures) == 0 and len(test_result.errors) == 0

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)