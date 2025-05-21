"""
Pavyzdinis skriptas, parodantis kaip eksportuoti eksperimento rezultatus į CSV.
"""
import os
import sys
import logging
from datetime import datetime

# Pridedame pagrindinį projekto katalogą į kelią
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importuojame reikalingas bibliotekas
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from database import SQLALCHEMY_DATABASE_URL
from services.experiment_service import ExperimentService

# Konfigūruojame žurnalą
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """
    Pagrindinė funkcija, demonstruojanti eksperimento rezultatų eksportavimą į CSV.
    """
    try:
        # Sukuriame duomenų bazės ryšį
        logger.info("Jungiamasi prie duomenų bazės...")
        engine = create_engine(SQLALCHEMY_DATABASE_URL)
        db = Session(engine)

        # Inicializuojame eksperimentų servisą
        logger.info("Inicializuojame eksperimentų servisą...")
        experiment_service = ExperimentService(db)
        
        # Gauname visus eksperimentus
        experiments = experiment_service.get_all_experiments(limit=10)
        
        if not experiments:
            logger.warning("Nėra jokių eksperimentų duomenų bazėje")
            return
        
        # Pasirenkame pirmą eksperimentą, kuris turi rezultatų
        selected_experiment = None
        
        for exp in experiments:
            # Tikriname, ar eksperimentas turi rezultatų
            results = experiment_service.get_experiment_results(exp.id)
            if results:
                selected_experiment = exp
                break
        
        if not selected_experiment:
            logger.warning("Nerasta eksperimentų su rezultatais")
            return
        
        # Sukuriame eksporto direktoriją, jei jos nėra
        export_dir = os.path.join(os.path.dirname(__file__), '..', 'exports')
        os.makedirs(export_dir, exist_ok=True)
        
        # Sukuriame failo pavadinimą su eksperimento pavadinimu ir data
        file_name = f"{selected_experiment.name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        output_file = os.path.join(export_dir, file_name)
        
        # Eksportuojame rezultatus į CSV
        logger.info(f"Eksportuojame eksperimento '{selected_experiment.name}' rezultatus į CSV...")
        success = experiment_service.export_results_to_csv(
            experiment_id=selected_experiment.id,
            output_file=output_file,
            include_stage=True,
            include_notes=True
        )
        
        if success:
            logger.info(f"Rezultatai sėkmingai eksportuoti į: {output_file}")
            
            # Parodome CSV failo kelią ir pavadinimą
            absolute_path = os.path.abspath(output_file)
            logger.info(f"Pilnas failo kelias: {absolute_path}")
            
            # Perskaitome ir parodome keletą CSV failo eilučių
            with open(output_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()[:6]  # Pirmosios 6 eilutės (antraštė + 5 rezultatai)
                
                logger.info("CSV failo turinys (pirmosios eilutės):")
                for i, line in enumerate(lines):
                    logger.info(f"{i+1}: {line.strip()}")
        else:
            logger.error("Eksportavimas nepavyko")
        
        # Uždarome duomenų bazės sesiją
        db.close()
        logger.info("Pavyzdžio vykdymas baigtas.")
        
    except Exception as e:
        logger.error(f"Klaida vykdant pavyzdį: {str(e)}")
        raise

if __name__ == "__main__":
    main()