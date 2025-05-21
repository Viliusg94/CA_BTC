"""
Modelių treniravimo servisas.
Šis modulis teikia metodus darbui su modelių treniravimo procesu, integruotu su sesijų valdymu.
"""
import os
import time
import json
import logging
import threading
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from database.models.user_models import User
from services.model_service import ModelService
from services.session_manager_service import SessionManagerService

# Sukonfigūruojame logerį
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TrainingService:
    """
    Servisas skirtas modelių treniravimui.
    Integruoja sesijų valdymą su modelių treniravimo procesu.
    """
    
    def __init__(self, db_session: Session):
        """
        Inicializuoja TrainingService objektą.
        
        Args:
            db_session: SQLAlchemy sesijos objektas duomenų bazės operacijoms
        """
        self.db_session = db_session
        # Inicializuojame reikalingus servisus
        self.model_service = ModelService(db_session)
        self.session_manager = SessionManagerService(db_session)
        # Saugome aktyvius treniravimo procesus
        self.active_trainings = {}
        # Blokuojame prieigą prie aktyvių treniravimų sąrašo
        self.lock = threading.Lock()
    
    def start_training(self, user_id: str, model_id: str, training_params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Pradeda modelio treniravimo procesą.
        
        Args:
            user_id: Naudotojo ID
            model_id: Modelio ID
            training_params: Treniravimo parametrai (dataset_name, epochs, batch_size, kt.)
            
        Returns:
            dict: Pradėto treniravimo informacija arba None, jei įvyko klaida
        """
        try:
            # Tikriname, ar egzistuoja modelis
            model = self.model_service.get_model(model_id)
            if not model:
                logger.error(f"Modelis su ID {model_id} nerastas")
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
            
            # Pridedame treniravimo parametrus į metaduomenis
            for key, value in training_params.items():
                metadata[key] = value
            
            # Pradedame treniravimo sesiją
            session_result = self.session_manager.start_session(
                user_id=user_id,
                session_type="training",
                metadata=metadata
            )
            
            if not session_result:
                logger.error("Nepavyko pradėti treniravimo sesijos")
                return None
            
            # Gauname sukurtos sesijos ID
            session_id = session_result["user_session"]["id"]
            training_session_id = session_result.get("training_session", {}).get("id")
            
            logger.info(f"Pradėta treniravimo sesija: ID={session_id}")
            
            # Paruošiame treniravimo informaciją
            training_info = {
                "session_id": session_id,
                "training_session_id": training_session_id,
                "model_id": model_id,
                "user_id": user_id,
                "start_time": datetime.now(timezone.utc),
                "parameters": training_params,
                "status": "running",
                "progress": {
                    "current_epoch": 0,
                    "total_epochs": training_params.get("total_epochs", 1),
                    "history": []
                }
            }
            
            # Pradedame treniravimo procesą atskirame gije
            training_thread = threading.Thread(
                target=self._run_training_process,
                args=(session_id, training_info)
            )
            training_thread.daemon = True  # Leidžia programai išeiti net jei gija dar veikia
            
            # Registruojame aktyvų treniravimą
            with self.lock:
                self.active_trainings[session_id] = {
                    "thread": training_thread,
                    "info": training_info,
                    "stop_requested": False
                }
            
            # Pradedame treniravimo giją
            training_thread.start()
            
            # Grąžiname treniravimo informaciją
            return {
                "session_id": session_id,
                "training_session_id": training_session_id,
                "model_id": model_id,
                "model_name": model.name,
                "status": "running",
                "parameters": training_params
            }
            
        except Exception as e:
            logger.error(f"Klaida pradedant treniravimą: {str(e)}")
            return None
    
    def _run_training_process(self, session_id: str, training_info: Dict[str, Any]) -> None:
        """
        Vykdo modelio treniravimo procesą atskirame gije.
        
        Args:
            session_id: Sesijos ID
            training_info: Treniravimo informacija
        """
        try:
            logger.info(f"Pradedamas treniravimo procesas sesijai {session_id}")
            
            # Gaukime treniravimo parametrus
            model_id = training_info["model_id"]
            total_epochs = training_info["parameters"].get("total_epochs", 10)
            batch_size = training_info["parameters"].get("batch_size", 32)
            learning_rate = training_info["parameters"].get("learning_rate", 0.001)
            
            # Imituojame treniravimo procesą
            for epoch in range(1, total_epochs + 1):
                # Tikriname, ar buvo paprašyta sustabdyti treniravimą
                with self.lock:
                    if session_id in self.active_trainings and self.active_trainings[session_id]["stop_requested"]:
                        logger.info(f"Treniravimo procesas sesijai {session_id} sustabdytas")
                        
                        # Atnaujiname sesijos būseną
                        self.session_manager.update_session(session_id, {
                            "status": "stopped",
                            "training_status": "stopped"
                        })
                        
                        # Pašaliname iš aktyvių treniravimų
                        with self.lock:
                            if session_id in self.active_trainings:
                                del self.active_trainings[session_id]
                        
                        return
                
                # Imituojame treniravimo žingsnį
                time.sleep(0.5)  # Imituojame procesą, realybėje čia būtų tikras treniravimas
                
                # Generuojame dirbtines treniravimo metrikos
                loss = 1.0 / (epoch + 1) + 0.1
                accuracy = 0.5 + 0.05 * epoch if epoch < 10 else 0.95
                
                # Atnaujiname treniravimo progresą
                training_info["progress"]["current_epoch"] = epoch
                training_info["progress"]["history"].append({
                    "epoch": epoch,
                    "loss": loss,
                    "accuracy": accuracy
                })
                
                # Atnaujiname sesijos būseną duomenų bazėje
                self.session_manager.update_session(session_id, {
                    "current_epoch": epoch,
                    "training_status": "running",
                    "metadata": {
                        "loss": loss,
                        "accuracy": accuracy,
                        "progress": f"{epoch}/{total_epochs}"
                    }
                })
                
                logger.info(f"Treniravimas {session_id}: Epocha {epoch}/{total_epochs}, Loss: {loss:.4f}, Accuracy: {accuracy:.4f}")
            
            # Treniravimas baigtas, atnaujiname modelio būseną
            try:
                # Imituojame modelio išsaugojimą
                model_path = f"models/{model_id}_trained.h5"
                
                # Atnaujiname modelio informaciją
                self.model_service.update_model(model_id, {
                    "trained": True,
                    "last_training": datetime.now(timezone.utc).isoformat(),
                    "accuracy": training_info["progress"]["history"][-1]["accuracy"],
                    "file_path": model_path
                })
                
                logger.info(f"Modelis {model_id} sėkmingai apmokytas ir atnaujintas")
                
            except Exception as model_e:
                logger.error(f"Klaida atnaujinant modelio būseną: {str(model_e)}")
            
            # Baigiame treniravimo sesiją
            final_results = {
                "completed": True,
                "total_epochs": total_epochs,
                "final_loss": training_info["progress"]["history"][-1]["loss"],
                "final_accuracy": training_info["progress"]["history"][-1]["accuracy"],
                "training_time_seconds": (datetime.now(timezone.utc) - training_info["start_time"]).total_seconds()
            }
            
            self.session_manager.end_session(session_id, success=True, results=final_results)
            
            logger.info(f"Treniravimo procesas sesijai {session_id} baigtas sėkmingai")
            
        except Exception as e:
            logger.error(f"Klaida vykdant treniravimą: {str(e)}")
            
            # Bandome baigti sesiją su klaida
            try:
                self.session_manager.end_session(session_id, success=False, results={
                    "error": str(e),
                    "completed": False
                })
            except:
                pass
        
        finally:
            # Pašaliname iš aktyvių treniravimų
            with self.lock:
                if session_id in self.active_trainings:
                    del self.active_trainings[session_id]
    
    def stop_training(self, session_id: str) -> bool:
        """
        Sustabdo vykdomą treniravimo procesą.
        
        Args:
            session_id: Sesijos ID
            
        Returns:
            bool: Ar pavyko sustabdyti treniravimą
        """
        try:
            with self.lock:
                if session_id not in self.active_trainings:
                    logger.warning(f"Treniravimo sesija su ID {session_id} nerasta arba jau baigta")
                    return False
                
                # Pažymime, kad treniravimas turi būti sustabdytas
                self.active_trainings[session_id]["stop_requested"] = True
            
            logger.info(f"Pateiktas prašymas sustabdyti treniravimą sesijai {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Klaida stabdant treniravimą: {str(e)}")
            return False
    
    def get_training_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Gauna treniravimo būseną.
        
        Args:
            session_id: Sesijos ID
            
        Returns:
            dict: Treniravimo būsena arba None, jei sesija nerasta
        """
        try:
            # Pirmiausia tikriname aktyvius treniravimus
            with self.lock:
                if session_id in self.active_trainings:
                    training_info = self.active_trainings[session_id]["info"]
                    
                    return {
                        "session_id": session_id,
                        "model_id": training_info["model_id"],
                        "status": "running",
                        "progress": {
                            "current_epoch": training_info["progress"]["current_epoch"],
                            "total_epochs": training_info["progress"]["total_epochs"],
                            "percentage": round(100 * training_info["progress"]["current_epoch"] / training_info["progress"]["total_epochs"], 2)
                        },
                        "latest_metrics": training_info["progress"]["history"][-1] if training_info["progress"]["history"] else None,
                        "start_time": training_info["start_time"]
                    }
            
            # Jei nėra aktyvių treniravimų, gauname informaciją iš duomenų bazės
            session_info = self.session_manager.get_session_info(session_id)
            
            if not session_info:
                logger.warning(f"Treniravimo sesija su ID {session_id} nerasta")
                return None
            
            # Tikriname, ar tai treniravimo sesija
            if session_info["user_session"]["type"] != "training":
                logger.warning(f"Sesija su ID {session_id} nėra treniravimo tipo")
                return None
            
            # Gauname treniravimo sesiją
            if "training_session" not in session_info:
                logger.warning(f"Sesijai su ID {session_id} nerasta treniravimo informacija")
                return None
            
            training_session = session_info["training_session"]
            
            # Paruošiame būsenos informaciją
            return {
                "session_id": session_id,
                "model_id": training_session["model_id"],
                "status": training_session["status"],
                "progress": {
                    "current_epoch": training_session["current_epoch"],
                    "total_epochs": training_session["total_epochs"],
                    "percentage": round(100 * training_session["current_epoch"] / training_session["total_epochs"], 2) if training_session["total_epochs"] else 0
                },
                "start_time": session_info["user_session"]["start_time"],
                "end_time": session_info["user_session"]["end_time"]
            }
            
        except Exception as e:
            logger.error(f"Klaida gaunant treniravimo būseną: {str(e)}")
            return None
    
    def list_trainings(self, user_id: str = None, model_id: str = None, status: str = None, limit: int = 100, offset: int = 0) -> Optional[Dict[str, Any]]:
        """
        Gauna treniravimų sąrašą.
        
        Args:
            user_id: Filtravimas pagal naudotoją (pasirinktinai)
            model_id: Filtravimas pagal modelį (pasirinktinai)
            status: Filtravimas pagal būseną (pasirinktinai)
            limit: Maksimalus grąžinamų sesijų skaičius
            offset: Kiek sesijų praleisti (puslapis)
            
        Returns:
            dict: Treniravimų sąrašas arba None, jei įvyko klaida
        """
        try:
            # Gauname sesijas iš duomenų bazės
            if user_id:
                # Jei nurodytas naudotojas, gauname jo sesijas
                sessions = self.session_manager.list_user_sessions(
                    user_id=user_id,
                    session_type="training",
                    limit=limit,
                    offset=offset
                )
            else:
                # Kitaip gauname visas treniravimo sesijas (naudojant training_session_service)
                training_sessions = self.session_manager.db_session.query(self.session_manager.training_session_service.__class__.__model__)
                
                # Filtruojame pagal modelį
                if model_id:
                    training_sessions = training_sessions.filter_by(model_id=model_id)
                
                # Filtruojame pagal būseną
                if status:
                    training_sessions = training_sessions.filter_by(training_status=status)
                
                training_sessions = training_sessions.limit(limit).offset(offset).all()
                
                # Konvertuojame į reikiamą formatą
                sessions = {
                    "total": len(training_sessions),
                    "items": []
                }
                
                for ts in training_sessions:
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
                logger.warning("Nerasta jokių treniravimo sesijų")
                return {"total": 0, "items": []}
            
            # Papildome aktyvių treniravimų informacija
            with self.lock:
                active_session_ids = set(self.active_trainings.keys())
            
            # Pridedame aktualią treniravimo informaciją
            results = []
            for session in sessions["items"]:
                session_id = session["id"]
                session_info = self.session_manager.get_session_info(session_id)
                
                if not session_info or "training_session" not in session_info:
                    continue
                
                training_session = session_info["training_session"]
                
                # Tikriname, ar treniravimas aktyvus
                is_active_training = session_id in active_session_ids
                
                # Paruošiame treniravimo informaciją
                training_info = {
                    "session_id": session_id,
                    "model_id": training_session["model_id"],
                    "status": "running" if is_active_training else training_session["status"],
                    "progress": {
                        "current_epoch": training_session["current_epoch"],
                        "total_epochs": training_session["total_epochs"],
                        "percentage": round(100 * training_session["current_epoch"] / training_session["total_epochs"], 2) if training_session["total_epochs"] else 0
                    },
                    "start_time": session["start_time"],
                    "end_time": session["end_time"]
                }
                
                results.append(training_info)
            
            return {
                "total": len(results),
                "items": results
            }
            
        except Exception as e:
            logger.error(f"Klaida gaunant treniravimų sąrašą: {str(e)}")
            return None