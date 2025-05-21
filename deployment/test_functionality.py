"""
Skriptas, patikrinantis ar visos sistemos funkcijos veikia teisingai 
testavimo aplinkoje prieš perkėlimą į produkcinę aplinką.
"""
import os
import sys
import logging
import argparse
import unittest
from datetime import datetime

# Konfigūruojame žurnalą
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(__file__), "functionality_test.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def parse_arguments():
    """
    Analizuoja komandinės eilutės argumentus.
    
    Returns:
        argparse.Namespace: Argumentų objektas
    """
    parser = argparse.ArgumentParser(description="Sistemos funkcionalumo testavimo įrankis")
    
    parser.add_argument(
        "--test-path", 
        default=os.path.join(os.path.dirname(__file__), "../test_environment"),
        help="Testavimo aplinkos kelias"
    )
    
    parser.add_argument(
        "--run-examples", 
        action="store_true",
        help="Paleisti pavyzdžius funkcionalumo patikrinimui"
    )
    
    return parser.parse_args()

def run_unit_tests(test_path):
    """
    Paleidžia visus vieneto testus.
    
    Args:
        test_path: Testavimo aplinkos kelias
    
    Returns:
        bool: Ar visi testai pavyko
    """
    try:
        # Keičiame darbo katalogą į testavimo aplinką
        original_dir = os.getcwd()
        os.chdir(test_path)
        
        # Pridedame testavimo aplinką į Python kelią
        sys.path.insert(0, test_path)
        
        # Paleidžiame testus
        logger.info("Paleidžiami vieneto testai...")
        
        # Tikriname, ar yra run_tests.py skriptas
        run_tests_path = os.path.join(test_path, "tests", "run_tests.py")
        
        if os.path.exists(run_tests_path):
            # Paleidžiame testus su run_tests.py skriptu
            import subprocess
            result = subprocess.run(
                [sys.executable, run_tests_path],
                capture_output=True,
                text=True
            )
            
            # Tikriname, ar testai pavyko
            if result.returncode == 0:
                logger.info("Visi testai pavyko")
                logger.info(f"Testų išvestis: {result.stdout}")
                success = True
            else:
                logger.error(f"Kai kurie testai nepavyko su klaidos kodu: {result.returncode}")
                logger.error(f"Testų klaida: {result.stderr}")
                success = False
        else:
            # Jei nėra run_tests.py skripto, naudojame unittest modulį tiesiogiai
            test_loader = unittest.TestLoader()
            test_suite = test_loader.discover(os.path.join(test_path, "tests"), pattern="test_*.py")
            
            test_result = unittest.TextTestRunner(verbosity=2).run(test_suite)
            
            # Tikriname, ar testai pavyko
            if test_result.wasSuccessful():
                logger.info("Visi testai pavyko")
                success = True
            else:
                logger.error(f"Kai kurie testai nepavyko: {len(test_result.failures)} klaidos, {len(test_result.errors)} klaidos")
                for failure in test_result.failures:
                    logger.error(f"Testas nepavyko: {failure[0]}")
                for error in test_result.errors:
                    logger.error(f"Testas sukėlė klaidą: {error[0]}")
                success = False
        
        # Grįžtame į pradinį katalogą
        os.chdir(original_dir)
        
        return success
    
    except Exception as e:
        logger.error(f"Klaida paleidžiant vieneto testus: {str(e)}")
        # Grįžtame į pradinį katalogą, jei įvyko klaida
        if 'original_dir' in locals():
            os.chdir(original_dir)
        return False

def run_examples(test_path):
    """
    Paleidžia pavyzdžius funkcionalumo patikrinimui.
    
    Args:
        test_path: Testavimo aplinkos kelias
    
    Returns:
        bool: Ar visi pavyzdžiai pavyko
    """
    try:
        # Keičiame darbo katalogą į testavimo aplinką
        original_dir = os.getcwd()
        os.chdir(test_path)
        
        # Pridedame testavimo aplinką į Python kelią
        sys.path.insert(0, test_path)
        
        # Ieškome pavyzdžių
        examples_dir = os.path.join(test_path, "examples")
        if not os.path.exists(examples_dir):
            logger.error(f"Pavyzdžių katalogas nerastas: {examples_dir}")
            os.chdir(original_dir)
            return False
        
        # Randam visus Python failus pavyzdžių kataloge
        example_files = [f for f in os.listdir(examples_dir) if f.endswith('.py')]
        
        if not example_files:
            logger.warning(f"Pavyzdžių kataloge nerasta Python failų: {examples_dir}")
            os.chdir(original_dir)
            return True
        
        # Paleidžiame kiekvieną pavyzdį
        success = True
        logger.info(f"Paleidžiami {len(example_files)} pavyzdžiai...")
        
        for example_file in example_files:
            example_path = os.path.join(examples_dir, example_file)
            logger.info(f"Paleidžiamas pavyzdys: {example_file}")
            
            import subprocess
            result = subprocess.run(
                [sys.executable, example_path],
                capture_output=True,
                text=True
            )
            
            # Tikriname, ar pavyzdys pavyko
            if result.returncode == 0:
                logger.info(f"Pavyzdys {example_file} pavyko")
            else:
                logger.error(f"Pavyzdys {example_file} nepavyko su klaidos kodu: {result.returncode}")
                logger.error(f"Klaida: {result.stderr}")
                success = False
        
        # Grįžtame į pradinį katalogą
        os.chdir(original_dir)
        
        return success
    
    except Exception as e:
        logger.error(f"Klaida paleidžiant pavyzdžius: {str(e)}")
        # Grįžtame į pradinį katalogą, jei įvyko klaida
        if 'original_dir' in locals():
            os.chdir(original_dir)
        return False

