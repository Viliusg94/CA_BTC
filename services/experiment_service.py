"""
Eksperimentų servisas.
Šis modulis teikia funkcijas darbui su eksperimentais - kūrimui, atnaujinimui ir paieškai.
"""
import json
import logging
import os
import csv
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Union
from sqlalchemy.orm import Session
from sqlalchemy import or_

# Importuojame eksperimento modelį
from database.models.experiment_models import Experiment, ExperimentResult

# Sukuriame žurnalininką
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ExperimentService:
    """
    Eksperimentų serviso klasė.
    Skirta darbui su eksperimentais - jų kūrimui, atnaujinimui ir paieškai.
    """
    
    def __init__(self, db: Session):
        """
        Inicializuoja eksperimentų servisą su duomenų bazės sesija.
        
        Args:
            db: SQLAlchemy sesijos objektas
        """
        self.db = db
        logger.info("Eksperimentų servisas inicializuotas")
    
    def create_experiment(self, name: str, creator_id: Optional[str] = None, 
                         description: Optional[str] = None, 
                         metadata: Optional[Dict[str, Any]] = None) -> Experiment:
        """
        Sukuria naują eksperimentą duomenų bazėje.
        
        Args:
            name: Eksperimento pavadinimas
            creator_id: Eksperimento kūrėjo ID (neprivalomas)
            description: Eksperimento aprašymas (neprivalomas)
            metadata: Papildoma informacija apie eksperimentą (neprivalomas)
            
        Returns:
            Experiment: Sukurtas eksperimento objektas
        """
        try:
            # Konvertuojame metadata į JSON, jei pateikta
            metadata_json = json.dumps(metadata) if metadata else None
            
            # Sukuriame naują eksperimento įrašą
            experiment = Experiment(
                name=name,
                creator_id=creator_id,
                description=description,
                metadata=metadata_json,
                status="naujas"  # Pradinis statusas
            )
            
            # Įrašome į duomenų bazę
            self.db.add(experiment)
            self.db.commit()
            self.db.refresh(experiment)
            
            logger.info(f"Sukurtas naujas eksperimentas: {experiment.name} (ID: {experiment.id})")
            return experiment
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Klaida kuriant eksperimentą: {str(e)}")
            raise
    
    def update_experiment_status(self, experiment_id: str, status: str) -> Experiment:
        """
        Atnaujina eksperimento statusą.
        
        Args:
            experiment_id: Eksperimento ID
            status: Naujas statusas (pvz., "vykdomas", "baigtas", "nutrauktas")
            
        Returns:
            Experiment: Atnaujintas eksperimento objektas
        """
        try:
            # Randame eksperimentą pagal ID
            experiment = self.db.query(Experiment).filter(Experiment.id == experiment_id).first()
            
            if not experiment:
                logger.error(f"Eksperimentas su ID {experiment_id} nerastas")
                raise ValueError(f"Eksperimentas su ID {experiment_id} nerastas")
            
            # Atnaujiname statusą
            experiment.status = status
            experiment.updated_at = datetime.now(timezone.utc)
            
            # Įrašome pakeitimus
            self.db.commit()
            self.db.refresh(experiment)
            
            logger.info(f"Eksperimento {experiment.name} (ID: {experiment.id}) statusas pakeistas į '{status}'")
            return experiment
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Klaida atnaujinant eksperimento statusą: {str(e)}")
            raise
    
    def get_experiment(self, experiment_id: str) -> Optional[Experiment]:
        """
        Gauna eksperimentą pagal ID.
        
        Args:
            experiment_id: Eksperimento ID
            
        Returns:
            Optional[Experiment]: Eksperimento objektas arba None, jei nerastas
        """
        try:
            experiment = self.db.query(Experiment).filter(Experiment.id == experiment_id).first()
            
            if not experiment:
                logger.warning(f"Eksperimentas su ID {experiment_id} nerastas")
                return None
            
            logger.info(f"Rastas eksperimentas: {experiment.name} (ID: {experiment.id})")
            return experiment
            
        except Exception as e:
            logger.error(f"Klaida gaunant eksperimentą: {str(e)}")
            raise
    
    def get_all_experiments(self, limit: int = 100, offset: int = 0) -> List[Experiment]:
        """
        Gauna visus eksperimentus su puslapiavimu.
        
        Args:
            limit: Maksimalus grąžinamų eksperimentų skaičius
            offset: Kiek eksperimentų praleisti
            
        Returns:
            List[Experiment]: Eksperimentų sąrašas
        """
        try:
            experiments = self.db.query(Experiment).order_by(
                Experiment.updated_at.desc()
            ).offset(offset).limit(limit).all()
            
            logger.info(f"Gauta {len(experiments)} eksperimentų")
            return experiments
            
        except Exception as e:
            logger.error(f"Klaida gaunant eksperimentų sąrašą: {str(e)}")
            raise
    
    def search_experiments(self, search_term: Optional[str] = None, 
                          status: Optional[str] = None, 
                          creator_id: Optional[str] = None,
                          limit: int = 100) -> List[Experiment]:
        """
        Ieško eksperimentų pagal pateiktus kriterijus.
        
        Args:
            search_term: Paieškos terminas pavadinime ar aprašyme (neprivalomas)
            status: Eksperimento statusas (neprivalomas)
            creator_id: Eksperimento kūrėjo ID (neprivalomas)
            limit: Maksimalus grąžinamų eksperimentų skaičius
            
        Returns:
            List[Experiment]: Eksperimentų, atitinkančių paieškos kriterijus, sąrašas
        """
        try:
            # Pradedame užklausą
            query = self.db.query(Experiment)
            
            # Pridedame filtrus, jei jie pateikti
            if search_term:
                search_filter = or_(
                    Experiment.name.ilike(f"%{search_term}%"),
                    Experiment.description.ilike(f"%{search_term}%")
                )
                query = query.filter(search_filter)
            
            if status:
                query = query.filter(Experiment.status == status)
            
            if creator_id:
                query = query.filter(Experiment.creator_id == creator_id)
            
            # Vykdome užklausą su rikiavimų pagal naujausius ir limitu
            experiments = query.order_by(Experiment.updated_at.desc()).limit(limit).all()
            
            logger.info(f"Rasta {len(experiments)} eksperimentų pagal pateiktus paieškos kriterijus")
            return experiments
            
        except Exception as e:
            logger.error(f"Klaida ieškant eksperimentų: {str(e)}")
            raise
    
    def update_experiment(self, experiment_id: str, 
                         name: Optional[str] = None,
                         description: Optional[str] = None,
                         metadata: Optional[Dict[str, Any]] = None) -> Experiment:
        """
        Atnaujina eksperimento duomenis.
        
        Args:
            experiment_id: Eksperimento ID
            name: Naujas eksperimento pavadinimas (neprivalomas)
            description: Naujas eksperimento aprašymas (neprivalomas)
            metadata: Nauji papildomi duomenys (neprivalomas)
            
        Returns:
            Experiment: Atnaujintas eksperimento objektas
        """
        try:
            # Randame eksperimentą pagal ID
            experiment = self.db.query(Experiment).filter(Experiment.id == experiment_id).first()
            
            if not experiment:
                logger.error(f"Eksperimentas su ID {experiment_id} nerastas")
                raise ValueError(f"Eksperimentas su ID {experiment_id} nerastas")
            
            # Atnaujiname laukus, jei jie pateikti
            if name:
                experiment.name = name
            
            if description:
                experiment.description = description
            
            if metadata:
                # Jei jau yra metadata, bandome sujungti su naujais
                if experiment.metadata:
                    try:
                        existing_metadata = json.loads(experiment.metadata)
                        # Sujungiame su naujais duomenimis
                        existing_metadata.update(metadata)
                        experiment.metadata = json.dumps(existing_metadata)
                    except json.JSONDecodeError:
                        # Jei neįmanoma išanalizuoti esamos metadata, tiesiog pakeičiame
                        experiment.metadata = json.dumps(metadata)
                else:
                    experiment.metadata = json.dumps(metadata)
            
            # Atnaujiname laiko žymą
            experiment.updated_at = datetime.now(timezone.utc)
            
            # Įrašome pakeitimus
            self.db.commit()
            self.db.refresh(experiment)
            
            logger.info(f"Eksperimentas {experiment.name} (ID: {experiment.id}) atnaujintas")
            return experiment
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Klaida atnaujinant eksperimentą: {str(e)}")
            raise
    
    def delete_experiment(self, experiment_id: str) -> bool:
        """
        Ištrina eksperimentą pagal ID.
        
        Args:
            experiment_id: Eksperimento ID
            
        Returns:
            bool: True, jei eksperimentas buvo sėkmingai ištrintas, False kitais atvejais
        """
        try:
            # Randame eksperimentą pagal ID
            experiment = self.db.query(Experiment).filter(Experiment.id == experiment_id).first()
            
            if not experiment:
                logger.warning(f"Eksperimentas su ID {experiment_id} nerastas, negalima ištrinti")
                return False
            
            # Ištriname eksperimentą
            self.db.delete(experiment)
            self.db.commit()
            
            logger.info(f"Eksperimentas {experiment.name} (ID: {experiment.id}) ištrintas")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Klaida ištrinant eksperimentą: {str(e)}")
            raise

    def save_hyperparameters(self, experiment_id: str, hyperparameters: Dict[str, Any]) -> Experiment:
        """
        Išsaugo eksperimento hiperparametrus.
        
        Args:
            experiment_id: Eksperimento ID
            hyperparameters: Hiperparametrų žodynas
            
        Returns:
            Experiment: Atnaujintas eksperimento objektas
        """
        try:
            # Randame eksperimentą pagal ID
            experiment = self.db.query(Experiment).filter(Experiment.id == experiment_id).first()
            
            if not experiment:
                logger.error(f"Eksperimentas su ID {experiment_id} nerastas")
                raise ValueError(f"Eksperimentas su ID {experiment_id} nerastas")
            
            # Gauname esamus metaduomenis arba sukuriame naują žodyną
            metadata = {}
            if experiment.metadata:
                try:
                    metadata = json.loads(experiment.metadata)
                except json.JSONDecodeError:
                    metadata = {}
            
            # Pridedame hiperparametrus į metaduomenis
            metadata["hyperparameters"] = hyperparameters
            
            # Atnaujiname metaduomenis
            experiment.metadata = json.dumps(metadata)
            experiment.updated_at = datetime.now(timezone.utc)
            
            # Įrašome pakeitimus
            self.db.commit()
            self.db.refresh(experiment)
            
            logger.info(f"Išsaugoti hiperparametrai eksperimentui {experiment.name} (ID: {experiment.id})")
            return experiment
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Klaida išsaugant hiperparametrus: {str(e)}")
            raise

    def get_hyperparameters(self, experiment_id: str) -> Dict[str, Any]:
        """
        Gauna eksperimento hiperparametrus.
        
        Args:
            experiment_id: Eksperimento ID
            
        Returns:
            Dict[str, Any]: Hiperparametrų žodynas
        """
        try:
            # Randame eksperimentą pagal ID
            experiment = self.db.query(Experiment).filter(Experiment.id == experiment_id).first()
            
            if not experiment:
                logger.error(f"Eksperimentas su ID {experiment_id} nerastas")
                raise ValueError(f"Eksperimentas su ID {experiment_id} nerastas")
            
            # Grąžiname hiperparametrus
            return experiment.get_hyperparameters()
            
        except Exception as e:
            logger.error(f"Klaida gaunant hiperparametrus: {str(e)}")
            raise

    def update_hyperparameters(self, experiment_id: str, hyperparameters: Dict[str, Any]) -> Experiment:
        """
        Atnaujina eksperimento hiperparametrus (prideda arba modifikuoja).
        
        Args:
            experiment_id: Eksperimento ID
            hyperparameters: Hiperparametrų žodynas, kuris bus sujungtas su esamais
            
        Returns:
            Experiment: Atnaujintas eksperimento objektas
        """
        try:
            # Randame eksperimentą pagal ID
            experiment = self.db.query(Experiment).filter(Experiment.id == experiment_id).first()
            
            if not experiment:
                logger.error(f"Eksperimentas su ID {experiment_id} nerastas")
                raise ValueError(f"Eksperimentas su ID {experiment_id} nerastas")
            
            # Gauname esamus metaduomenis
            metadata = {}
            if experiment.metadata:
                try:
                    metadata = json.loads(experiment.metadata)
                except json.JSONDecodeError:
                    metadata = {}
            
            # Gauname esamus hiperparametrus arba inicializuojame tuščiu žodynu
            existing_hyperparameters = metadata.get("hyperparameters", {})
            
            # Sujungiame naujus hiperparametrus su esamais
            existing_hyperparameters.update(hyperparameters)
            
            # Atnaujiname metaduomenis
            metadata["hyperparameters"] = existing_hyperparameters
            experiment.metadata = json.dumps(metadata)
            experiment.updated_at = datetime.now(timezone.utc)
            
            # Įrašome pakeitimus
            self.db.commit()
            self.db.refresh(experiment)
            
            logger.info(f"Atnaujinti hiperparametrai eksperimentui {experiment.name} (ID: {experiment.id})")
            return experiment
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Klaida atnaujinant hiperparametrus: {str(e)}")
            raise

    def delete_hyperparameter(self, experiment_id: str, param_name: str) -> Experiment:
        """
        Pašalina konkretų hiperparametrą iš eksperimento.
        
        Args:
            experiment_id: Eksperimento ID
            param_name: Hiperparametro pavadinimas, kurį reikia pašalinti
            
        Returns:
            Experiment: Atnaujintas eksperimento objektas
        """
        try:
            # Randame eksperimentą pagal ID
            experiment = self.db.query(Experiment).filter(Experiment.id == experiment_id).first()
            
            if not experiment:
                logger.error(f"Eksperimentas su ID {experiment_id} nerastas")
                raise ValueError(f"Eksperimentas su ID {experiment_id} nerastas")
            
            # Gauname esamus metaduomenis
            metadata = {}
            if experiment.metadata:
                try:
                    metadata = json.loads(experiment.metadata)
                except json.JSONDecodeError:
                    metadata = {}
            
            # Gauname esamus hiperparametrus
            hyperparameters = metadata.get("hyperparameters", {})
            
            # Jei hiperparametras egzistuoja, pašaliname jį
            if param_name in hyperparameters:
                del hyperparameters[param_name]
                
                # Atnaujiname metaduomenis
                metadata["hyperparameters"] = hyperparameters
                experiment.metadata = json.dumps(metadata)
                experiment.updated_at = datetime.now(timezone.utc)
                
                # Įrašome pakeitimus
                self.db.commit()
                self.db.refresh(experiment)
                
                logger.info(f"Pašalintas hiperparametras '{param_name}' iš eksperimento {experiment.name}")
            else:
                logger.warning(f"Hiperparametras '{param_name}' nerastas eksperimente {experiment.name}")
            
            return experiment
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Klaida šalinant hiperparametrą: {str(e)}")
            raise

    def add_experiment_result(self, experiment_id: str, metric_name: str, 
                        metric_value: Union[float, int], stage: str = None, 
                        notes: str = None) -> ExperimentResult:
        """
        Prideda naują eksperimento metrikos rezultatą.
        
        Args:
            experiment_id: Eksperimento ID
            metric_name: Metrikos pavadinimas
            metric_value: Metrikos reikšmė (privalo būti skaičius)
            stage: Etapas, kuriame metrika buvo išmatuota (neprivalomas)
            notes: Papildomi komentarai (neprivalomi)
            
        Returns:
            ExperimentResult: Sukurtas rezultato objektas
            
        Raises:
            ValueError: Jei metrikos reikšmė nėra skaičius
        """
        try:
            # Patikriname, ar eksperimentas egzistuoja
            experiment = self.db.query(Experiment).filter(Experiment.id == experiment_id).first()
            
            if not experiment:
                logger.error(f"Eksperimentas su ID {experiment_id} nerastas")
                raise ValueError(f"Eksperimentas su ID {experiment_id} nerastas")
            
            # Patikriname, ar metrikos reikšmė yra skaičius
            try:
                numeric_value = float(metric_value)
            except (ValueError, TypeError):
                logger.error(f"Metrikos reikšmė '{metric_value}' nėra skaičius")
                raise ValueError(f"Metrikos reikšmė privalo būti skaičius, gauta: {metric_value}")
            
            # Sukuriame naują rezultato įrašą
            result = ExperimentResult(
                experiment_id=experiment_id,
                metric_name=metric_name,
                metric_value=str(numeric_value),  # Konvertuojame į string saugojimui
                stage=stage,
                notes=notes
            )
            
            # Įrašome į duomenų bazę
            self.db.add(result)
            self.db.commit()
            self.db.refresh(result)
            
            # Atnaujiname eksperimento paskutinio atnaujinimo datą
            experiment.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            
            logger.info(f"Pridėtas naujas rezultatas eksperimentui {experiment.name}: {metric_name} = {numeric_value}")
            return result
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Klaida pridedant eksperimento rezultatą: {str(e)}")
            raise  

    def get_experiment_results(self, experiment_id: str, metric_name: str = None) -> List[ExperimentResult]:
        """
        Gauna eksperimento rezultatus.
        
        Args:
            experiment_id: Eksperimento ID
            metric_name: Filtruoti pagal metrikos pavadinimą (neprivalomas)
            
        Returns:
            List[ExperimentResult]: Eksperimento rezultatų sąrašas
        """
        try:
            # Pradedame užklausą
            query = self.db.query(ExperimentResult).filter(ExperimentResult.experiment_id == experiment_id)
            
            # Jei nurodytas metrikos pavadinimas, filtruojame
            if metric_name:
                query = query.filter(ExperimentResult.metric_name == metric_name)
            
            # Rikiuojame pagal sukūrimo datą (naujausi pirmi)
            results = query.order_by(ExperimentResult.created_at.desc()).all()
            
            logger.info(f"Gauta {len(results)} rezultatų eksperimentui {experiment_id}")
            return results
            
        except Exception as e:
            logger.error(f"Klaida gaunant eksperimentų rezultatus: {str(e)}")
            raise

    def get_latest_experiment_result(self, experiment_id: str, metric_name: str) -> Optional[ExperimentResult]:
        """
        Gauna naujausią eksperimento rezultatą pagal metrikos pavadinimą.
        
        Args:
            experiment_id: Eksperimento ID
            metric_name: Metrikos pavadinimas
            
        Returns:
            Optional[ExperimentResult]: Naujausias rezultato objektas arba None, jei nerasta
        """
        try:
            # Ieškome naujausio rezultato
            result = self.db.query(ExperimentResult).filter(
                ExperimentResult.experiment_id == experiment_id,
                ExperimentResult.metric_name == metric_name
            ).order_by(ExperimentResult.created_at.desc()).first()
            
            if result:
                logger.info(f"Rastas naujausias rezultatas eksperimentui {experiment_id}: {metric_name} = {result.metric_value}")
            else:
                logger.info(f"Nerasta rezultatų eksperimentui {experiment_id} su metrika {metric_name}")
            
            return result
            
        except Exception as e:
            logger.error(f"Klaida gaunant naujausią eksperimento rezultatą: {str(e)}")
            raise

    def delete_experiment_result(self, result_id: str) -> bool:
        """
        Ištrina eksperimento rezultatą pagal ID.
        
        Args:
            result_id: Rezultato ID
            
        Returns:
            bool: True, jei rezultatas buvo sėkmingai ištrintas, False kitais atvejais
        """
        try:
            # Randame rezultatą pagal ID
            result = self.db.query(ExperimentResult).filter(ExperimentResult.id == result_id).first()
            
            if not result:
                logger.warning(f"Rezultatas su ID {result_id} nerastas, negalima ištrinti")
                return False
            
            # Ištriname rezultatą
            self.db.delete(result)
            self.db.commit()
            
            logger.info(f"Rezultatas {result.metric_name} = {result.metric_value} ištrintas")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Klaida ištrinant eksperimento rezultatą: {str(e)}")
            raise

    def get_experiment_metrics_summary(self, experiment_id: str) -> Dict[str, Any]:
        """
        Gauna eksperimento metrikų suvestinę.
        
        Args:
            experiment_id: Eksperimento ID
            
        Returns:
            Dict[str, Any]: Metrikų suvestinė (pavadinimas -> reikšmė)
        """
        try:
            # Gauname visus eksperimento rezultatus
            results = self.get_experiment_results(experiment_id)
            
            if not results:
                logger.info(f"Eksperimentui {experiment_id} nerasta jokių rezultatų")
                return {}
            
            # Grupuojame metrikas pagal pavadinimą ir etapą
            metrics_summary = {}
            
            for result in results:
                metric_key = result.metric_name
                if result.stage:
                    metric_key = f"{result.stage}_{metric_key}"
                
                # Išsaugome tik naujausią įrašą kiekvienai metrikai
                if metric_key not in metrics_summary or result.created_at > metrics_summary[metric_key]["created_at"]:
                    metrics_summary[metric_key] = {
                        "value": result.numeric_value,
                        "created_at": result.created_at
                    }
            
            # Suformuojame galutinę suvestinę (tik su reikšmėmis)
            final_summary = {key: data["value"] for key, data in metrics_summary.items()}
            
            logger.info(f"Suformuota metrikų suvestinė eksperimentui {experiment_id} su {len(final_summary)} metrikomis")
            return final_summary
            
        except Exception as e:
            logger.error(f"Klaida gaunant eksperimento metrikų suvestinę: {str(e)}")
            raise

    def compare_experiments(self, experiment_id1: str, experiment_id2: str) -> Dict[str, Any]:
        """
        Palygina du eksperimentus - jų hiperparametrus ir rezultatus.
        
        Args:
            experiment_id1: Pirmo eksperimento ID
            experiment_id2: Antro eksperimento ID
            
        Returns:
            Dict[str, Any]: Eksperimentų palyginimo rezultatai
        """
        try:
            # Gauname abu eksperimentus
            experiment1 = self.get_experiment(experiment_id1)
            experiment2 = self.get_experiment(experiment_id2)
            
            if not experiment1 or not experiment2:
                logger.error("Vienas ar abu eksperimentai nerasti")
                missing = []
                if not experiment1:
                    missing.append(experiment_id1)
                if not experiment2:
                    missing.append(experiment_id2)
                return {
                    "success": False,
                    "error": f"Eksperimentai nerasti: {', '.join(missing)}"
                }
            
            # Paruošiame palyginimo rezultatus
            comparison = {
                "success": True,
                "experiment1": {
                    "id": experiment1.id,
                    "name": experiment1.name,
                    "status": experiment1.status,
                    "created_at": experiment1.created_at.isoformat() if experiment1.created_at else None,
                    "updated_at": experiment1.updated_at.isoformat() if experiment1.updated_at else None
                },
                "experiment2": {
                    "id": experiment2.id,
                    "name": experiment2.name,
                    "status": experiment2.status,
                    "created_at": experiment2.created_at.isoformat() if experiment2.created_at else None,
                    "updated_at": experiment2.updated_at.isoformat() if experiment2.updated_at else None
                },
                "hyperparameters_comparison": {},
                "metrics_comparison": {}
            }
            
            # Gauname hiperparametrus
            hyperparams1 = self.get_hyperparameters(experiment_id1)
            hyperparams2 = self.get_hyperparameters(experiment_id2)
            
            # Sudarome hiperparametrų palyginimą
            all_hyperparams = set(hyperparams1.keys()) | set(hyperparams2.keys())
            
            for param in all_hyperparams:
                comparison["hyperparameters_comparison"][param] = {
                    "experiment1": hyperparams1.get(param, "Nenustatyta"),
                    "experiment2": hyperparams2.get(param, "Nenustatyta"),
                    "different": hyperparams1.get(param) != hyperparams2.get(param)
                }
            
            # Gauname metrikas
            metrics1 = self.get_experiment_metrics_summary(experiment_id1)
            metrics2 = self.get_experiment_metrics_summary(experiment_id2)
            
            # Sudarome metrikų palyginimą
            all_metrics = set(metrics1.keys()) | set(metrics2.keys())
            
            for metric in all_metrics:
                metric_value1 = metrics1.get(metric)
                metric_value2 = metrics2.get(metric)
                
                # Apskaičiuojame skirtumą, jei abu yra skaičiai
                difference = None
                percent_change = None
                
                if metric_value1 is not None and metric_value2 is not None:
                    difference = metric_value2 - metric_value1
                    if metric_value1 != 0:  # Išvengiame dalybos iš nulio
                        percent_change = (difference / abs(metric_value1)) * 100
                
                comparison["metrics_comparison"][metric] = {
                    "experiment1": metric_value1 if metric_value1 is not None else "Nenustatyta",
                    "experiment2": metric_value2 if metric_value2 is not None else "Nenustatyta",
                    "difference": difference,
                    "percent_change": percent_change,
                    "better_in_experiment2": self._is_metric_better(metric, metric_value1, metric_value2)
                }
            
            logger.info(f"Sėkmingai palyginami eksperimentai: {experiment1.name} ir {experiment2.name}")
            return comparison
            
        except Exception as e:
            logger.error(f"Klaida lyginant eksperimentus: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def _is_metric_better(self, metric_name: str, value1: float, value2: float) -> Optional[bool]:
        """
        Nustato, ar antrojo eksperimento metrika yra geresnė už pirmojo.
        
        Args:
            metric_name: Metrikos pavadinimas
            value1: Pirmojo eksperimento reikšmė
            value2: Antrojo eksperimento reikšmė
            
        Returns:
            Optional[bool]: True, jei antrojo geresnė; False, jei pirmojo geresnė; None, jei negalima palyginti
        """
        if value1 is None or value2 is None:
            return None
        
        # Kai kurios metrikos yra geresnės, kai mažesnė reikšmė yra geresnė
        lower_is_better = ["loss", "error", "mae", "mse", "rmse"]
        
        # Tikriname, ar metrikos pavadinimas turi bent vieną iš žodžių, kur mažesnė reikšmė yra geresnė
        is_lower_better = any(word in metric_name.lower() for word in lower_is_better)
        
        if is_lower_better:
            return value2 < value1
        else:
            # Kitoms metrikoms (pvz., accuracy, precision) didesnė reikšmė yra geresnė
            return value2 > value1

    def find_similar_experiments(self, experiment_id: str, 
                           metric_names: List[str] = None,
                           hyperparameter_names: List[str] = None,
                           max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Randa eksperimentus, panašius į nurodytą pagal metrikas ir hiperparametrus.
        
        Args:
            experiment_id: Eksperimento ID, kuriam ieškome panašių
            metric_names: Metrikų pavadinimai, pagal kuriuos lyginti (neprivalomas)
            hyperparameter_names: Hiperparametrų pavadinimai, pagal kuriuos lyginti (neprivalomas)
            max_results: Maksimalus grąžinamų rezultatų skaičius
            
        Returns:
            List[Dict[str, Any]]: Panašių eksperimentų sąrašas su panašumo įverčiu
        """
        try:
            # Gauname bazinį eksperimentą
            base_experiment = self.get_experiment(experiment_id)
            
            if not base_experiment:
                logger.error(f"Eksperimentas su ID {experiment_id} nerastas")
                return []
            
            # Gauname bazinio eksperimento hiperparametrus and metrikas
            base_hyperparams = self.get_hyperparameters(experiment_id)
            base_metrics = self.get_experiment_metrics_summary(experiment_id)
            
            # Jei nenurodyti konkretūs hiperparametrai ar metrikos, naudojame visus
            if not hyperparameter_names:
                hyperparameter_names = list(base_hyperparams.keys())
            
            if not metric_names:
                metric_names = list(base_metrics.keys())
            
            # Gauname visus eksperimentus (išskyrus bazinį)
            all_experiments = self.get_all_experiments(limit=100)  # Imame pakankamai daug
            
            similar_experiments = []
            
            for exp in all_experiments:
                # Praleidžiame patį bazinį eksperimentą
                if exp.id == experiment_id:
                    continue
                
                # Gauname eksperimento hiperparametrus and metrikas
                exp_hyperparams = self.get_hyperparameters(exp.id)
                exp_metrics = self.get_experiment_metrics_summary(exp.id)
                
                # Skaičiuojame hiperparametrų panašumą
                hyperparams_similarity = 0
                hyperparams_count = 0
                
                for param_name in hyperparameter_names:
                    if param_name in base_hyperparams and param_name in exp_hyperparams:
                        # Jei hiperparametrai sutampa, pridedame 1 tašką
                        if base_hyperparams[param_name] == exp_hyperparams[param_name]:
                            hyperparams_similarity += 1
                        hyperparams_count += 1
                
                # Skaičiuojame metrikų panašumą
                metrics_similarity = 0
                metrics_count = 0
                
                for metric_name in metric_names:
                    if metric_name in base_metrics and metric_name in exp_metrics:
                        base_value = base_metrics[metric_name]
                        exp_value = exp_metrics[metric_name]
                        
                        # Skaičiuojame panašumą pagal santykį arba skirtumą
                        if base_value != 0 and exp_value != 0:
                            # Jei reikšmės artimos (skirtumas < 10%), pridedame 1 tašką
                            ratio = min(base_value, exp_value) / max(base_value, exp_value)
                            if ratio > 0.9:  # 90% panašumas
                                metrics_similarity += 1
                        metrics_count += 1
                
                # Apskaičiuojame bendrą panašumo įvertį
                total_similarity = 0
                if hyperparams_count > 0:
                    hyperparams_score = hyperparams_similarity / hyperparams_count
                    total_similarity += hyperparams_score * 0.6  # Hiperparametrai sudaro 60% svorio
                
                if metrics_count > 0:
                    metrics_score = metrics_similarity / metrics_count
                    total_similarity += metrics_score * 0.4  # Metrikos sudaro 40% svorio
                
                # Pridedame į panašių eksperimentų sąrašą
                similar_experiments.append({
                    "experiment": {
                        "id": exp.id,
                        "name": exp.name,
                        "status": exp.status,
                        "created_at": exp.created_at.isoformat() if exp.created_at else None
                    },
                    "similarity_score": total_similarity,
                    "hyperparams_similarity": hyperparams_similarity / hyperparams_count if hyperparams_count > 0 else 0,
                    "metrics_similarity": metrics_similarity / metrics_count if metrics_count > 0 else 0
                })
            
            # Rikiuojame pagal panašumo įvertį (nuo didžiausio iki mažiausio)
            similar_experiments.sort(key=lambda x: x["similarity_score"], reverse=True)
            
            # Grąžiname tik nurodytą skaičių rezultatų
            return similar_experiments[:max_results]
            
        except Exception as e:
            logger.error(f"Klaida ieškant panašių eksperimentų: {str(e)}")
            return []

    def format_comparison_table(self, comparison: Dict[str, Any]) -> str:
        """
        Formatuoja eksperimentų palyginimą lentelės formatu.
        
        Args:
            comparison: Eksperimentų palyginimo rezultatai
            
        Returns:
            str: Suformatuota palyginimo lentelė
        """
        if not comparison.get("success", False):
            return f"Nepavyko palyginti eksperimentų: {comparison.get('error', 'Nežinoma klaida')}"
        
        # Gauname eksperimentų informaciją
        exp1_name = comparison["experiment1"]["name"]
        exp2_name = comparison["experiment2"]["name"]
        
        result = f"Eksperimentų palyginimas: {exp1_name} vs {exp2_name}\n\n"
        
        # Formatuojame hiperparametrų palyginimą
        result += "=== HIPERPARAMETRAI ===\n"
        result += f"{'Parametras':<20} | {exp1_name:<15} | {exp2_name:<15} | {'Skirtumas':<10}\n"
        result += "-" * 70 + "\n"
        
        for param, values in comparison["hyperparameters_comparison"].items():
            exp1_value = str(values["experiment1"])
            exp2_value = str(values["experiment2"])
            different = "SKIRIASI" if values["different"] else "VIENODI"
            
            result += f"{param:<20} | {exp1_value:<15} | {exp2_value:<15} | {different:<10}\n"
        
        # Formatuojame metrikų palyginimą
        result += "\n=== METRIKOS ===\n"
        result += f"{'Metrika':<20} | {exp1_name:<15} | {exp2_name:<15} | {'Skirtumas':<10} | {'Pokytis':<10} | {'Geresnis':<10}\n"
        result += "-" * 90 + "\n"
        
        for metric, values in comparison["metrics_comparison"].items():
            exp1_value = values["experiment1"] if isinstance(values["experiment1"], str) else f"{values['experiment1']:.4f}"
            exp2_value = values["experiment2"] if isinstance(values["experiment2"], str) else f"{values['experiment2']:.4f}"
            
            diff = ""
            if values["difference"] is not None:
                diff = f"{values['difference']:.4f}"
            
            change = ""
            if values["percent_change"] is not None:
                change = f"{values['percent_change']:.2f}%"
            
            better = ""
            if values["better_in_experiment2"] is True:
                better = "2-as"
            elif values["better_in_experiment2"] is False:
                better = "1-as"
            
            result += f"{metric:<20} | {exp1_value:<15} | {exp2_value:<15} | {diff:<10} | {change:<10} | {better:<10}\n"
        
        return result

    def export_results_to_csv(self, experiment_id: str, output_file: str, 
                          include_stage: bool = True, include_notes: bool = False) -> bool:
        """
        Eksportuoja eksperimento rezultatus į CSV failą.
        
        Args:
            experiment_id: Eksperimento ID
            output_file: CSV failo, į kurį eksportuoti rezultatus, kelias
            include_stage: Ar įtraukti etapo (stage) stulpelį (numatytasis: True)
            include_notes: Ar įtraukti pastabų (notes) stulpelį (numatytasis: False)
            
        Returns:
            bool: True, jei eksportavimas sėkmingas, False kitais atvejais
        """
        try:
            # Gauname eksperimentą
            experiment = self.get_experiment(experiment_id)
            
            if not experiment:
                logger.error(f"Eksperimentas su ID {experiment_id} nerastas")
                return False
            
            # Gauname eksperimento rezultatus
            results = self.get_experiment_results(experiment_id)
            
            if not results:
                logger.warning(f"Eksperimentui {experiment.name} nerasta jokių rezultatų")
                return False
            
            # Sukuriame direktorijas, jei jų nėra
            os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
            
            # Nustatome stulpelius
            columns = ["metric_name", "metric_value", "created_at"]
            
            if include_stage:
                columns.append("stage")
            
            if include_notes:
                columns.append("notes")
            
            # Atidarome failą rašymui
            with open(output_file, 'w', newline='', encoding='utf-8') as csv_file:
                # Sukuriame CSV rašymo objektą
                writer = csv.writer(csv_file)
                
                # Rašome antraštinę eilutę
                header = columns
                writer.writerow(header)
                
                # Rašome rezultatus
                for result in results:
                    row = [
                        result.metric_name,
                        result.metric_value,
                        result.created_at.strftime("%Y-%m-%d %H:%M:%S")
                    ]
                    
                    if include_stage:
                        row.append(result.stage if result.stage else "")
                    
                    if include_notes:
                        row.append(result.notes if result.notes else "")
                    
                    writer.writerow(row)
            
            # Sėkmingai eksportavome
            logger.info(f"Eksperimento {experiment.name} rezultatai sėkmingai eksportuoti į {output_file}")
            
            # Grąžiname eilučių skaičių (be antraščių)
            return True
            
        except Exception as e:
            logger.error(f"Klaida eksportuojant eksperimento rezultatus į CSV: {str(e)}")
            return False

    def import_results_from_csv(self, experiment_id: str, csv_file: str) -> Dict[str, Any]:
        """
        Importuoja eksperimento rezultatus iš CSV failo.
        
        Args:
            experiment_id: Eksperimento ID, į kurį importuoti rezultatus
            csv_file: CSV failo, iš kurio importuoti rezultatus, kelias
            
        Returns:
            Dict[str, Any]: Importavimo rezultatai su statistika
        """
       
        # Tikrinama, ar CSV failas egzistuoja
        if not os.path.exists(csv_file):
            logger.error(f"CSV failas nerastas: {csv_file}")
            return {
                "success": False,
                "error": f"CSV failas nerastas: {csv_file}",
                "imported_count": 0,
                "skipped_count": 0,
                "error_count": 0
            }
        
        # Gauname eksperimentą
        experiment = self.get_experiment(experiment_id)
        
        if not experiment:
            logger.error(f"Eksperimentas su ID {experiment_id} nerastas")
            return {
                "success": False,
                "error": f"Eksperimentas su ID {experiment_id} nerastas",
                "imported_count": 0,
                "skipped_count": 0,
                "error_count": 0
            }
        
        # Rezultatų skaitliukai
        imported_count = 0  # Sėkmingai importuotų įrašų skaičius
        skipped_count = 0   # Praleistų įrašų skaičius (jau egzistuoja arba neteisingas formatas)
        error_count = 0     # Klaidų skaičius
        errors = []         # Klaidų sąrašas
        
        # Atidarome CSV failą skaitymui
        with open(csv_file, 'r', newline='', encoding='utf-8') as csv_file:
            # Sukuriame CSV skaitymo objektą
            reader = csv.reader(csv_file)
            
            # Skaitome antraštinę eilutę
            headers = next(reader, None)
            
            if not headers:
                logger.error("CSV failas tuščias arba netinkamo formato")
                return {
                    "success": False,
                    "error": "CSV failas tuščias arba netinkamo formato",
                    "imported_count": 0,
                    "skipped_count": 0,
                    "error_count": 0
                }
            
            # Tikriname, ar yra būtini stulpeliai
            required_columns = ["metric_name", "metric_value"]
            missing_columns = [col for col in required_columns if col not in headers]
            
            if missing_columns:
                logger.error(f"CSV failui trūksta būtinų stulpelių: {', '.join(missing_columns)}")
                return {
                    "success": False,
                    "error": f"CSV failui trūksta būtinų stulpelių: {', '.join(missing_columns)}",
                    "imported_count": 0,
                    "skipped_count": 0,
                    "error_count": 0
                }
            
            # Indeksai stulpelių
            metric_name_idx = headers.index("metric_name")
            metric_value_idx = headers.index("metric_value")
            stage_idx = headers.index("stage") if "stage" in headers else None
            notes_idx = headers.index("notes") if "notes" in headers else None
            
            # Skaitome kiekvieną eilutę ir ją importuojame
            row_num = 1  # Pradedame nuo 1, nes 0 yra antraštė
            
            for row in reader:
                row_num += 1
                
                try:
                    # Tikriname, ar eilutė turi pakankamai stulpelių
                    if len(row) < max(metric_name_idx, metric_value_idx) + 1:
                        logger.warning(f"CSV eilutė {row_num} turi nepakankamai stulpelių, praleidžiama")
                        skipped_count += 1
                        continue
                    
                    # Gauname metrikas ir reikšmes
                    metric_name = row[metric_name_idx].strip()
                    metric_value_str = row[metric_value_idx].strip()
                    
                    # Validuojame metriką ir reikšmę
                    if not metric_name:
                        logger.warning(f"CSV eilutė {row_num} neturi metrikos pavadinimo, praleidžiama")
                        skipped_count += 1
                        continue
                    
                    # Konvertuojame reikšmę į skaičių
                    try:
                        metric_value = float(metric_value_str)
                    except ValueError:
                        logger.warning(f"CSV eilutė {row_num} turi netinkamą metrikos reikšmę: {metric_value_str}, praleidžiama")
                        skipped_count += 1
                        continue
                    
                    # Gauname stage ir notes, jei jie yra
                    stage = row[stage_idx].strip() if stage_idx is not None and stage_idx < len(row) else None
                    notes = row[notes_idx].strip() if notes_idx is not None and notes_idx < len(row) else None
                    
                    # Pridedame eksperimento rezultatą
                    self.add_experiment_result(
                        experiment_id=experiment_id,
                        metric_name=metric_name,
                        metric_value=metric_value,
                        stage=stage,
                        notes=notes
                    )
                    
                    imported_count += 1
                    
                except Exception as e:
                    error_message = f"Klaida importuojant CSV eilutę {row_num}: {str(e)}"
                    logger.error(error_message)
                    errors.append(error_message)
                    error_count += 1
        
        # Sėkmingai importavome
        success = imported_count > 0 and error_count == 0
        message = f"Importuota {imported_count} metrikų, praleista {skipped_count}, klaidų {error_count}"
        
        logger.info(f"CSV importavimas baigtas: {message}")
        
        return {
            "success": success,
            "message": message,
            "imported_count": imported_count,
            "skipped_count": skipped_count,
            "error_count": error_count,
            "errors": errors if errors else None
        }

    def generate_experiment_report(self, experiment_id: str, include_hyperparams: bool = True,
                              include_metrics: bool = True) -> str:
        """
        Generuoja tekstinę ataskaitą apie eksperimentą.
        
        Args:
            experiment_id: Eksperimento ID
            include_hyperparams: Ar įtraukti hiperparametrus į ataskaitą (numatytasis: True)
            include_metrics: Ar įtraukti metrikas į ataskaitą (numatytasis: True)
            
        Returns:
            str: Suformatuota tekstinė ataskaita
        """
        try:
            # Gauname eksperimentą
            experiment = self.get_experiment(experiment_id)
            
            if not experiment:
                logger.error(f"Eksperimentas su ID {experiment_id} nerastas")
                return f"KLAIDA: Eksperimentas su ID {experiment_id} nerastas"
            
            # Formuojame ataskaitos antraštę
            report = []
            report.append("=" * 60)
            report.append("EKSPERIMENTO ATASKAITA")
            report.append("=" * 60)
            report.append("")
            
            # Pagrindinė informacija apie eksperimentą
            report.append(f"Eksperimento ID:        {experiment.id}")
            report.append(f"Pavadinimas:            {experiment.name}")
            report.append(f"Statusas:               {experiment.status}")
            report.append(f"Sukūrimo data:          {experiment.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            report.append(f"Paskutinis atnaujinimas:{experiment.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
            
            if experiment.creator_id:
                report.append(f"Kūrėjas:                {experiment.creator_id}")
            
            if experiment.description:
                report.append("")
                report.append("APRAŠYMAS:")
                report.append("-" * 60)
                report.append(experiment.description)
            
            # Hiperparametrai
            if include_hyperparams:
                hyperparams = self.get_hyperparameters(experiment_id)
                
                if hyperparams:
                    report.append("")
                    report.append("HIPERPARAMETRAI:")
                    report.append("-" * 60)
                    
                    # Rikiuojame hiperparametrus pagal pavadinimą
                    sorted_params = sorted(hyperparams.items())
                    
                    for param_name, param_value in sorted_params:
                        report.append(f"{param_name:<25}: {param_value}")
                else:
                    report.append("")
                    report.append("HIPERPARAMETRAI: Nėra")
                    
            # Metrikos ir rezultatai
            if include_metrics:
                metrics_summary = self.get_experiment_metrics_summary(experiment_id)
                results = self.get_experiment_results(experiment_id)
                
                if metrics_summary:
                    report.append("")
                    report.append("METRIKOS (paskutinės reikšmės):")
                    report.append("-" * 60)
                    
                    # Grupuojame metrikas pagal etapą
                    stage_metrics = {}
                    
                    for metric_key, metric_value in metrics_summary.items():
                        # Išskaidome metrikos raktą į etapą ir pavadinimą, jei įmanoma
                        if "_" in metric_key and not metric_key.startswith("_"):
                            stage, name = metric_key.split("_", 1)
                            if stage not in stage_metrics:
                                stage_metrics[stage] = []
                            stage_metrics[stage].append((name, metric_value))
                        else:
                            # Jei nėra etapo, priskiriam "kita" kategorijai
                            if "kita" not in stage_metrics:
                                stage_metrics["kita"] = []
                            stage_metrics["kita"].append((metric_key, metric_value))
                    
                    # Išvedame metrikas pagal etapus
                    for stage, metrics in sorted(stage_metrics.items()):
                        report.append(f"{stage.upper()}:")
                        for name, value in sorted(metrics):
                            report.append(f"    {name:<20}: {value:.6f}")
                        report.append("")
                else:
                    report.append("")
                    report.append("METRIKOS: Nėra")
                
                # Pridedame paskutinių rezultatų istoriją
                if results:
                    report.append("")
                    report.append("PASKUTINIAI 10 REZULTATŲ:")
                    report.append("-" * 60)
                    report.append(f"{'Data':<20} {'Metrika':<20} {'Etapas':<15} {'Reikšmė':<10}")
                    report.append("-" * 60)
                    
                    for result in results[:10]:  # Parodome tik paskutinius 10 rezultatų
                        date_str = result.created_at.strftime("%Y-%m-%d %H:%M:%S")
                        stage = result.stage if result.stage else "-"
                        report.append(f"{date_str:<20} {result.metric_name:<20} {stage:<15} {result.metric_value:<10}")
            
            # Sugeneruojame galutinę ataskaitą
            return "\n".join(report)
            
        except Exception as e:
            logger.error(f"Klaida generuojant eksperimento ataskaitą: {str(e)}")
            return f"KLAIDA: Nepavyko sugeneruoti ataskaitos: {str(e)}"

    def save_experiment_report(self, experiment_id: str, output_file: str,
                          include_hyperparams: bool = True, include_metrics: bool = True) -> bool:
        """
        Sugeneruoja ir išsaugo eksperimento ataskaitą į tekstinį failą.
        
        Args:
            experiment_id: Eksperimento ID
            output_file: Failo, į kurį išsaugoti ataskaitą, kelias
            include_hyperparams: Ar įtraukti hiperparametrus į ataskaitą (numatytasis: True)
            include_metrics: Ar įtraukti metrikas į ataskaitą (numatytasis: True)
            
        Returns:
            bool: True, jei išsaugojimas sėkmingas, False kitais atvejais
        """
        try:
            # Gauname eksperimentą
            experiment = self.get_experiment(experiment_id)
            
            if not experiment:
                logger.error(f"Eksperimentas su ID {experiment_id} nerastas")
                return False
            
            # Generuojame ataskaitą
            report = self.generate_experiment_report(
                experiment_id=experiment_id,
                include_hyperparams=include_hyperparams,
                include_metrics=include_metrics
            )
            
            # Sukuriame direktorijas, jei jų nėra
            os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
            
            # Įrašome ataskaitą į failą
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report)
            
            logger.info(f"Eksperimento {experiment.name} ataskaita išsaugota į {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Klaida išsaugant eksperimento ataskaitą: {str(e)}")
            return False

    def export_experiment_to_json(self, experiment_id: str, output_file: str) -> bool:
        """
        Eksportuoja eksperimentą ir jo rezultatus į JSON failą.
        
        Args:
            experiment_id: Eksperimento ID
            output_file: JSON failo, į kurį eksportuoti, kelias
            
        Returns:
            bool: True, jei eksportavimas sėkmingas, False kitais atvejais
        """
        try:
            # Gauname eksperimentą
            experiment = self.get_experiment(experiment_id)
            
            if not experiment:
                logger.error(f"Eksperimentas su ID {experiment_id} nerastas")
                return False
            
            # Gauname hiperparametrus
            hyperparameters = self.get_hyperparameters(experiment_id)
            
            # Gauname visus rezultatus
            results = self.get_experiment_results(experiment_id)
            results_data = []
            
            for result in results:
                results_data.append({
                    "id": result.id,
                    "metric_name": result.metric_name,
                    "metric_value": result.metric_value,
                    "created_at": result.created_at.isoformat() if result.created_at else None,
                    "stage": result.stage,
                    "notes": result.notes
                })
            
            # Sukuriame eksportuojamą struktūrą
            export_data = {
                "experiment": {
                    "id": experiment.id,
                    "name": experiment.name,
                    "description": experiment.description,
                    "status": experiment.status,
                    "creator_id": experiment.creator_id,
                    "created_at": experiment.created_at.isoformat() if experiment.created_at else None,
                    "updated_at": experiment.updated_at.isoformat() if experiment.updated_at else None,
                    "metadata": experiment.get_metadata_dict() if hasattr(experiment, "get_metadata_dict") else {}
                },
                "hyperparameters": hyperparameters,
                "results": results_data,
                "export_info": {
                    "exported_at": datetime.now(timezone.utc).isoformat(),
                    "export_version": "1.0"
                }
            }
            
            # Sukuriame direktorijas, jei jų nėra
            os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
            
            # Įrašome į JSON failą
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Eksperimentas {experiment.name} sėkmingai eksportuotas į {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Klaida eksportuojant eksperimentą į JSON: {str(e)}")
            return False

    def import_experiment_from_json(self, json_file: str, 
                              create_new_id: bool = True,
                              creator_id: str = None) -> Dict[str, Any]:
        """
        Importuoja eksperimentą ir jo rezultatus iš JSON failo.
        
        Args:
            json_file: JSON failo, iš kurio importuoti, kelias
            create_new_id: Ar sukurti naują ID importuojamam eksperimentui (išvengiant konfliktų)
            creator_id: Nurodytas kūrėjo ID (jei nenurodytas, naudojamas originalus arba None)
            
        Returns:
            Dict[str, Any]: Importavimo rezultatų žodynas
        """
        try:
            # Tikriname, ar JSON failas egzistuoja
            if not os.path.exists(json_file):
                logger.error(f"JSON failas nerastas: {json_file}")
                return {
                    "success": False,
                    "error": f"JSON failas nerastas: {json_file}"
                }
        
            # Skaitome JSON failą
            with open(json_file, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            # Tikriname, ar JSON turi reikiamą struktūrą
            if not all(key in import_data for key in ["experiment", "hyperparameters", "results"]):
                logger.error("JSON failas neturi reikiamos struktūros")
                return {
                    "success": False,
                    "error": "JSON failas neturi reikiamos struktūros (trūksta experiment, hyperparameters arba results)"
                }
            
            # Gauname eksperimento duomenis
            experiment_data = import_data["experiment"]
            original_id = experiment_data.get("id")
            
            # Tikriname, ar eksperimentas su tokiu ID jau egzistuoja
            if not create_new_id and original_id:
                existing_experiment = self.get_experiment(original_id)
                if existing_experiment:
                    logger.warning(f"Eksperimentas su ID {original_id} jau egzistuoja ir create_new_id=False")
                    return {
                        "success": False,
                        "error": f"Eksperimentas su ID {original_id} jau egzistuoja. Nustatykite create_new_id=True, jei norite importuoti kaip naują eksperimentą."
                    }
            
            # Sukuriame naują eksperimentą
            new_experiment = self.create_experiment(
                name=experiment_data.get("name", "Importuotas eksperimentas"),
                creator_id=creator_id or experiment_data.get("creator_id"),
                description=experiment_data.get("description", ""),
                status=experiment_data.get("status", "importuotas")
            )
            
            # Išsaugome hiperparametrus
            if import_data.get("hyperparameters"):
                self.save_hyperparameters(new_experiment.id, import_data["hyperparameters"])
            
            # Importuojame rezultatus
            imported_results_count = 0
            skipped_results_count = 0
            
            for result_data in import_data.get("results", []):
                try:
                    # Konvertuojame metric_value į skaičių
                    metric_value = float(result_data.get("metric_value", 0))
                    
                    # Pridedame rezultatą
                    self.add_experiment_result(
                        experiment_id=new_experiment.id,
                        metric_name=result_data.get("metric_name", "unknown"),
                        metric_value=metric_value,
                        stage=result_data.get("stage"),
                        notes=result_data.get("notes")
                    )
                    
                    imported_results_count += 1
                    
                except Exception as e:
                    logger.warning(f"Nepavyko importuoti rezultato: {str(e)}")
                    skipped_results_count += 1
            
            # Atnaujinamas eksperimento statusas ir paskutinio atnaujinimo data
            if experiment_data.get("status"):
                self.update_experiment_status(new_experiment.id, experiment_data["status"])
            
            # Grąžiname rezultatus
            return {
                "success": True,
                "message": f"Eksperimentas sėkmingai importuotas. Rezultatai: importuota {imported_results_count}, praleista {skipped_results_count}",
                "experiment_id": new_experiment.id,
                "experiment_name": new_experiment.name,
                "original_id": original_id,
                "imported_results_count": imported_results_count,
                "skipped_results_count": skipped_results_count
            }
            
        except Exception as e:
            logger.error(f"Klaida importuojant eksperimentą iš JSON: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def visualize_experiment_metrics(self, experiment_id: str, metric_names: List[str] = None,
                               stages: List[str] = None, output_file: str = None, 
                               title: str = None, figsize: tuple = (10, 6)) -> bool:
        """
        Vizualizuoja eksperimento metrikas panaudojant linijinę diagramą.
        
        Args:
            experiment_id: Eksperimento ID
            metric_names: Metrikų pavadinimai, kuriuos norima vizualizuoti (jei None, naudojamos visos)
            stages: Etapai, kuriuos norima vizualizuoti (jei None, naudojami visi)
            output_file: Failo kelias, kur išsaugoti paveikslėlį (jei None, tik rodomas)
            title: Diagramos pavadinimas (jei None, naudojamas eksperimento pavadinimas)
            figsize: Diagramos dydis coliais (plotis, aukštis)
            
        Returns:
            bool: True, jei vizualizacija sėkminga, False kitais atvejais
        """
        try:
            # Importuojame matplotlib tik kai reikia
            import matplotlib.pyplot as plt
            from matplotlib.ticker import MaxNLocator
            import numpy as np
            
            # Gauname eksperimentą
            experiment = self.get_experiment(experiment_id)
            
            if not experiment:
                logger.error(f"Eksperimentas su ID {experiment_id} nerastas")
                return False
            
            # Gauname visus eksperimento rezultatus
            all_results = self.get_experiment_results(experiment_id)
            
            if not all_results:
                logger.warning(f"Eksperimentui {experiment.name} nerasta jokių rezultatų")
                return False
            
            # Apdorojame rezultatus pagal metrikas ir etapus
            metrics_data = {}
            
            # Jei metric_names neperduotas, naudojame visas rastas metrikas
            if metric_names is None:
                metric_names = list(set(result.metric_name for result in all_results))
            
            # Filtruojame rezultatus pagal etapus, jei jie nurodyti
            filtered_results = all_results
            if stages:
                filtered_results = [r for r in all_results if r.stage in stages]
                if not filtered_results:
                    logger.warning(f"Nerasta rezultatų su nurodytais etapais: {', '.join(stages)}")
                    return False
            
            # Grupuojame rezultatus pagal metrikas
            for metric_name in metric_names:
                # Filtruojame pagal metrikos pavadinimą
                metric_results = [r for r in filtered_results if r.metric_name == metric_name]
                
                if not metric_results:
                    logger.warning(f"Nerasta rezultatų metrikoms: {metric_name}")
                    continue
                    
                # Rikiuojame pagal sukūrimo datą
                metric_results.sort(key=lambda r: r.created_at)
                
                # Grupuojame pagal etapą, jei jis yra
                for stage in set(r.stage for r in metric_results if r.stage) or [None]:
                    # Jei etapai filtruojami ir šio etapo nėra sąraše, praleidžiame
                    if stages and stage not in stages:
                        continue
                        
                    # Filtruojame pagal etapą
                    stage_results = [r for r in metric_results if r.stage == stage]
                    
                    if not stage_results:
                        continue
                    
                    # Kuriame raktą etapo ir metrikos kombinacijai
                    key = f"{metric_name}_{stage}" if stage else metric_name
                    
                    # Išsaugome datą ir reikšmę
                    dates = [r.created_at for r in stage_results]
                    values = [float(r.metric_value) for r in stage_results]
                    
                    metrics_data[key] = {
                        "dates": dates,
                        "values": values,
                        "stage": stage,
                        "metric_name": metric_name
                    }
            
            if not metrics_data:
                logger.warning("Nėra tinkamų duomenų vizualizacijai")
                return False
            
            # Sukuriame grafiką
            plt.figure(figsize=figsize)
            
            # Spalvų schema pagal etapus
            stage_colors = {
                "train": "blue",
                "validation": "green",
                "test": "red",
                None: "gray"
            }
            
            # Piešiame kiekvieną metriką
            for key, data in metrics_data.items():
                # Nustatome žymėjimo spalvą pagal etapą
                stage = data["stage"]
                color = stage_colors.get(stage, "black")
                
                # Nustatome linijos stilių
                linestyle = "-"
                if stage == "train":
                    linestyle = "-"
                elif stage == "validation":
                    linestyle = "--"
                elif stage == "test":
                    linestyle = "-."
                
                # Nustatome žymeklį (marker) kas 5 taškus, jei taškų nedaug
                marker = "o" if len(data["values"]) < 20 else None
                markevery = 5 if len(data["values"]) >= 10 else 1
                
                # Piešiame liniją su pavadinimo etikete
                label = f"{data['metric_name']}"
                if stage:
                    label += f" ({stage})"
                
                plt.plot(data["dates"], data["values"], 
                         label=label, color=color, 
                         linestyle=linestyle, 
                         marker=marker, markevery=markevery)
            
            # Nustatome diagramos pavadinimą
            if title:
                plt.title(title)
            else:
                plt.title(f"Eksperimento '{experiment.name}' metrikos")
            
            # Konfiguruojame ašis
            plt.xlabel("Data")
            plt.ylabel("Reikšmė")
            
            # Formatuojame x ašį rodyti datas
            plt.gcf().autofmt_xdate()
            
            # Pridedame tinklelį
            plt.grid(True, linestyle="--", alpha=0.7)
            
            # Pridedame legendą
            plt.legend(loc="best")
            
            # Įtraukiame y ašį nuo nulio, jei reikšmės teigiamos
            if all(min(data["values"]) >= 0 for data in metrics_data.values()):
                plt.ylim(bottom=0)
            
            # Nustatome y ašies formatą taip, kad rodytų sveikus skaičius, jei įmanoma
            plt.gca().yaxis.set_major_locator(MaxNLocator(integer=True))
            
            # Išsaugome paveikslėlį, jei nurodytas failas
            if output_file:
                # Sukuriame direktorijas, jei jų nėra
                os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
                
                # Išsaugome paveikslėlį
                plt.savefig(output_file, dpi=300, bbox_inches="tight")
                logger.info(f"Eksperimento vizualizacija išsaugota į {output_file}")
                plt.close()
                return True
            else:
                # Rodome grafiką interaktyviai
                plt.tight_layout()
                plt.show()
                return True
            
        except ImportError as e:
            logger.error(f"Trūksta reikalingų bibliotekų vizualizacijai: {str(e)}")
            logger.error("Įdiekite matplotlib paketą: pip install matplotlib")
            return False
        except Exception as e:
            logger.error(f"Klaida vizualizuojant eksperimento metrikas: {str(e)}")
            return False

    def visualize_metrics_comparison(self, experiment_id: str, metrics: List[str], 
                                stage: str = None, output_file: str = None,
                                title: str = None, figsize: tuple = (10, 6)) -> bool:
        """
        Vizualizuoja kelių metrikų palyginimą viename eksperimente.
        
        Args:
            experiment_id: Eksperimento ID
            metrics: Metrikų pavadinimai, kuriuos norima palyginti
            stage: Etapas, kuriam norima palyginti metrikas (jei None, naudojami visi)
            output_file: Failo kelias, kur išsaugoti paveikslėlį (jei None, tik rodomas)
            title: Diagramos pavadinimas (jei None, naudojamas eksperimento pavadinimas)
            figsize: Diagramos dydis coliais (plotis, aukštis)
            
        Returns:
            bool: True, jei vizualizacija sėkminga, False kitais atvejais
        """
        # Naudojame pagrindinį vizualizacijos metodą, bet su konkrečiu etapu
        stages = [stage] if stage else None
        return self.visualize_experiment_metrics(
            experiment_id=experiment_id,
            metric_names=metrics,
            stages=stages,
            output_file=output_file,
            title=title,
            figsize=figsize
        )
