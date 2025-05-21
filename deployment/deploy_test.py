"""
Skriptas naujos schemos diegimui į testavimo aplinką.
"""
import os
import sys
import shutil
import logging
import argparse
from datetime import datetime

# Pridedame pagrindinį projekto katalogą į Python kelią
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Konfigūruojame žurnalą
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(__file__), "deployment.log")),
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
    parser = argparse.ArgumentParser(description="Diegimo į testavimo aplinką įrankis")
    
    parser.add_argument(
        "--test-path", 
        default=os.path.join(os.path.dirname(__file__), "../test_environment"),
        help="Testavimo aplinkos kelias"
    )
    
    parser.add_argument(
        "--db-name", 
        default="ca_btc_test.db",
        help="Testavimo duomenų bazės failo pavadinimas"
    )
    
    parser.add_argument(
        "--clean", 
        action="store_true",
        help="Išvalyti testavimo aplinką prieš diegiant"
    )
    
    return parser.parse_args()

def prepare_test_environment(test_path, clean=False):
    """
    Paruošia testavimo aplinką.
    
    Args:
        test_path: Testavimo aplinkos kelias
        clean: Ar išvalyti testavimo aplinką
    
    Returns:
        bool: Ar pavyko paruošti aplinką
    """
    try:
        # Tikriname, ar testavimo aplinkos kelias egzistuoja
        if not os.path.exists(test_path):
            os.makedirs(test_path)
            logger.info(f"Sukurtas testavimo aplinkos katalogas: {test_path}")
        
        # Jei nurodyta, išvalome testavimo aplinką
        if clean and os.path.exists(test_path):
            # Sukuriame atsarginę kopiją prieš išvalant
            backup_folder = f"{test_path}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            if os.path.exists(test_path) and os.listdir(test_path):
                shutil.copytree(test_path, backup_folder)
                logger.info(f"Sukurta testavimo aplinkos atsarginė kopija: {backup_folder}")
            
            # Išvalome testavimo aplinkos katalogą, bet neištriname paties katalogo
            for item in os.listdir(test_path):
                item_path = os.path.join(test_path, item)
                if os.path.isfile(item_path):
                    os.remove(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
            
            logger.info(f"Testavimo aplinka išvalyta: {test_path}")
        
        return True
    
    except Exception as e:
        logger.error(f"Klaida ruošiant testavimo aplinką: {str(e)}")
        return False

def copy_project_files(test_path):
    """
    Kopijuoja projekto failus į testavimo aplinką.
    
    Args:
        test_path: Testavimo aplinkos kelias
    
    Returns:
        bool: Ar pavyko nukopijuoti failus
    """
    try:
        # Projekto pagrindinis kelias
        project_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        
        # Katalogai, kuriuos kopijuojame
        folders_to_copy = ['database', 'services', 'examples', 'tests']
        
        # Kopijuojame kiekvieną katalogą
        for folder in folders_to_copy:
            source_folder = os.path.join(project_path, folder)
            target_folder = os.path.join(test_path, folder)
            
            # Tikriname, ar šaltinio katalogas egzistuoja
            if os.path.exists(source_folder):
                # Jei tikslo katalogas jau egzistuoja, išvalome jį
                if os.path.exists(target_folder):
                    shutil.rmtree(target_folder)
                
                # Kopijuojame katalogą
                shutil.copytree(source_folder, target_folder)
                logger.info(f"Nukopijuotas katalogas: {folder}")
            else:
                logger.warning(f"Katalogas nerastas: {source_folder}")
        
        # Kopijuojame pagrindinius Python modulius
        python_files = [f for f in os.listdir(project_path) if f.endswith('.py')]
        
        for py_file in python_files:
            source_file = os.path.join(project_path, py_file)
            target_file = os.path.join(test_path, py_file)
            
            shutil.copy2(source_file, target_file)
            logger.info(f"Nukopijuotas failas: {py_file}")
        
        # Kopijuojame requirements.txt, jei jis egzistuoja
        req_file = os.path.join(project_path, "requirements.txt")
        if os.path.exists(req_file):
            shutil.copy2(req_file, os.path.join(test_path, "requirements.txt"))
            logger.info("Nukopijuotas requirements.txt failas")
        
        return True
    
    except Exception as e:
        logger.error(f"Klaida kopijuojant projekto failus: {str(e)}")
        return False

def setup_test_database(test_path, db_name):
    """
    Sukonfigūruoja testavimo duomenų bazę.
    
    Args:
        test_path: Testavimo aplinkos kelias
        db_name: Duomenų bazės failo pavadinimas
    
    Returns:
        bool: Ar pavyko sukonfigūruoti duomenų bazę
    """
    try:
        # Duomenų bazės konfigūracijos failo kelias
        db_config_path = os.path.join(test_path, "database", "__init__.py")
        
        # Jei failas neegzistuoja, grąžiname klaidą
        if not os.path.exists(db_config_path):
            logger.error(f"Duomenų bazės konfigūracijos failas nerastas: {db_config_path}")
            return False
        
        # Sukuriame testavimo duomenų bazės kelią
        test_db_path = os.path.join(test_path, db_name)
        
        # Atnaujinamos duomenų bazės prisijungimo nuostatos
        with open(db_config_path, 'r') as f:
            content = f.read()
        
        # Pakeičiame duomenų bazės URL
        updated_content = content.replace(
            'SQLALCHEMY_DATABASE_URL = "sqlite:///ca_btc.db"',
            f'SQLALCHEMY_DATABASE_URL = "sqlite:///{db_name}"'
        )
        
        # Išsaugome atnaujintą failą
        with open(db_config_path, 'w') as f:
            f.write(updated_content)
        
        logger.info(f"Duomenų bazės konfigūracija atnaujinta: {db_config_path}")
        
        # Patikriname, ar reikia sukurti duomenų bazę
        if not os.path.exists(test_db_path):
            # Duomenų bazė bus sukurta pirmą kartą paleidus migracijos skriptą
            logger.info(f"Duomenų bazės failas bus sukurtas migracijos metu: {test_db_path}")
        
        return True
    
    except Exception as e:
        logger.error(f"Klaida konfigūruojant testavimo duomenų bazę: {str(e)}")
        return False

def run_database_migration(test_path):
    """
    Paleidžia duomenų bazės migracijos skriptą.
    
    Args:
        test_path: Testavimo aplinkos kelias
    
    Returns:
        bool: Ar pavyko paleisti migraciją
    """
    try:
        # Migracijos skripto kelias
        migration_script_path = os.path.join(test_path, "database", "migration_script.py")
        
        # Tikriname, ar migracijos skriptas egzistuoja
        if not os.path.exists(migration_script_path):
            logger.error(f"Migracijos skriptas nerastas: {migration_script_path}")
            return False
        
        # Keičiame darbo katalogą į testavimo aplinką
        original_dir = os.getcwd()
        os.chdir(test_path)
        
        # Paleidžiame migracijos skriptą Python interpretatoriu
        logger.info("Paleidžiamas migracijos skriptas...")
        import subprocess
        result = subprocess.run(
            [sys.executable, migration_script_path],
            capture_output=True,
            text=True
        )
        
        # Grįžtame į pradinį katalogą
        os.chdir(original_dir)
        
        # Tikriname, ar migracijos skriptas pavyko
        if result.returncode == 0:
            logger.info("Migracijos skriptas įvykdytas sėkmingai")
            logger.info(f"Migracijos išvestis: {result.stdout}")
            return True
        else:
            logger.error(f"Migracijos skriptas nepavyko su klaidos kodu: {result.returncode}")
            logger.error(f"Migracijos klaida: {result.stderr}")
            return False
    
    except Exception as e:
        logger.error(f"Klaida paleidžiant migracijos skriptą: {str(e)}")
        return False

def deploy_to_test_environment():
    """
    Diegia projektą į testavimo aplinką.
    
    Returns:
        bool: Ar diegimas pavyko
    """
    try:
        # Analizuojame komandinės eilutės argumentus
        args = parse_arguments()
        
        logger.info(f"Pradedamas diegimas į testavimo aplinką: {args.test_path}")
        
        # Paruošiame testavimo aplinką
        if not prepare_test_environment(args.test_path, args.clean):
            logger.error("Nepavyko paruošti testavimo aplinkos, diegimas nutraukiamas")
            return False
        
        # Kopijuojame projekto failus
        if not copy_project_files(args.test_path):
            logger.error("Nepavyko nukopijuoti projekto failų, diegimas nutraukiamas")
            return False
        
        # Konfigūruojame testavimo duomenų bazę
        if not setup_test_database(args.test_path, args.db_name):
            logger.error("Nepavyko sukonfigūruoti testavimo duomenų bazės, diegimas nutraukiamas")
            return False
        
        # Paleidžiame duomenų bazės migraciją
        if not run_database_migration(args.test_path):
            logger.error("Nepavyko atlikti duomenų bazės migracijos, diegimas nutraukiamas")
            return False
        
        logger.info(f"Diegimas į testavimo aplinką baigtas sėkmingai: {args.test_path}")
        return True
    
    except Exception as e:
        logger.error(f"Klaida diegiant į testavimo aplinką: {str(e)}")
        return False

if __name__ == "__main__":
    # Paleidžiame diegimą į testavimo aplinką
    success = deploy_to_test_environment()
    sys.exit(0 if success else 1)