"""
Simuliacijų vykdymo servisas.
Šis modulis teikia metodus darbui su Bitcoin kainų simuliavimo procesu, integruotu su sesijų valdymu.
"""
import os
import time
import json
import logging
import threading
import random
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from database.models.user_models import User
from services.model_service import ModelService
from services.session_manager_service import SessionManagerService

# Sukonfigūruojame logerį
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimulationService:
    """
    Servisas skirtas Bitcoin kainų simuliacijoms.
    Integruoja sesijų valdymą su simuliacijų vykdymo procesu.
    """
    
    def __init__(self, db_session: Session):
        """
        Inicializuoja SimulationService objektą.
        
        Args:
            db_session: SQLAlchemy sesijos objektas duomenų bazės operacijoms
        """
        self.db_session = db_session
        # Inicializuojame reikalingus servisus
        self.model_service = ModelService(db_session)
        self.session_manager = SessionManagerService(db_session)
        # Saugome aktyvias simuliacijas
        self.active_simulations = {}
        # Blokuojame prieigą prie aktyvių simuliacijų sąrašo
        self.lock = threading.Lock()
    
    def start_simulation(self, user_id: str, model_id: str, simulation_params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Pradeda Bitcoin kainos simuliavimo procesą.
        
        Args:
            user_id: Naudotojo ID
            model_id: Modelio ID
            simulation_params: Simuliacijos parametrai (start_date, duration, initial_price, kt.)
            
        Returns:
            dict: Pradėtos simuliacijos informacija arba None, jei įvyko klaida
        """
        try:
            # Tikriname, ar egzistuoja modelis
            model = self.model_service.get_model(model_id)
            if not model:
                logger.error(f"Modelis su ID {model_id} nerastas")
                return None
            
            # Tikriname, ar modelis apmokytas
            if not model.trained:
                logger.error(f"Modelis su ID {model_id} nėra apmokytas")
                return None
            
            # Tikriname, ar egzistuoja naudotojas
            user = self.db_session.query(User).filter(User.id == user_id).first()
            if not user:
                logger.error(f"Naudotojas su ID {user_id} nerastas")
                return None
            
            # Paruošiame metaduomenis sesijai
            metadata = {
                "model_id": model_id,
                "model_name": model.name,
                "model_type": model.type
            }
            
            # Pridedame simuliacijos parametrus į metaduomenis
            for key, value in simulation_params.items():
                metadata[key] = value
            
            # Pradedame testavimo sesiją
            session_result = self.session_manager.start_session(
                user_id=user_id,
                session_type="testing",
                metadata=metadata
            )
            
            if not session_result:
                logger.error("Nepavyko pradėti testavimo sesijos")
                return None
            
            # Gauname sukurtos sesijos ID
            session_id = session_result["user_session"]["id"]
            testing_session_id = session_result.get("testing_session", {}).get("id")
            
            logger.info(f"Pradėta simuliacijos sesija: ID={session_id}")
            
            # Paruošiame simuliacijos informaciją
            simulation_info = {
                "session_id": session_id,
                "testing_session_id": testing_session_id,
                "model_id": model_id,
                "user_id": user_id,
                "start_time": datetime.now(timezone.utc),
                "parameters": simulation_params,
                "status": "running",
                "progress": {
                    "current_step": 0,
                    "total_steps": simulation_params.get("steps", 30),
                    "price_history": []
                }
            }
            
            # Pradedame simuliacijos procesą atskirame gije
            simulation_thread = threading.Thread(
                target=self._run_simulation_process,
                args=(session_id, simulation_info)
            )
            simulation_thread.daemon = True  # Leidžia programai išeiti net jei gija dar veikia
            
            # Registruojame aktyvią simuliaciją
            with self.lock:
                self.active_simulations[session_id] = {
                    "thread": simulation_thread,
                    "info": simulation_info,
                    "stop_requested": False
                }
            
            # Pradedame simuliacijos giją
            simulation_thread.start()
            
            # Grąžiname simuliacijos informaciją
            return {
                "session_id": session_id,
                "testing_session_id": testing_session_id,
                "model_id": model_id,
                "model_name": model.name,
                "status": "running",
                "parameters": simulation_params
            }
            
        except Exception as e:
            logger.error(f"Klaida pradedant simuliaciją: {str(e)}")
            return None
    
    def _run_simulation_process(self, session_id: str, simulation_info: Dict[str, Any]) -> None:
        """
        Vykdo Bitcoin kainos simuliavimo procesą atskirame gije.
        
        Args:
            session_id: Sesijos ID
            simulation_info: Simuliacijos informacija
        """
        try:
            logger.info(f"Pradedamas simuliacijos procesas sesijai {session_id}")
            
            # Gaukime simuliacijos parametrus
            model_id = simulation_info["model_id"]
            total_steps = simulation_info["parameters"].get("steps", 30)
            initial_price = simulation_info["parameters"].get("initial_price", 30000)
            volatility = simulation_info["parameters"].get("volatility", 0.02)
            trend = simulation_info["parameters"].get("trend", 0.001)
            
            # Inicializuojame kainą
            current_price = initial_price
            simulation_info["progress"]["price_history"].append({
                "step": 0,
                "price": current_price,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            # Vykdome simuliaciją žingsnis po žingsnio
            for step in range(1, total_steps + 1):
                # Tikriname, ar buvo paprašyta sustabdyti simuliaciją
                with self.lock:
                    if session_id in self.active_simulations and self.active_simulations[session_id]["stop_requested"]:
                        logger.info(f"Simuliacijos procesas sesijai {session_id} sustabdytas")
                        
                        # Atnaujiname sesijos būseną
                        self.session_manager.update_session(session_id, {
                            "status": "stopped",
                            "testing_status": "stopped"
                        })
                        
                        # Pašaliname iš aktyvių simuliacijų
                        with self.lock:
                            if session_id in self.active_simulations:
                                del self.active_simulations[session_id]
                        
                        return
                
                # Imituojame modelio prognozę ir simuliacijos žingsnį
                time.sleep(0.2)  # Imituojame procesą, realybėje čia būtų tikras modelio prognozavimas
                
                # Skaičiuojame naują kainą (atsitiktinė simuliacija)
                price_change = current_price * (trend + volatility * np.random.randn())
                current_price = max(0, current_price + price_change)  # Kaina negali būti neigiama
                
                # Atnaujiname simuliacijos progresą
                simulation_info["progress"]["current_step"] = step
                simulation_info["progress"]["price_history"].append({
                    "step": step,
                    "price": current_price,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                
                # Atnaujiname sesijos būseną duomenų bazėje
                self.session_manager.update_session(session_id, {
                    "testing_status": "running",
                    "metadata": {
                        "current_step": step,
                        "total_steps": total_steps,
                        "current_price": current_price,
                        "progress": f"{step}/{total_steps}"
                    }
                })
                
                logger.info(f"Simuliacija {session_id}: Žingsnis {step}/{total_steps}, Kaina: ${current_price:.2f}")
            
            # Simuliacija baigta, analizuojame rezultatus
            price_history = simulation_info["progress"]["price_history"]
            starting_price = price_history[0]["price"]
            final_price = price_history[-1]["price"]
            price_change_pct = (final_price - starting_price) / starting_price * 100
            
            # Randame maksimalią ir minimalią kainas
            prices = [p["price"] for p in price_history]
            max_price = max(prices)
            min_price = min(prices)
            
            # Analizuojame kainos kryptį
            price_trend = "up" if final_price > starting_price else "down" if final_price < starting_price else "sideways"
            
            # Paruošiame simuliacijos rezultatus
            simulation_results = {
                "completed": True,
                "total_steps": total_steps,
                "starting_price": starting_price,
                "final_price": final_price,
                "price_change_pct": price_change_pct,
                "max_price": max_price,
                "min_price": min_price,
                "price_trend": price_trend,
                "volatility": volatility,
                "trend": trend,
                "simulation_time_seconds": (datetime.now(timezone.utc) - simulation_info["start_time"]).total_seconds(),
                "price_history": [{"step": p["step"], "price": p["price"]} for p in price_history]
            }
            
            # Baigiame testavimo sesiją
            self.session_manager.end_session(session_id, success=True, results=simulation_results)
            
            logger.info(f"Simuliacijos procesas sesijai {session_id} baigtas sėkmingai")
            logger.info(f"Simuliacijos rezultatai: Pradžios kaina ${starting_price:.2f}, "
                        f"Galutinė kaina ${final_price:.2f}, Pokytis {price_change_pct:.2f}%")
            
        except Exception as e:
            logger.error(f"Klaida vykdant simuliaciją: {str(e)}")
            
            # Bandome baigti sesiją su klaida
            try:
                self.session_manager.end_session(session_id, success=False, results={
                    "error": str(e),
                    "completed": False
                })
            except:
                pass
        
        finally:
            # Pašaliname iš aktyvių simuliacijų
            with self.lock:
                if session_id in self.active_simulations:
                    del self.active_simulations[session_id]
    
    def stop_simulation(self, session_id: str) -> bool:
        """
        Sustabdo vykdomą simuliacijos procesą.
        
        Args:
            session_id: Sesijos ID
            
        Returns:
            bool: Ar pavyko sustabdyti simuliaciją
        """
        try:
            with self.lock:
                if session_id not in self.active_simulations:
                    logger.warning(f"Simuliacijos sesija su ID {session_id} nerasta arba jau baigta")
                    return False
                
                # Pažymime, kad simuliacija turi būti sustabdyta
                self.active_simulations[session_id]["stop_requested"] = True
            
            logger.info(f"Pateiktas prašymas sustabdyti simuliaciją sesijai {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Klaida stabdant simuliaciją: {str(e)}")
            return False
    
    def get_simulation_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Gauna simuliacijos būseną.
        
        Args:
            session_id: Sesijos ID
            
        Returns:
            dict: Simuliacijos būsena arba None, jei sesija nerasta
        """
        try:
            # Pirmiausia tikriname aktyvias simuliacijas
            with self.lock:
                if session_id in self.active_simulations:
                    simulation_info = self.active_simulations[session_id]["info"]
                    
                    current_step = simulation_info["progress"]["current_step"]
                    total_steps = simulation_info["progress"]["total_steps"]
                    price_history = simulation_info["progress"]["price_history"]
                    
                    return {
                        "session_id": session_id,
                        "model_id": simulation_info["model_id"],
                        "status": "running",
                        "progress": {
                            "current_step": current_step,
                            "total_steps": total_steps,
                            "percentage": round(100 * current_step / total_steps, 2)
                        },
                        "current_price": price_history[-1]["price"] if price_history else None,
                        "price_history": price_history[-10:] if len(price_history) > 10 else price_history,  # Grąžiname tik paskutinius 10 įrašų
                        "start_time": simulation_info["start_time"]
                    }
            
            # Jei nėra aktyvių simuliacijų, gauname informaciją iš duomenų bazės
            session_info = self.session_manager.get_session_info(session_id)
            
            if not session_info:
                logger.warning(f"Simuliacijos sesija su ID {session_id} nerasta")
                return None
            
            # Tikriname, ar tai testavimo sesija
            if session_info["user_session"]["type"] != "testing":
                logger.warning(f"Sesija su ID {session_id} nėra testavimo tipo")
                return None
            
            # Gauname testavimo sesiją
            if "testing_session" not in session_info:
                logger.warning(f"Sesijai su ID {session_id} nerasta testavimo informacija")
                return None
            
            testing_session = session_info["testing_session"]
            
            # Tikriname, ar yra rezultatai
            if testing_session["results"]:
                try:
                    results = json.loads(testing_session["results"]) if isinstance(testing_session["results"], str) else testing_session["results"]
                    
                    # Paruošiame būsenos informaciją
                    return {
                        "session_id": session_id,
                        "model_id": testing_session["model_id"],
                        "status": testing_session["status"],
                        "progress": {
                            "current_step": results.get("total_steps", 0),
                            "total_steps": results.get("total_steps", 0),
                            "percentage": 100
                        },
                        "result_summary": {
                            "starting_price": results.get("starting_price"),
                            "final_price": results.get("final_price"),
                            "price_change_pct": results.get("price_change_pct"),
                            "price_trend": results.get("price_trend"),
                            "simulation_time": results.get("simulation_time_seconds")
                        },
                        "price_history": results.get("price_history", [])[-10:],  # Paskutiniai 10 įrašų
                        "start_time": session_info["user_session"]["start_time"],
                        "end_time": session_info["user_session"]["end_time"]
                    }
                except Exception as e:
                    logger.error(f"Klaida apdorojant rezultatus: {str(e)}")
            
            # Jei nėra rezultatų, grąžiname bazinę informaciją
            return {
                "session_id": session_id,
                "model_id": testing_session["model_id"],
                "status": testing_session["status"],
                "start_time": session_info["user_session"]["start_time"],
                "end_time": session_info["user_session"]["end_time"]
            }
            
        except Exception as e:
            logger.error(f"Klaida gaunant simuliacijos būseną: {str(e)}")
            return None
    
    def list_simulations(self, user_id: str = None, model_id: str = None, status: str = None, limit: int = 100, offset: int = 0) -> Optional[Dict[str, Any]]:
        """
        Gauna simuliacijų sąrašą.
        
        Args:
            user_id: Filtravimas pagal naudotoją (pasirinktinai)
            model_id: Filtravimas pagal modelį (pasirinktinai)
            status: Filtravimas pagal būseną (pasirinktinai)
            limit: Maksimalus grąžinamų sesijų skaičius
            offset: Kiek sesijų praleisti (puslapis)
            
        Returns:
            dict: Simuliacijų sąrašas arba None, jei įvyko klaida
        """
        try:
            # Gauname sesijas iš duomenų bazės
            if user_id:
                # Jei nurodytas naudotojas, gauname jo sesijas
                sessions = self.session_manager.list_user_sessions(
                    user_id=user_id,
                    session_type="testing",
                    limit=limit,
                    offset=offset
                )
            else:
                # Kitaip gauname visas testavimo sesijas (naudojant testing_session_service)
                testing_sessions = self.session_manager.db_session.query(self.session_manager.testing_session_service.__class__.__model__)
                
                # Filtruojame pagal modelį
                if model_id:
                    testing_sessions = testing_sessions.filter_by(model_id=model_id)
                
                # Filtruojame pagal būseną
                if status:
                    testing_sessions = testing_sessions.filter_by(testing_status=status)
                
                testing_sessions = testing_sessions.limit(limit).offset(offset).all()
                
                # Konvertuojame į reikiamą formatą
                sessions = {
                    "total": len(testing_sessions),
                    "items": []
                }
                
                for ts in testing_sessions:
                    user_session = ts.session
                    sessions["items"].append({
                        "id": user_session.id,
                        "type": user_session.session_type,
                        "start_time": user_session.start_time,
                        "end_time": user_session.end_time,
                        "is_active": user_session.is_active,
                        "status": user_session.status
                    })
            
            if not sessions:
                logger.warning("Nerasta jokių simuliacijos sesijų")
                return {"total": 0, "items": []}
            
            # Papildome aktyvių simuliacijų informacija
            with self.lock:
                active_session_ids = set(self.active_simulations.keys())
            
            # Pridedame aktualią simuliacijos informaciją
            results = []
            for session in sessions["items"]:
                session_id = session["id"]
                
                # Gauname detalią informaciją
                simulation_status = self.get_simulation_status(session_id)
                
                if simulation_status:
                    results.append(simulation_status)
            
            return {
                "total": len(results),
                "items": results
            }
            
        except Exception as e:
            logger.error(f"Klaida gaunant simuliacijų sąrašą: {str(e)}")
            return None