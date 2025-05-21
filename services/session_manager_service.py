"""
Bendras sesijų valdymo servisas.
Šis modulis teikia aukšto lygio metodus darbui su įvairių tipų naudotojų sesijomis.
"""
import logging
from typing import Optional, Dict, Any, Union
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from database.models.user_models import UserSession, TrainingSession, TestingSession
from services.session_service import SessionService
from services.training_session_service import TrainingSessionService
from services.testing_session_service import TestingSessionService

# Sukonfigūruojame logerį
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SessionManagerService:
    """
    Aukšto lygio servisas darbui su naudotojų sesijomis.
    Leidžia valdyti skirtingų tipų sesijas per vieną sąsają.
    """
    
    def __init__(self, db_session: Session):
        """
        Inicializuoja SessionManagerService objektą.
        
        Args:
            db_session: SQLAlchemy sesijos objektas duomenų bazės operacijoms
        """
        self.db_session = db_session
        # Inicializuojame reikalingus servisus
        self.session_service = SessionService(db_session)
        self.training_session_service = TrainingSessionService(db_session)
        self.testing_session_service = TestingSessionService(db_session)
    
    def start_session(self, user_id: str, session_type: str, metadata: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """
        Pradeda naują naudotojo sesiją.
        
        Args:
            user_id: Naudotojo ID
            session_type: Sesijos tipas (training/testing/general)
            metadata: Papildomi sesijos duomenys
            
        Returns:
            dict: Sukurtos sesijos informacija arba None, jei įvyko klaida
        """
        try:
            # Tikriname, ar tinkamas sesijos tipas
            if session_type not in ["training", "testing", "general"]:
                logger.error(f"Netinkamas sesijos tipas: {session_type}")
                return None
            
            # Paruošiame pradinius sesijos duomenis
            session_data = {
                "user_id": user_id,
                "session_type": session_type,
                "is_active": True,
                "status": "active",
                "start_time": datetime.now(timezone.utc)
            }
            
            # Jei yra papildomų duomenų, pridedame juos
            if metadata:
                session_data["metadata"] = metadata
            
            # Sukuriame bazinę naudotojo sesiją
            user_session = self.session_service.create_session(session_data)
            
            if not user_session:
                logger.error(f"Nepavyko sukurti naudotojo sesijos tipo {session_type}")
                return None
            
            # Jei tai treniravimo sesija, sukuriame susietą treniravimo sesiją
            if session_type == "training":
                # Paruošiame pradinius treniravimo sesijos duomenis
                training_data = {
                    "training_status": "pending"
                }
                
                # Jei metadata turi modelio ID, pridedame jį
                if metadata and "model_id" in metadata:
                    training_data["model_id"] = metadata["model_id"]
                
                # Pridedame kitus treniravimo parametrus iš metadata
                if metadata:
                    for key in ["dataset_name", "learning_rate", "batch_size", "total_epochs"]:
                        if key in metadata:
                            training_data[key] = metadata[key]
                
                # Sukuriame treniravimo sesiją
                training_session = self.training_session_service.create_training_session(
                    user_session.id, training_data
                )
                
                if not training_session:
                    # Jei nepavyko sukurti treniravimo sesijos, ištriname naudotojo sesiją
                    self.session_service.delete_session(user_session.id)
                    logger.error("Nepavyko sukurti treniravimo sesijos, naudotojo sesija ištrinta")
                    return None
                
                # Grąžiname abiejų sesijų informaciją
                return {
                    "user_session": {
                        "id": user_session.id,
                        "type": user_session.session_type,
                        "start_time": user_session.start_time,
                        "status": user_session.status
                    },
                    "training_session": {
                        "id": training_session.id,
                        "model_id": training_session.model_id,
                        "status": training_session.training_status
                    }
                }
            
            # Jei tai testavimo sesija, sukuriame susietą testavimo sesiją
            elif session_type == "testing":
                # Paruošiame pradinius testavimo sesijos duomenis
                testing_data = {
                    "testing_status": "pending"
                }
                
                # Jei metadata turi modelio ID, pridedame jį
                if metadata and "model_id" in metadata:
                    testing_data["model_id"] = metadata["model_id"]
                
                # Pridedame kitus testavimo parametrus iš metadata
                if metadata:
                    for key in ["dataset_name", "test_type", "test_params"]:
                        if key in metadata:
                            testing_data[key] = metadata[key]
                
                # Sukuriame testavimo sesiją
                testing_session = self.testing_session_service.create_testing_session(
                    user_session.id, testing_data
                )
                
                if not testing_session:
                    # Jei nepavyko sukurti testavimo sesijos, ištriname naudotojo sesiją
                    self.session_service.delete_session(user_session.id)
                    logger.error("Nepavyko sukurti testavimo sesijos, naudotojo sesija ištrinta")
                    return None
                
                # Grąžiname abiejų sesijų informaciją
                return {
                    "user_session": {
                        "id": user_session.id,
                        "type": user_session.session_type,
                        "start_time": user_session.start_time,
                        "status": user_session.status
                    },
                    "testing_session": {
                        "id": testing_session.id,
                        "model_id": testing_session.model_id,
                        "status": testing_session.testing_status
                    }
                }
            
            # Jei tai bendro tipo sesija, grąžiname tik jos informaciją
            else:
                return {
                    "user_session": {
                        "id": user_session.id,
                        "type": user_session.session_type,
                        "start_time": user_session.start_time,
                        "status": user_session.status
                    }
                }
                
        except Exception as e:
            logger.error(f"Klaida pradedant sesiją: {str(e)}")
            return None
    
    def update_session(self, session_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Atnaujina esamą sesiją.
        
        Args:
            session_id: Naudotojo sesijos ID
            update_data: Duomenys, kuriuos reikia atnaujinti
            
        Returns:
            dict: Atnaujintos sesijos informacija arba None, jei įvyko klaida
        """
        try:
            # Gauname naudotojo sesiją
            user_session = self.session_service.get_session(session_id)
            
            if not user_session:
                logger.error(f"Sesija su ID {session_id} nerasta")
                return None
            
            # Tikriname, ar sesija aktyvi
            if not user_session.is_active:
                logger.warning(f"Bandoma atnaujinti neaktyvią sesiją {session_id}")
                return None
            
            # Ruošiame sesijos atnaujinimo duomenis
            session_update_data = {}
            
            # Kopijuojame bendrus atnaujinimo duomenis
            for key in ["metadata", "ip_address", "user_agent"]:
                if key in update_data:
                    session_update_data[key] = update_data[key]
            
            # Jei yra status, atnaujiname jį
            if "status" in update_data:
                session_update_data["status"] = update_data["status"]
            
            # Atnaujiname naudotojo sesiją
            updated_user_session = self.session_service.update_session(session_id, session_update_data)
            
            if not updated_user_session:
                logger.error(f"Nepavyko atnaujinti naudotojo sesijos {session_id}")
                return None
            
            # Jei tai treniravimo sesija, atnaujiname ir ją
            if user_session.session_type == "training":
                # Gauname treniravimo sesiją
                training_session = self.training_session_service.get_training_session_by_user_session(session_id)
                
                if not training_session:
                    logger.error(f"Treniravimo sesija nerasta naudotojo sesijai {session_id}")
                    return None
                
                # Ruošiame treniravimo sesijos atnaujinimo duomenis
                training_update_data = {}
                
                # Kopijuojame treniravimo specifinius atnaujinimo duomenis
                for key in ["current_epoch", "learning_rate", "batch_size"]:
                    if key in update_data:
                        training_update_data[key] = update_data[key]
                
                # Jei yra training_status, atnaujiname jį
                if "training_status" in update_data:
                    training_update_data["training_status"] = update_data["training_status"]
                
                # Atnaujiname treniravimo sesiją
                updated_training_session = self.training_session_service.update_training_session(
                    training_session.id, training_update_data
                )
                
                if not updated_training_session:
                    logger.error(f"Nepavyko atnaujinti treniravimo sesijos {training_session.id}")
                    return None
                
                # Grąžiname atnaujintų sesijų informaciją
                return {
                    "user_session": {
                        "id": updated_user_session.id,
                        "type": updated_user_session.session_type,
                        "start_time": updated_user_session.start_time,
                        "status": updated_user_session.status
                    },
                    "training_session": {
                        "id": updated_training_session.id,
                        "model_id": updated_training_session.model_id,
                        "status": updated_training_session.training_status,
                        "current_epoch": updated_training_session.current_epoch
                    }
                }
            
            # Jei tai testavimo sesija, atnaujiname ir ją
            elif user_session.session_type == "testing":
                # Gauname testavimo sesiją
                testing_session = self.testing_session_service.get_testing_session_by_user_session(session_id)
                
                if not testing_session:
                    logger.error(f"Testavimo sesija nerasta naudotojo sesijai {session_id}")
                    return None
                
                # Ruošiame testavimo sesijos atnaujinimo duomenis
                testing_update_data = {}
                
                # Kopijuojame testavimo specifinius atnaujinimo duomenis
                for key in ["test_params", "results"]:
                    if key in update_data:
                        testing_update_data[key] = update_data[key]
                
                # Jei yra testing_status, atnaujiname jį
                if "testing_status" in update_data:
                    testing_update_data["testing_status"] = update_data["testing_status"]
                
                # Atnaujiname testavimo sesiją
                updated_testing_session = self.testing_session_service.update_testing_session(
                    testing_session.id, testing_update_data
                )
                
                if not updated_testing_session:
                    logger.error(f"Nepavyko atnaujinti testavimo sesijos {testing_session.id}")
                    return None
                
                # Grąžiname atnaujintų sesijų informaciją
                return {
                    "user_session": {
                        "id": updated_user_session.id,
                        "type": updated_user_session.session_type,
                        "start_time": updated_user_session.start_time,
                        "status": updated_user_session.status
                    },
                    "testing_session": {
                        "id": updated_testing_session.id,
                        "model_id": updated_testing_session.model_id,
                        "status": updated_testing_session.testing_status
                    }
                }
            
            # Jei tai bendro tipo sesija, grąžiname tik jos informaciją
            else:
                return {
                    "user_session": {
                        "id": updated_user_session.id,
                        "type": updated_user_session.session_type,
                        "start_time": updated_user_session.start_time,
                        "status": updated_user_session.status
                    }
                }
        
        except Exception as e:
            logger.error(f"Klaida atnaujinant sesiją: {str(e)}")
            return None
    
    def end_session(self, session_id: str, success: bool = True, results: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """
        Baigia naudotojo sesiją.
        
        Args:
            session_id: Naudotojo sesijos ID
            success: Ar sesija baigta sėkmingai
            results: Sesijos rezultatai (jei yra)
            
        Returns:
            dict: Baigtos sesijos informacija arba None, jei įvyko klaida
        """
        try:
            # Gauname naudotojo sesiją
            user_session = self.session_service.get_session(session_id)
            
            if not user_session:
                logger.error(f"Sesija su ID {session_id} nerasta")
                return None
            
            # Tikriname, ar sesija jau baigta
            if not user_session.is_active:
                logger.warning(f"Sesija {session_id} jau baigta")
                return {
                    "user_session": {
                        "id": user_session.id,
                        "type": user_session.session_type,
                        "start_time": user_session.start_time,
                        "end_time": user_session.end_time,
                        "status": user_session.status
                    }
                }
            
            # Baigtos sesijos duomenys
            session_end_data = {
                "is_active": False,
                "end_time": datetime.now(timezone.utc),
                "status": "completed" if success else "failed"
            }
            
            # Baigiame naudotojo sesiją
            ended_user_session = self.session_service.end_session(session_id)
            
            if not ended_user_session:
                logger.error(f"Nepavyko baigti naudotojo sesijos {session_id}")
                return None
            
            result_data = {}
            
            # Jei tai treniravimo sesija, baigiame ir ją
            if user_session.session_type == "training":
                # Gauname treniravimo sesiją
                training_session = self.training_session_service.get_training_session_by_user_session(session_id)
                
                if not training_session:
                    logger.error(f"Treniravimo sesija nerasta naudotojo sesijai {session_id}")
                else:
                    # Baigiame treniravimo sesiją
                    ended_training_session = self.training_session_service.complete_training(training_session.id)
                    
                    if not ended_training_session:
                        logger.error(f"Nepavyko baigti treniravimo sesijos {training_session.id}")
                    else:
                        result_data["training_session"] = {
                            "id": ended_training_session.id,
                            "model_id": ended_training_session.model_id,
                            "status": ended_training_session.training_status,
                            "current_epoch": ended_training_session.current_epoch,
                            "total_epochs": ended_training_session.total_epochs
                        }
            
            # Jei tai testavimo sesija, baigiame ir ją
            elif user_session.session_type == "testing":
                # Gauname testavimo sesiją
                testing_session = self.testing_session_service.get_testing_session_by_user_session(session_id)
                
                if not testing_session:
                    logger.error(f"Testavimo sesija nerasta naudotojo sesijai {session_id}")
                else:
                    # Jei yra rezultatai, išsaugome juos
                    if results:
                        ended_testing_session = self.testing_session_service.save_test_results(
                            testing_session.id, results, success
                        )
                    else:
                        # Atnaujinama būsena be rezultatų
                        status_update = {"testing_status": "completed" if success else "failed"}
                        ended_testing_session = self.testing_session_service.update_testing_session(
                            testing_session.id, status_update
                        )
                    
                    if not ended_testing_session:
                        logger.error(f"Nepavyko baigti testavimo sesijos {testing_session.id}")
                    else:
                        result_data["testing_session"] = {
                            "id": ended_testing_session.id,
                            "model_id": ended_testing_session.model_id,
                            "status": ended_testing_session.testing_status,
                            "success": ended_testing_session.success
                        }
            
            # Pridedame naudotojo sesijos informaciją į rezultatus
            result_data["user_session"] = {
                "id": ended_user_session.id,
                "type": ended_user_session.session_type,
                "start_time": ended_user_session.start_time,
                "end_time": ended_user_session.end_time,
                "status": ended_user_session.status
            }
            
            return result_data
            
        except Exception as e:
            logger.error(f"Klaida baigiant sesiją: {str(e)}")
            return None
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Gauna išsamią informaciją apie sesiją.
        
        Args:
            session_id: Naudotojo sesijos ID
            
        Returns:
            dict: Sesijos informacija arba None, jei įvyko klaida
        """
        try:
            # Gauname naudotojo sesiją
            user_session = self.session_service.get_session(session_id)
            
            if not user_session:
                logger.error(f"Sesija su ID {session_id} nerasta")
                return None
            
            # Paruošiame pradinį rezultatų žodyną
            result = {
                "user_session": {
                    "id": user_session.id,
                    "user_id": user_session.user_id,
                    "type": user_session.session_type,
                    "start_time": user_session.start_time,
                    "end_time": user_session.end_time,
                    "is_active": user_session.is_active,
                    "status": user_session.status
                }
            }
            
            # Jei tai treniravimo sesija, pridedame jos informaciją
            if user_session.session_type == "training":
                training_session = self.training_session_service.get_training_session_by_user_session(session_id)
                
                if training_session:
                    result["training_session"] = {
                        "id": training_session.id,
                        "model_id": training_session.model_id,
                        "dataset_name": training_session.dataset_name,
                        "current_epoch": training_session.current_epoch,
                        "total_epochs": training_session.total_epochs,
                        "learning_rate": training_session.learning_rate,
                        "status": training_session.training_status
                    }
            
            # Jei tai testavimo sesija, pridedame jos informaciją
            elif user_session.session_type == "testing":
                testing_session = self.testing_session_service.get_testing_session_by_user_session(session_id)
                
                if testing_session:
                    result["testing_session"] = {
                        "id": testing_session.id,
                        "model_id": testing_session.model_id,
                        "dataset_name": testing_session.dataset_name,
                        "test_type": testing_session.test_type,
                        "status": testing_session.testing_status,
                        "success": testing_session.success
                    }
                    
                    # Jei yra rezultatai, pridedame juos
                    if testing_session.results:
                        import json
                        try:
                            result["testing_session"]["results"] = json.loads(testing_session.results)
                        except:
                            result["testing_session"]["results"] = testing_session.results
            
            return result
            
        except Exception as e:
            logger.error(f"Klaida gaunant sesijos informaciją: {str(e)}")
            return None
    
    def list_user_sessions(self, user_id: str, session_type: str = None, active_only: bool = False, limit: int = 100, offset: int = 0) -> Optional[Dict[str, Any]]:
        """
        Gauna naudotojo sesijų sąrašą.
        
        Args:
            user_id: Naudotojo ID
            session_type: Filtravimas pagal sesijos tipą (pasirinktinai)
            active_only: Ar grąžinti tik aktyvias sesijas
            limit: Maksimalus grąžinamų sesijų skaičius
            offset: Kiek sesijų praleisti (puslapis)
            
        Returns:
            dict: Sesijų sąrašas arba None, jei įvyko klaida
        """
        try:
            # Gauname naudotojo sesijas
            sessions = self.session_service.list_user_sessions(user_id, active_only, limit, offset)
            
            # Jei nurodytas sesijos tipas, filtruojame pagal jį
            if session_type:
                sessions = [s for s in sessions if s.session_type == session_type]
            
            # Paruošiame rezultatų žodyną
            result = {
                "total": len(sessions),
                "items": []
            }
            
            # Pridedame kiekvienos sesijos informaciją
            for session in sessions:
                session_info = {
                    "id": session.id,
                    "type": session.session_type,
                    "start_time": session.start_time,
                    "end_time": session.end_time,
                    "is_active": session.is_active,
                    "status": session.status
                }
                
                result["items"].append(session_info)
            
            return result
            
        except Exception as e:
            logger.error(f"Klaida gaunant naudotojo sesijų sąrašą: {str(e)}")
            return None