"""
Pavyzdinis skriptas, parodantis kaip naudoti sesijų valdymą integruotą su treniravimo ir simuliacijų servisais.
"""
import os
import sys
import logging
import json
import time
from datetime import datetime

# Pridedame pagrindinį projekto katalogą į kelią
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importuojame reikalingas bibliotekas
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from database import SQLALCHEMY_DATABASE_URL
from services.user_service import UserService
from services.model_service import ModelService
from services.training_service import TrainingService
from services.simulation_service import SimulationService
from services.session_manager_service import SessionManagerService

# Konfigūruojame žurnalą
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """
    Pagrindinė funkcija, demonstruojanti sesijų valdymo integracijos naudojimą.
    """
    # Prisijungiame prie duomenų bazės
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    db_session = Session(engine)
    
    # Sukuriame reikalingus servisus
    user_service = UserService(db_session)
    model_service = ModelService(db_session)
    training_service = TrainingService(db_session)
    simulation_service = SimulationService(db_session)
    session_manager = SessionManagerService(db_session)
    
    # Saugosime sukurtų objektų ID, kad galėtume juos ištrinti pabaigoje
    user_id = None
    model_id = None
    training_session_id = None
    simulation_session_id = None
    
    try:
        logger.info("Pradedamas sesijų integracijos pavyzdys")
        
        # 1. Sukuriame naudotoją testavimui
        logger.info("1. Kuriame naudotoją")
        
        user_data = {
            "username": "integrated_sessions_test",
            "email": "integrated@example.com",
            "password": "slaptazodis123",
            "full_name": "Integruotos Sesijos"
        }
        
        user = user_service.create_user(user_data)
        
        if not user:
            logger.error("Nepavyko sukurti naudotojo")
            return
        
        user_id = user.id
        logger.info(f"Sukurtas naudotojas: ID={user.id}, Vardas={user.username}")
        
        # 2. Sukuriame modelį, su kuriuo dirbsime
        logger.info("2. Kuriame modelį")
        
        model_data = {
            "name": "Integruotų sesijų pavyzdžio modelis",
            "type": "lstm",
            "hyperparameters": {
                "layers": 3,
                "units": 128,
                "dropout": 0.3
            }
        }
        
        model = model_service.create_model(model_data)
        
        if not model:
            logger.error("Nepavyko sukurti modelio")
            return
        
        model_id = model.id
        logger.info(f"Sukurtas modelis: ID={model.id}, Pavadinimas={model.name}")
        
        # 3. Pradedame modelio treniravimą
        logger.info("3. Pradedame modelio treniravimą")
        
        training_params = {
            "dataset_name": "btc_historical_data",
            "total_epochs": 5,  # Mažas skaičius demonstruoti greitai
            "batch_size": 32,
            "learning_rate": 0.001,
            "validation_split": 0.2
        }
        
        training_result = training_service.start_training(user.id, model.id, training_params)
        
        if not training_result:
            logger.error("Nepavyko pradėti modelio treniravimo")
            return
        
        training_session_id = training_result["session_id"]
        logger.info(f"Pradėtas modelio treniravimas: Sesijos ID={training_session_id}")
        
        # 4. Stebime treniravimo progresą
        logger.info("4. Stebime treniravimo progresą")
        
        # Tikriname treniravimo būseną kas sekundę, bet ne daugiau kaip 15 kartų
        for i in range(15):
            training_status = training_service.get_training_status(training_session_id)
            
            if not training_status:
                logger.error("Nepavyko gauti treniravimo būsenos")
                break
            
            logger.info(f"Treniravimo būsena: Epocha {training_status['progress']['current_epoch']}/"
                        f"{training_status['progress']['total_epochs']} "
                        f"({training_status['progress']['percentage']}%), Statusas: {training_status['status']}")
            
            # Jei treniravimas baigtas, nutraukiame ciklą
            if training_status['status'] in ['completed', 'failed', 'stopped']:
                logger.info(f"Treniravimas baigtas su būsena: {training_status['status']}")
                break
            
            time.sleep(1)  # Laukiame 1 sekundę
        
        # 5. Gauname galutinius treniravimo rezultatus per session_manager
        logger.info("5. Gauname galutinius treniravimo rezultatus")
        
        session_info = session_manager.get_session_info(training_session_id)
        
        if session_info:
            logger.info(f"Treniravimo sesijos informacija: {json.dumps(session_info, default=str, indent=2)}")
        else:
            logger.error("Nepavyko gauti treniravimo sesijos informacijos")
        
        # 6. Pradedame Bitcoin kainos simuliaciją naudojant apmokytą modelį
        logger.info("6. Pradedame Bitcoin kainos simuliaciją")
        
        # Laukiame, kol modelis bus tikrai apmokytas
        while True:
            model = model_service.get_model(model_id)
            if model and model.trained:
                logger.info("Modelis sėkmingai apmokytas, pradedame simuliaciją")
                break
            time.sleep(1)
            logger.info("Laukiame, kol modelis bus apmokytas...")
        
        simulation_params = {
            "steps": 10,  # Mažas skaičius demonstruoti greitai
            "initial_price": 30000,
            "volatility": 0.02,
            "trend": 0.001
        }
        
        simulation_result = simulation_service.start_simulation(user.id, model.id, simulation_params)
        
        if not simulation_result:
            logger.error("Nepavyko pradėti Bitcoin kainos simuliacijos")
            return
        
        simulation_session_id = simulation_result["session_id"]
        logger.info(f"Pradėta Bitcoin kainos simuliacija: Sesijos ID={simulation_session_id}")
        
        # 7. Stebime simuliacijos progresą
        logger.info("7. Stebime simuliacijos progresą")
        
        # Tikriname simuliacijos būseną kas sekundę, bet ne daugiau kaip 15 kartų
        for i in range(15):
            simulation_status = simulation_service.get_simulation_status(simulation_session_id)
            
            if not simulation_status:
                logger.error("Nepavyko gauti simuliacijos būsenos")
                break
            
            if "progress" in simulation_status:
                logger.info(f"Simuliacijos būsena: Žingsnis {simulation_status['progress']['current_step']}/"
                            f"{simulation_status['progress']['total_steps']} "
                            f"({simulation_status['progress']['percentage']}%), Statusas: {simulation_status['status']}")
                
                if "current_price" in simulation_status:
                    logger.info(f"Dabartinė kaina: ${simulation_status['current_price']:.2f}")
            else:
                logger.info(f"Simuliacijos būsena: {simulation_status['status']}")
            
            # Jei simuliacija baigta, nutraukiame ciklą
            if simulation_status.get('status') in ['completed', 'failed', 'stopped']:
                logger.info(f"Simuliacija baigta su būsena: {simulation_status['status']}")
                break
            
            time.sleep(1)  # Laukiame 1 sekundę
        
        # 8. Gauname galutinius simuliacijos rezultatus
        logger.info("8. Gauname galutinius simuliacijos rezultatus")
        
        # Laukiame, kol simuliacija tikrai baigsis
        while True:
            simulation_status = simulation_service.get_simulation_status(simulation_session_id)
            if simulation_status and simulation_status.get('status') in ['completed', 'failed', 'stopped']:
                break
            time.sleep(1)
            logger.info("Laukiame, kol simuliacija bus baigta...")
        
        # Gauname detalius rezultatus
        simulation_info = session_manager.get_session_info(simulation_session_id)
        
        if simulation_info and "testing_session" in simulation_info and simulation_info["testing_session"].get("results"):
            results = simulation_info["testing_session"]["results"]
            if isinstance(results, str):
                results = json.loads(results)
            
            logger.info(f"Simuliacijos rezultatai:")
            logger.info(f"  Pradžios kaina: ${results['starting_price']:.2f}")
            logger.info(f"  Galutinė kaina: ${results['final_price']:.2f}")
            logger.info(f"  Kainos pokytis: {results['price_change_pct']:.2f}%")
            logger.info(f"  Kainos tendencija: {results['price_trend']}")
            logger.info(f"  Maks. kaina: ${results['max_price']:.2f}")
            logger.info(f"  Min. kaina: ${results['min_price']:.2f}")
            logger.info(f"  Simuliacijos trukmė: {results['simulation_time_seconds']:.2f} sek.")
        else:
            logger.error("Nepavyko gauti simuliacijos rezultatų")
        
        # 9. Gauname visus naudotojo sesijų sąrašus per session_manager
        logger.info("9. Gauname visus naudotojo sesijų sąrašus")
        
        sessions_list = session_manager.list_user_sessions(user.id)
        
        if sessions_list:
            logger.info(f"Naudotojo sesijų skaičius: {sessions_list['total']}")
            for session in sessions_list["items"]:
                logger.info(f"  - Sesija {session['id']}: tipas={session['type']}, statusas={session['status']}")
        else:
            logger.error("Nepavyko gauti naudotojo sesijų sąrašo")
        
        # 10. Gauname sesijų sąrašus per specializuotus servisus
        logger.info("10. Gauname sesijų sąrašus per specializuotus servisus")
        
        trainings_list = training_service.list_trainings(user_id=user.id)
        
        if trainings_list:
            logger.info(f"Naudotojo treniravimų skaičius: {trainings_list['total']}")
            for training in trainings_list["items"]:
                logger.info(f"  - Treniravimas {training['session_id']}: statusas={training['status']}")
        else:
            logger.error("Nepavyko gauti naudotojo treniravimų sąrašo")
        
        simulations_list = simulation_service.list_simulations(user_id=user.id)
        
        if simulations_list:
            logger.info(f"Naudotojo simuliacijų skaičius: {simulations_list['total']}")
            for simulation in simulations_list["items"]:
                logger.info(f"  - Simuliacija {simulation['session_id']}: statusas={simulation['status']}")
        else:
            logger.error("Nepavyko gauti naudotojo simuliacijų sąrašo")
        
        # 11. Valome testavimo duomenis
        logger.info("11. Valome testavimo duomenis")
        
        # Ištriname modelį
        if model_service.delete_model(model.id):
            logger.info(f"Modelis {model.id} ištrintas")
        
        # Ištriname naudotoją (kartu ištrins ir visas susijusias sesijas)
        if user_service.delete_user(user.id):
            logger.info(f"Naudotojas {user.id} ištrintas")
        
        logger.info("Sesijų integracijos pavyzdys baigtas")
        
    except Exception as e:
        logger.error(f"Įvyko klaida: {str(e)}")
        
        # Bandome išvalyti duomenis, net jei įvyko klaida
        try:
            if model_id and model_service:
                model_service.delete_model(model_id)
            
            if user_id and user_service:
                user_service.delete_user(user_id)
        except:
            pass
    
    finally:
        # Uždarome duomenų bazės sesiją
        db_session.close()
        logger.info("Duomenų bazės sesija uždaryta")

if __name__ == "__main__":
    main()