def verify_database_integrity(test_path):
    """
    Patikrina duomenų bazės integralumą.
    
    Args:
        test_path: Testavimo aplinkos kelias
    
    Returns:
        bool: Ar duomenų bazės integralumas teisingas
    """
    try:
        # Pridedame testavimo aplinką į Python kelią
        sys.path.insert(0, test_path)
        
        # Importuojame reikalingas bibliotekas
        import sqlite3
        
        # Randame duomenų bazės failą
        db_files = [f for f in os.listdir(test_path) if f.endswith('.db')]
        
        if not db_files:
            logger.error(f"Nerasta duomenų bazės failų testavimo aplinkoje: {test_path}")
            return False
        
        # Naudojame pirmą rastą duomenų bazės failą
        db_path = os.path.join(test_path, db_files[0])
        logger.info(f"Tikrinamas duomenų bazės integralumas: {db_path}")
        
        # Atidarome duomenų bazę
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Tikriname, ar visos reikalingos lentelės egzistuoja
        required_tables = ['models', 'simulations', 'trades', 'predictions']
        
        # Gauname visas lenteles
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        
        # Tikriname, ar visos reikalingos lentelės yra
        missing_tables = [table for table in required_tables if table not in tables]
        
        if missing_tables:
            logger.error(f"Trūksta šių lentelių: {', '.join(missing_tables)}")
            conn.close()
            return False
        
        # Tikriname ryšius
        success = True
        
        # 1. Patikriname, ar models->simulations ryšys veikia
        try:
            cursor.execute("SELECT m.id FROM models m LEFT JOIN simulations s ON m.id = s.model_id LIMIT 1")
            cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(f"Klaida tikrinant models->simulations ryšį: {str(e)}")
            success = False
        
        # 2. Patikriname, ar simulations->trades ryšys veikia
        try:
            cursor.execute("SELECT s.id FROM simulations s LEFT JOIN trades t ON s.id = t.simulation_id LIMIT 1")
            cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(f"Klaida tikrinant simulations->trades ryšį: {str(e)}")
            success = False
        
        # 3. Patikriname, ar models->predictions ryšys veikia
        try:
            cursor.execute("SELECT m.id FROM models m LEFT JOIN predictions p ON m.id = p.model_id LIMIT 1")
            cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(f"Klaida tikrinant models->predictions ryšį: {str(e)}")
            success = False
        
        # Uždarome jungtį
        conn.close()
        
        if success:
            logger.info("Duomenų bazės integralumas teisingas, visi ryšiai veikia")
        
        return success
    
    except Exception as e:
        logger.error(f"Klaida tikrinant duomenų bazės integralumą: {str(e)}")
        return False

def test_functionality():
    """
    Patikrina sistemos funkcionalumą testavimo aplinkoje.
    
    Returns:
        bool: Ar visos funkcijos veikia teisingai
    """
    try:
        # Analizuojame komandinės eilutės argumentus
        args = parse_arguments()
        
        logger.info(f"Pradedamas funkcionalumo testavimas aplinkoje: {args.test_path}")
        
        # Patikriname, ar testavimo aplinka egzistuoja
        if not os.path.exists(args.test_path):
            logger.error(f"Testavimo aplinka nerasta: {args.test_path}")
            return False
        
        # Patikriname duomenų bazės integralumą
        if not verify_database_integrity(args.test_path):
            logger.error("Duomenų bazės integralumo tikrinimas nepavyko")
            return False
        
        # Paleidžiame vieneto testus
        if not run_unit_tests(args.test_path):
            logger.error("Kai kurie vieneto testai nepavyko")
            return False
        
        # Jei nurodyta, paleidžiame pavyzdžius
        if args.run_examples:
            if not run_examples(args.test_path):
                logger.error("Kai kurie pavyzdžiai nepavyko")
                return False
        
        logger.info("Funkcionalumo testavimas baigtas sėkmingai, visos funkcijos veikia teisingai")
        return True
    
    except Exception as e:
        logger.error(f"Klaida testuojant funkcionalumą: {str(e)}")
        return False

if __name__ == "__main__":
    # Paleidžiame funkcionalumo testavimą
    success = test_functionality()
    sys.exit(0 if success else 1)