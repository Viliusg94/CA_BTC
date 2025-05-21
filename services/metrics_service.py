"""
Metrikų servisas.
Šis modulis apibrėžia metrikų serviso klasę, skirtą dirbti su įvairiomis metrikomis.
"""
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Union
from sqlalchemy.orm import Session
from sqlalchemy import func
import os

# Importuojame metrikų modelius
from database.models.metrics_models import UserMetric, ModelMetric, SessionMetric
from services.metrics_visualization import MetricsVisualization

# Sukuriame žurnalininką
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MetricsService:
    """
    Metrikų serviso klasė, skirta darbui su naudotojų, modelių ir sesijų metrikomis.
    """
    
    def __init__(self, db: Session):
        """
        Inicializuoja metrikų servisą su duomenų bazės sesija.
        
        Args:
            db: SQLAlchemy sesijos objektas
        """
        self.db = db
        logger.info("Metrikų servisas inicializuotas")
    
    # ----- Naudotojo metrikos -----
    
    def create_user_metric(self, user_id: str, metric_type: str, metric_name: str, 
                           numeric_value: float = None, string_value: str = None,
                           time_period: str = None, metadata: Dict = None) -> UserMetric:
        """
        Sukuria naują naudotojo metriką.
        
        Args:
            user_id: Naudotojo ID
            metric_type: Metrikos tipas (accuracy, usage, performance)
            metric_name: Metrikos pavadinimas
            numeric_value: Skaitinė reikšmė (jei yra)
            string_value: Tekstinė reikšmė (jei yra)
            time_period: Laiko periodas (daily, weekly, monthly, yearly)
            metadata: Papildoma informacija JSON formatu
            
        Returns:
            UserMetric: Sukurta metrika
        """
        try:
            # Paverčiame metadata į JSON tekstą, jei ji pateikta
            metadata_json = json.dumps(metadata) if metadata else None
            
            # Sukuriame metriką
            metric = UserMetric(
                user_id=user_id,
                metric_type=metric_type,
                metric_name=metric_name,
                numeric_value=numeric_value,
                string_value=string_value,
                time_period=time_period,
                metadata=metadata_json,
                timestamp=datetime.now(timezone.utc)
            )
            
            # Pridedame į duomenų bazę
            self.db.add(metric)
            self.db.commit()
            self.db.refresh(metric)
            
            logger.info(f"Sukurta naudotojo metrika: {metric_type} - {metric_name} naudotojui {user_id}")
            return metric
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Klaida kuriant naudotojo metriką: {str(e)}")
            raise
    
    def get_user_metrics(self, user_id: str, metric_type: str = None, 
                        metric_name: str = None, time_period: str = None,
                        limit: int = 100) -> List[UserMetric]:
        """
        Gauna naudotojo metrikas pagal nurodytus filtrus.
        
        Args:
            user_id: Naudotojo ID
            metric_type: Metrikos tipas (jei norima filtruoti)
            metric_name: Metrikos pavadinimas (jei norima filtruoti)
            time_period: Laiko periodas (jei norima filtruoti)
            limit: Maksimalus grąžinamų rezultatų skaičius
            
        Returns:
            List[UserMetric]: Metrikų sąrašas
        """
        try:
            # Pradedame užklausą
            query = self.db.query(UserMetric).filter(UserMetric.user_id == user_id)
            
            # Pridedame filtrus, jei jie nurodyti
            if metric_type:
                query = query.filter(UserMetric.metric_type == metric_type)
            if metric_name:
                query = query.filter(UserMetric.metric_name == metric_name)
            if time_period:
                query = query.filter(UserMetric.time_period == time_period)
            
            # Rikiuojame pagal laiko žymą mažėjančia tvarka ir ribojame rezultatus
            metrics = query.order_by(UserMetric.timestamp.desc()).limit(limit).all()
            
            logger.info(f"Gauta {len(metrics)} naudotojo {user_id} metrikų")
            return metrics
            
        except Exception as e:
            logger.error(f"Klaida gaunant naudotojo metrikas: {str(e)}")
            raise
    
    # ----- Modelio metrikos -----
    
    def create_model_metric(self, model_id: str, metric_type: str, metric_name: str, 
                           value: float, user_id: str = None, dataset_name: str = None,
                           metadata: Dict = None) -> ModelMetric:
        """
        Sukuria naują modelio metriką.
        
        Args:
            model_id: Modelio ID
            metric_type: Metrikos tipas (accuracy, training, testing)
            metric_name: Metrikos pavadinimas
            value: Metrikos reikšmė
            user_id: Naudotojo ID, kuris atliko matavimą (jei yra)
            dataset_name: Duomenų rinkinio pavadinimas (jei yra)
            metadata: Papildoma informacija JSON formatu
            
        Returns:
            ModelMetric: Sukurta metrika
        """
        try:
            # Paverčiame metadata į JSON tekstą, jei ji pateikta
            metadata_json = json.dumps(metadata) if metadata else None
            
            # Sukuriame metriką
            metric = ModelMetric(
                model_id=model_id,
                user_id=user_id,
                metric_type=metric_type,
                metric_name=metric_name,
                value=value,
                dataset_name=dataset_name,
                metadata=metadata_json,
                timestamp=datetime.now(timezone.utc)
            )
            
            # Pridedame į duomenų bazę
            self.db.add(metric)
            self.db.commit()
            self.db.refresh(metric)
            
            logger.info(f"Sukurta modelio metrika: {metric_type} - {metric_name} modeliui {model_id}")
            return metric
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Klaida kuriant modelio metriką: {str(e)}")
            raise
    
    def get_model_metrics(self, model_id: str, metric_type: str = None, 
                         metric_name: str = None, dataset_name: str = None,
                         limit: int = 100) -> List[ModelMetric]:
        """
        Gauna modelio metrikas pagal nurodytus filtrus.
        
        Args:
            model_id: Modelio ID
            metric_type: Metrikos tipas (jei norima filtruoti)
            metric_name: Metrikos pavadinimas (jei norima filtruoti)
            dataset_name: Duomenų rinkinio pavadinimas (jei norima filtruoti)
            limit: Maksimalus grąžinamų rezultatų skaičius
            
        Returns:
            List[ModelMetric]: Metrikų sąrašas
        """
        try:
            # Pradedame užklausą
            query = self.db.query(ModelMetric).filter(ModelMetric.model_id == model_id)
            
            # Pridedame filtrus, jei jie nurodyti
            if metric_type:
                query = query.filter(ModelMetric.metric_type == metric_type)
            if metric_name:
                query = query.filter(ModelMetric.metric_name == metric_name)
            if dataset_name:
                query = query.filter(ModelMetric.dataset_name == dataset_name)
            
            # Rikiuojame pagal laiko žymą mažėjančia tvarka ir ribojame rezultatus
            metrics = query.order_by(ModelMetric.timestamp.desc()).limit(limit).all()
            
            logger.info(f"Gauta {len(metrics)} modelio {model_id} metrikų")
            return metrics
            
        except Exception as e:
            logger.error(f"Klaida gaunant modelio metrikas: {str(e)}")
            raise
    
    # ----- Sesijos metrikos -----
    
    def create_session_metric(self, session_id: str, metric_type: str, metric_name: str, 
                             numeric_value: float = None, string_value: str = None,
                             metadata: Dict = None) -> SessionMetric:
        """
        Sukuria naują sesijos metriką.
        
        Args:
            session_id: Sesijos ID
            metric_type: Metrikos tipas (duration, resource, performance)
            metric_name: Metrikos pavadinimas
            numeric_value: Skaitinė reikšmė (jei yra)
            string_value: Tekstinė reikšmė (jei yra)
            metadata: Papildoma informacija JSON formatu
            
        Returns:
            SessionMetric: Sukurta metrika
        """
        try:
            # Paverčiame metadata į JSON tekstą, jei ji pateikta
            metadata_json = json.dumps(metadata) if metadata else None
            
            # Sukuriame metriką
            metric = SessionMetric(
                session_id=session_id,
                metric_type=metric_type,
                metric_name=metric_name,
                numeric_value=numeric_value,
                string_value=string_value,
                metadata=metadata_json,
                timestamp=datetime.now(timezone.utc)
            )
            
            # Pridedame į duomenų bazę
            self.db.add(metric)
            self.db.commit()
            self.db.refresh(metric)
            
            logger.info(f"Sukurta sesijos metrika: {metric_type} - {metric_name} sesijai {session_id}")
            return metric
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Klaida kuriant sesijos metriką: {str(e)}")
            raise
    
    def get_session_metrics(self, session_id: str, metric_type: str = None, 
                           metric_name: str = None, limit: int = 100) -> List[SessionMetric]:
        """
        Gauna sesijos metrikas pagal nurodytus filtrus.
        
        Args:
            session_id: Sesijos ID
            metric_type: Metrikos tipas (jei norima filtruoti)
            metric_name: Metrikos pavadinimas (jei norima filtruoti)
            limit: Maksimalus grąžinamų rezultatų skaičius
            
        Returns:
            List[SessionMetric]: Metrikų sąrašas
        """
        try:
            # Pradedame užklausą
            query = self.db.query(SessionMetric).filter(SessionMetric.session_id == session_id)
            
            # Pridedame filtrus, jei jie nurodyti
            if metric_type:
                query = query.filter(SessionMetric.metric_type == metric_type)
            if metric_name:
                query = query.filter(SessionMetric.metric_name == metric_name)
            
            # Rikiuojame pagal laiko žymą mažėjančia tvarka ir ribojame rezultatus
            metrics = query.order_by(SessionMetric.timestamp.desc()).limit(limit).all()
            
            logger.info(f"Gauta {len(metrics)} sesijos {session_id} metrikų")
            return metrics
            
        except Exception as e:
            logger.error(f"Klaida gaunant sesijos metrikas: {str(e)}")
            raise
    
    # ----- Agregavimo ir statistikos metodai -----
    
    def get_user_metrics_summary(self, user_id: str, metric_type: str = None) -> Dict[str, Any]:
        """
        Grąžina naudotojo metrikų suvestinę.
        
        Args:
            user_id: Naudotojo ID
            metric_type: Metrikos tipas filtravimui (neprivalomas)
            
        Returns:
            Dict: Suvestinės objektas
        """
        try:
            # Pradedame užklausą
            query = self.db.query(UserMetric).filter(UserMetric.user_id == user_id)
            
            if metric_type:
                query = query.filter(UserMetric.metric_type == metric_type)
            
            # Gauname metrikų skaičių
            metrics_count = query.count()
            
            # Gauname skirtingų metrikų tipus
            metric_types = query.with_entities(
                UserMetric.metric_type, func.count(UserMetric.id)
            ).group_by(UserMetric.metric_type).all()
            
            # Formuojame suvestinę
            summary = {
                "user_id": user_id,
                "total_metrics": metrics_count,
                "metric_types": {t[0]: t[1] for t in metric_types},
                "last_updated": query.order_by(UserMetric.timestamp.desc()).first().timestamp if metrics_count > 0 else None
            }
            
            logger.info(f"Sugeneruota naudotojo {user_id} metrikų suvestinė")
            return summary
            
        except Exception as e:
            logger.error(f"Klaida gaunant naudotojo metrikų suvestinę: {str(e)}")
            raise
    
    def get_model_metrics_summary(self, model_id: str, metric_type: str = None) -> Dict[str, Any]:
        """
        Grąžina modelio metrikų suvestinę.
        
        Args:
            model_id: Modelio ID
            metric_type: Metrikos tipas filtravimui (neprivalomas)
            
        Returns:
            Dict: Suvestinės objektas
        """
        try:
            # Pradedame užklausą
            query = self.db.query(ModelMetric).filter(ModelMetric.model_id == model_id)
            
            if metric_type:
                query = query.filter(ModelMetric.metric_type == metric_type)
            
            # Gauname metrikų skaičių
            metrics_count = query.count()
            
            # Gauname vidutines accuracy metrikos reikšmes
            accuracy_metrics = query.filter(
                ModelMetric.metric_type == "accuracy"
            ).with_entities(
                ModelMetric.metric_name, func.avg(ModelMetric.value)
            ).group_by(ModelMetric.metric_name).all()
            
            # Formuojame suvestinę
            summary = {
                "model_id": model_id,
                "total_metrics": metrics_count,
                "average_accuracy": {m[0]: m[1] for m in accuracy_metrics},
                "last_updated": query.order_by(ModelMetric.timestamp.desc()).first().timestamp if metrics_count > 0 else None
            }
            
            logger.info(f"Sugeneruota modelio {model_id} metrikų suvestinė")
            return summary
            
        except Exception as e:
            logger.error(f"Klaida gaunant modelio metrikų suvestinę: {str(e)}")
            raise
    
    # ----- Trynimo metodai -----
    
    def delete_user_metrics(self, user_id: str, older_than_days: int = None) -> int:
        """
        Ištrina naudotojo metrikas.
        
        Args:
            user_id: Naudotojo ID
            older_than_days: Ištrinti senesnes nei nurodyta dienų skaičius (neprivalomas)
            
        Returns:
            int: Ištrintų metrikų skaičius
        """
        try:
            # Pradedame užklausą
            query = self.db.query(UserMetric).filter(UserMetric.user_id == user_id)
            
            # Jei nurodytas amžius, filtruojame senesnes metrikas
            if older_than_days:
                cutoff_date = datetime.now(timezone.utc) - timedelta(days=older_than_days)
                query = query.filter(UserMetric.timestamp < cutoff_date)
            
            # Gauname metrikų skaičių prieš ištrinant
            metrics_count = query.count()
            
            # Ištriname metrikas
            query.delete(synchronize_session=False)
            self.db.commit()
            
            logger.info(f"Ištrinta {metrics_count} naudotojo {user_id} metrikų")
            return metrics_count
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Klaida trinant naudotojo metrikas: {str(e)}")
            raise

    # ----- Papildomi metodai -----
    
    def calculate_and_save_session_metrics(self, session_id: str) -> List[SessionMetric]:
        """
        Apskaičiuoja ir išsaugo sesijos metrikas.
        
        Args:
            session_id: Sesijos ID
            
        Returns:
            List[SessionMetric]: Sukurtų sesijos metrikų sąrašas
        """
        try:
            # Importuojame metrikų skaičiavimo klasę
            from services.metrics_calculator import MetricsCalculator
            
            # Inicializuojame skaičiavimo klasę
            calculator = MetricsCalculator(self.db)
            
            # Apskaičiuojame sesijos metrikas
            metrics_data = calculator.calculate_session_metrics(session_id)
            
            # Išsaugome apskaičiuotas metrikas
            saved_metrics = []
            for metric_data in metrics_data:
                metric = self.create_session_metric(
                    session_id=metric_data["session_id"],
                    metric_type=metric_data["metric_type"],
                    metric_name=metric_data["metric_name"],
                    numeric_value=metric_data.get("numeric_value"),
                    string_value=metric_data.get("string_value"),
                    metadata=metric_data.get("metadata", {})
                )
                saved_metrics.append(metric)
            
            logger.info(f"Apskaičiuotos ir išsaugotos {len(saved_metrics)} sesijos metrikos")
            return saved_metrics
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Klaida skaičiuojant ir išsaugant sesijos metrikas: {str(e)}")
            raise

    def calculate_and_save_user_metrics(self, user_id: str, time_period: int = 30) -> List[UserMetric]:
        """
        Apskaičiuoja ir išsaugo naudotojo metrikas.
        
        Args:
            user_id: Naudotojo ID
            time_period: Laikotarpis dienomis
            
        Returns:
            List[UserMetric]: Sukurtų naudotojo metrikų sąrašas
        """
        try:
            # Importuojame metrikų skaičiavimo klasę
            from services.metrics_calculator import MetricsCalculator
            
            # Inicializuojame skaičiavimo klasę
            calculator = MetricsCalculator(self.db)
            
            # Apskaičiuojame naudotojo metrikas
            metrics_data = calculator.calculate_user_session_metrics(user_id, time_period)
            
            # Išsaugome apskaičiuotas metrikas
            saved_metrics = []
            for metric_data in metrics_data:
                # Tikriname, ar metrika yra naudotojo metrika
                if "user_id" in metric_data:
                    metric = self.create_user_metric(
                        user_id=metric_data["user_id"],
                        metric_type=metric_data["metric_type"],
                        metric_name=metric_data["metric_name"],
                        numeric_value=metric_data.get("numeric_value"),
                        string_value=metric_data.get("string_value"),
                        time_period=metric_data.get("time_period"),
                        metadata=metric_data.get("metadata", {})
                    )
                    saved_metrics.append(metric)
            
            logger.info(f"Apskaičiuotos ir išsaugotos {len(saved_metrics)} naudotojo metrikos")
            return saved_metrics
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Klaida skaičiuojant ir išsaugant naudotojo metrikas: {str(e)}")
            raise

    def calculate_and_save_model_metrics(self, model_id: str, dataset_name: str,
                                      predictions: List[float], actual_values: List[float],
                                      user_id: str = None) -> List[ModelMetric]:
        """
        Apskaičiuoja ir išsaugo modelio veikimo metrikas.
        
        Args:
            model_id: Modelio ID
            dataset_name: Duomenų rinkinio pavadinimas
            predictions: Prognozuotos reikšmės
            actual_values: Faktinės reikšmės
            user_id: Naudotojo ID, kuris atlieka matavimą (neprivalomas)
            
        Returns:
            List[ModelMetric]: Sukurtų modelio metrikų sąrašas
        """
        try:
            # Importuojame metrikų skaičiavimo klasę
            from services.metrics_calculator import MetricsCalculator
            
            # Inicializuojame skaičiavimo klasę
            calculator = MetricsCalculator(self.db)
            
            # Apskaičiuojame modelio metrikas
            metrics_data = calculator.calculate_model_performance_metrics(
                model_id, dataset_name, predictions, actual_values
            )
            
            # Išsaugome apskaičiuotas metrikas
            saved_metrics = []
            for metric_data in metrics_data:
                metric = self.create_model_metric(
                    model_id=metric_data["model_id"],
                    metric_type=metric_data["metric_type"],
                    metric_name=metric_data["metric_name"],
                    value=metric_data["value"],
                    user_id=user_id,
                    dataset_name=metric_data["dataset_name"],
                    metadata=metric_data.get("metadata", {})
                )
                saved_metrics.append(metric)
            
            logger.info(f"Apskaičiuotos ir išsaugotos {len(saved_metrics)} modelio metrikos")
            return saved_metrics
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Klaida skaičiuojant ir išsaugant modelio metrikas: {str(e)}")
            raise

    def get_metric_trends(self, user_id: str, metric_name: str, days: int = 90) -> Dict[str, Any]:
        """
        Gauna metrikos tendencijų analizės rezultatus.
        
        Args:
            user_id: Naudotojo ID
            metric_name: Metrikos pavadinimas
            days: Dienų skaičius analizei
            
        Returns:
            Dict: Tendencijų analizės rezultatai
        """
        try:
            # Importuojame metrikų skaičiavimo klasę
            from services.metrics_calculator import MetricsCalculator
            
            # Inicializuojame skaičiavimo klasę
            calculator = MetricsCalculator(self.db)
            
            # Apskaičiuojame metrikos tendencijas
            trends = calculator.calculate_metric_trends(user_id, metric_name, days)
            
            logger.info(f"Gautos '{metric_name}' metrikos tendencijos naudotojui {user_id}")
            return trends
            
        except Exception as e:
            logger.error(f"Klaida gaunant metrikos tendencijas: {str(e)}")
            raise

    def get_aggregated_metrics(self, user_id: str, metric_name: str, start_date: datetime, 
                          end_date: datetime, period: str = "daily") -> List[Dict[str, Any]]:
        """
        Gauna agreguotas metrikas pagal nurodytą laikotarpį.
        
        Args:
            user_id: Naudotojo ID
            metric_name: Metrikos pavadinimas
            start_date: Pradžios data
            end_date: Pabaigos data
            period: Agregavimo periodas ("daily", "weekly", "monthly")
            
        Returns:
            List[Dict]: Agreguotų metrikų sąrašas
        """
        try:
            # Importuojame metrikų skaičiavimo klasę
            from services.metrics_calculator import MetricsCalculator
            
            # Inicializuojame skaičiavimo klasę
            calculator = MetricsCalculator(self.db)
            
            # Gauname agreguotas metrikas
            aggregated_metrics = calculator.aggregate_metrics_by_period(
                user_id, metric_name, start_date, end_date, period
            )
            
            logger.info(f"Gautos agreguotos '{metric_name}' metrikos naudotojui {user_id}")
            return aggregated_metrics
            
        except Exception as e:
            logger.error(f"Klaida gaunant agreguotas metrikas: {str(e)}")
            raise
    
    def export_user_metrics(self, user_id: str, format: str = "csv", 
                      output_path: str = None, metric_type: str = None,
                      start_date = None, end_date = None) -> str:
        """
        Eksportuoja naudotojo metrikas nurodytu formatu.
        
        Args:
            user_id: Naudotojo ID
            format: Eksportavimo formatas (csv, json, excel)
            output_path: Kelias, kur išsaugoti failą (jei nenurodyta, generuojamas automatiškai)
            metric_type: Metrikos tipas filtravimui (neprivalomas)
            start_date: Pradžios data filtravimui (neprivaloma)
            end_date: Pabaigos data filtravimui (neprivaloma)
            
        Returns:
            str: Išsaugoto failo kelias
        """
        try:
            # Inicializuojame vizualizacijos servisą
            viz_service = MetricsVisualization(self.db)
            
            # Jei nenurodytas failo kelias, sugeneruojame
            if not output_path:
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_dir = os.path.join("exports", "metrics")
                os.makedirs(output_dir, exist_ok=True)
                output_path = os.path.join(output_dir, f"user_metrics_{user_id}_{timestamp}.{format}")
            
            # Gauname metrikas
            metrics = self.get_user_metrics(
                user_id=user_id,
                metric_type=metric_type,
                limit=10000  # Didelis skaičius, kad gautume visas metrikas
            )
            
            # Eksportuojame pagal nurodytą formatą
            if format.lower() == "csv":
                return viz_service.export_user_metrics_to_csv(
                    user_id, output_path, metric_type, start_date, end_date
                )
            elif format.lower() == "json":
                return viz_service.export_metrics_to_json(metrics, output_path)
            elif format.lower() == "excel":
                return viz_service.export_metrics_to_excel(metrics, output_path)
            else:
                logger.error(f"Nežinomas eksportavimo formatas: {format}")
                return ""
                
        except Exception as e:
            logger.error(f"Klaida eksportuojant naudotojo metrikas: {str(e)}")
            return ""

    def export_model_metrics(self, model_id: str, format: str = "csv", 
                       output_path: str = None, metric_type: str = None,
                       dataset_name: str = None) -> str:
        """
        Eksportuoja modelio metrikas nurodytu formatu.
        
        Args:
            model_id: Modelio ID
            format: Eksportavimo formatas (csv, json, excel)
            output_path: Kelias, kur išsaugoti failą (jei nenurodyta, generuojamas automatiškai)
            metric_type: Metrikos tipas filtravimui (neprivalomas)
            dataset_name: Duomenų rinkinio pavadinimas filtravimui (neprivalomas)
            
        Returns:
            str: Išsaugoto failo kelias
        """
        try:
            # Inicializuojame vizualizacijos servisą
            viz_service = MetricsVisualization(self.db)
            
            # Jei nenurodytas failo kelias, sugeneruojame
            if not output_path:
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_dir = os.path.join("exports", "metrics")
                os.makedirs(output_dir, exist_ok=True)
                output_path = os.path.join(output_dir, f"model_metrics_{model_id}_{timestamp}.{format}")
            
            # Gauname metrikas
            metrics = self.get_model_metrics(
                model_id=model_id,
                metric_type=metric_type,
                metric_name=None,
                dataset_name=dataset_name,
                limit=10000  # Didelis skaičius, kad gautume visas metrikas
            )
            
            # Eksportuojame pagal nurodytą formatą
            if format.lower() == "csv":
                return viz_service.export_model_metrics_to_csv(
                    model_id, output_path, metric_type, dataset_name
                )
            elif format.lower() == "json":
                return viz_service.export_metrics_to_json(metrics, output_path)
            elif format.lower() == "excel":
                return viz_service.export_metrics_to_excel(metrics, output_path)
            else:
                logger.error(f"Nežinomas eksportavimo formatas: {format}")
                return ""
                
        except Exception as e:
            logger.error(f"Klaida eksportuojant modelio metrikas: {str(e)}")
            return ""

    def prepare_visualization_data(self, data_type: str, **kwargs) -> Dict[str, Any]:
        """
        Paruošia duomenis vizualizacijoms.
        
        Args:
            data_type: Duomenų tipas vizualizacijai ("time_series", "comparison", "distribution")
            **kwargs: Papildomi parametrai, priklausantys nuo vizualizacijos tipo
            
        Returns:
            Dict: Duomenys, paruošti vizualizacijai
        """
        try:
            # Inicializuojame vizualizacijos servisą
            viz_service = MetricsVisualization(self.db)
            
            # Paruošiame duomenis pagal nurodytą tipą
            if data_type == "time_series":
                return viz_service.prepare_time_series_data(
                    user_id=kwargs.get("user_id"),
                    metric_name=kwargs.get("metric_name"),
                    start_date=kwargs.get("start_date"),
                    end_date=kwargs.get("end_date"),
                    period=kwargs.get("period", "daily")
                )
            elif data_type == "comparison":
                return viz_service.prepare_comparison_data(
                    model_ids=kwargs.get("model_ids", []),
                    metric_name=kwargs.get("metric_name"),
                    dataset_name=kwargs.get("dataset_name")
                )
            elif data_type == "distribution":
                return viz_service.prepare_distribution_data(
                    user_id=kwargs.get("user_id"),
                    metric_name=kwargs.get("metric_name"),
                    start_date=kwargs.get("start_date"),
                    end_date=kwargs.get("end_date")
                )
            else:
                logger.error(f"Nežinomas duomenų tipas vizualizacijai: {data_type}")
                return {
                    "status": "error",
                    "message": f"Nežinomas duomenų tipas vizualizacijai: {data_type}"
                }
                
        except Exception as e:
            logger.error(f"Klaida ruošiant duomenis vizualizacijai: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }