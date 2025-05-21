"""
Skriptas schemos perkėlimui į produkcinę aplinką.
"""
import os
import sys
import shutil
import logging
import argparse
import json
from datetime import datetime

# Konfigūruojame žurnalą
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(__file__), "production_deployment.log")),
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
    parser = argparse.ArgumentParser(description="Diegimo į produkcinę aplinką įrankis")
    
    parser.add_argument(
        "--prod-path", 
        default=os.path.join(os.path.dirname(__file__), "../production"),
        help="Produkcinės aplinkos kelias"
    )
    
    parser.add_argument(
        "--test-path", 
        default=os.path.join(os.path.dirname(__file__), "../test_environment"),
        help="Testavimo aplinkos kelias"
    )
    
    parser.add_argument(
        "--db-name", 
        default="ca_btc_prod.db",
        help="Produkcinės duomenų bazės failo pavadinimas"
    )
    
    parser.add_argument(
        "--config-file", 
        default=os.path.join(os.path.dirname(__file__), "production_config.json"),
        help="Produkcinės aplinkos konfigūracijos failas"
    )
    
    parser.add_argument(
        "--force", 
        action="store_true",
        help="Priverstinai diegti, net jei funkcionalumo testai nepavyko"
    )
    
    return parser.parse_args()

def create_default_config(config_file):
    """
    Sukuria numatytąjį konfigūracijos failą, jei jis neegzistuoja.
    
    Args:
        config_file: Konfigūracijos failo kelias
    """
    if not os.path.exists(config_file):
        config = {
            "db_connection": "sqlite:///ca_btc_prod.db",
            "log_level": "INFO",
            "backup_enabled": True,
            "backup_retention_days": 30,
            "environment": "production"
        }
        
        # Sukuriame katalogą, jei jo nėra
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        
        # Išsaugome konfigūraciją
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=4)
        
        logger.info(f"Sukurtas numatytasis konfigūracijos failas: {config_file}")

def test_functionality(test_path):
    """
    Patikrina, ar visos funkcijos veikia teisingai testavimo aplinkoje.
    
    Args:
        test_path: Testavimo aplinkos kelias
    
    Returns:
        bool: Ar visos funkcijos veikia teisingai
    """
    try:
        # Funkcionalumo testavimo skripto kelias
        test_script_path = os.path.join(os.path.dirname(__file__), "test_functionality.py")
        
        # Tikriname, ar testavimo skriptas egzistuoja
        if not os.path.exists(test_script_path):
            logger.error(f"Funkcionalumo testavimo skriptas nerastas: {test_script_path}")
            return False
        
        # Paleidžiame testavimo skriptą
        logger.info("Tikrinamas sistemos funkcionalumas testavimo aplinkoje...")
        
        import subprocess
        result = subprocess.run(
            [sys.executable, test_script_path, "--test-path", test_path, "--run-examples"],
            capture_output=True,
            text=True
        )
        
        # Tikriname, ar testai pavyko
        if result.returncode == 0:
            logger.info("Funkcionalumo testai pavyko")
            logger.info(f"Testų išvestis: {result.stdout}")
            return True
        else:
            logger.error(f"Funkcionalumo testai nepavyko su klaidos kodu: {result.returncode}")
            logger.error(f"Testų klaida: {result.stderr}")
            return False
    
    except Exception as e:
        logger.error(f"Klaida tikrinant funkcionalumą: {str(e)}")
        return False

def prepare_production_environment(prod_path):
    """
    Paruošia produkcinę aplinką.
    
    Args:
        prod_path: Produkcinės aplinkos kelias
    
    Returns:
        bool: Ar pavyko paruošti aplinką
    """
    try:
        # Tikriname, ar produkcinės aplinkos kelias egzistuoja
        if not os.path.exists(prod_path):
            os.makedirs(prod_path)
            logger.info(f"Sukurtas produkcinės aplinkos katalogas: {prod_path}")
            return True
        
        # Jei kelias egzistuoja, sukuriame atsarginę kopiją
        backup_folder = f"{prod_path}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if os.path.exists(prod_path) and os.listdir(prod_path):
            shutil.copytree(prod_path, backup_folder)
            logger.info(f"Sukurta produkcinės aplinkos atsarginė kopija: {backup_folder}")
        
        return True
    
    except Exception as e:
        logger.error(f"Klaida ruošiant produkcinę aplinką: {str(e)}")
        return False

def copy_from_test_to_production(test_path, prod_path):
    """
    Kopijuoja failus iš testavimo į produkcinę aplinką.
    
    Args:
        test_path: Testavimo aplinkos kelias
        prod_path: Produkcinės aplinkos kelias
    
    Returns:
        bool: Ar pavyko nukopijuoti failus
    """
    try:
        # Katalogai, kuriuos kopijuojame
        folders_to_copy = ['database', 'services', 'examples', 'tests']
        
        # Kopijuojame kiekvieną katalogą
        for folder in folders_to_copy:
            source_folder = os.path.join(test_path, folder)
            target_folder = os.path.join(prod_path, folder)
            
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
        python_files = [f for f in os.listdir(test_path) if f.endswith('.py')]
        
        for py_file in python_files:
            source_file = os.path.join(test_path, py_file)
            target_file = os.path.join(prod_path, py_file)
            
            shutil.copy2(source_file, target_file)
            logger.info(f"Nukopijuotas failas: {py_file}")
        
        # Kopijuojame requirements.txt, jei jis egzistuoja
        req_file = os.path.join(test_path, "requirements.txt")
        if os.path.exists(req_file):
            shutil.copy2(req_file, os.path.join(prod_path, "requirements.txt"))
            logger.info("Nukopijuotas requirements.txt failas")
        
        return True
    
    except Exception as e:
        logger.error(f"Klaida kopijuojant failus iš testavimo į produkcinę aplinką: {str(e)}")
        return False

def setup_production_database(prod_path, db_name, config_file):
    """
    Sukonfigūruoja produkcinę duomenų bazę.
    
    Args:
        prod_path: Produkcinės aplinkos kelias
        db_name: Duomenų bazės failo pavadinimas
        config_file: Konfigūracijos failo kelias
    
    Returns:
        bool: Ar pavyko sukonfigūruoti duomenų bazę
    """
    try:
        # Duomenų bazės konfigūracijos failo kelias
        db_config_path = os.path.join(prod_path, "database", "__init__.py")
        
        # Jei failas neegzistuoja, grąžiname klaidą
        if not os.path.exists(db_config_path):
            logger.error(f"Duomenų bazės konfigūracijos failas nerastas: {db_config_path}")
            return False
        
        # Sukuriame produkcinės duomenų bazės kelią
        prod_db_path = os.path.join(prod_path, db_name)
        
        # Nuskaitome konfigūraciją
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        # Atnaujinamos duomenų bazės prisijungimo nuostatos
        with open(db_config_path, 'r') as f:
            content = f.read()
        
        # Pakeičiame duomenų bazės URL
        updated_content = content.replace(
            'SQLALCHEMY_DATABASE_URL = "sqlite:///ca_btc.db"',
            f'SQLALCHEMY_DATABASE_URL = "{config["db_connection"]}"'
        )
        
        # Išsaugome atnaujintą failą
        with open(db_config_path, 'w') as f:
            f.write(updated_content)
        
        logger.info(f"Duomenų bazės konfigūracija atnaujinta: {db_config_path}")
        
        return True
    
    except Exception as e:
        logger.error(f"Klaida konfigūruojant produkcinę duomenų bazę: {str(e)}")
        return False

def run_database_migration(prod_path):
    """
    Paleidžia duomenų bazės migracijos skriptą produkcinėje aplinkoje.
    
    Args:
        prod_path: Produkcinės aplinkos kelias
    
    Returns:
        bool: Ar pavyko paleisti migraciją
    """
    try:
        # Migracijos skripto kelias
        migration_script_path = os.path.join(prod_path, "database", "migration_script.py")
        
        # Tikriname, ar migracijos skriptas egzistuoja
        if not os.path.exists(migration_script_path):
            logger.error(f"Migracijos skriptas nerastas: {migration_script_path}")
            return False
        
        # Keičiame darbo katalogą į produkcinę aplinką
        original_dir = os.getcwd()
        os.chdir(prod_path)
        
        # Paleidžiame migracijos skriptą Python interpretatoriu
        logger.info("Paleidžiamas migracijos skriptas produkcinėje aplinkoje...")
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
            logger.info("Migracijos skriptas produkcinėje aplinkoje įvykdytas sėkmingai")
            logger.info(f"Migracijos išvestis: {result.stdout}")
            return True
        else:
            logger.error(f"Migracijos skriptas produkcinėje aplinkoje nepavyko su klaidos kodu: {result.returncode}")
            logger.error(f"Migracijos klaida: {result.stderr}")
            return False
    
    except Exception as e:
        logger.error(f"Klaida paleidžiant migracijos skriptą produkcinėje aplinkoje: {str(e)}")
        return False

def deploy_to_production():
    """
    Diegia projektą į produkcinę aplinką.
    
    Returns:
        bool: Ar diegimas pavyko
    """
    try:
        # Analizuojame komandinės eilutės argumentus
        args = parse_arguments()
        
        # Sukuriame numatytąjį konfigūracijos failą, jei jis neegzistuoja
        create_default_config(args.config_file)
        
        logger.info(f"Pradedamas diegimas į produkcinę aplinką: {args.prod_path}")
        
        # Tikriname, ar testavimo aplinka egzistuoja
        if not os.path.exists(args.test_path):
            logger.error(f"Testavimo aplinka nerasta: {args.test_path}")
            return False
        
        # Patikriname funkcionalumą testavimo aplinkoje, nebent nurodyta priverstinai diegti
        if not args.force:
            if not test_functionality(args.test_path):
                logger.error("Funkcionalumo testai nepavyko, diegimas nutraukiamas. Naudokite --force parametrą, jei norite diegti priverstinai.")
                return False
        else:
            logger.warning("Priverstinis diegimas, funkcionalumo testai praleidžiami")
        
        # Paruošiame produkcinę aplinką
        if not prepare_production_environment(args.prod_path):
            logger.error("Nepavyko paruošti produkcinės aplinkos, diegimas nutraukiamas")
            return False
        
        # Kopijuojame failus iš testavimo į produkcinę aplinką
        if not copy_from_test_to_production(args.test_path, args.prod_path):
            logger.error("Nepavyko nukopijuoti failų į produkcinę aplinką, diegimas nutraukiamas")
            return False
        
        # Konfigūruojame produkcinę duomenų bazę
        if not setup_production_database(args.prod_path, args.db_name, args.config_file):
            logger.error("Nepavyko sukonfigūruoti produkcinės duomenų bazės, diegimas nutraukiamas")
            return False
        
        # Paleidžiame duomenų bazės migraciją produkcinėje aplinkoje
        if not run_database_migration(args.prod_path):
            logger.error("Nepavyko atlikti duomenų bazės migracijos produkcinėje aplinkoje, diegimas nutraukiamas")
            return False
        
        logger.info(f"Diegimas į produkcinę aplinką baigtas sėkmingai: {args.prod_path}")
        return True
    
    except Exception as e:
        logger.error(f"Klaida diegiant į produkcinę aplinką: {str(e)}")
        return False

if __name__ == "__main__":
    # Paleidžiame diegimą į produkcinę aplinką
    success = deploy_to_production()
    sys.exit(0 if success else 1)