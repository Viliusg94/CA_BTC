"""
Metrikų skaičiavimo modulis.
Skirtas apskaičiuoti įvairias metrikas remiantis naudotojų sesijomis ir modelių veikimu.
"""
import logging
import json
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional, Union, Tuple
from sqlalchemy import func, desc, and_, or_, extract, case
from sqlalchemy.orm import Session

# Importuojame reikalingus modelius
from database.models.user_models import User, UserSession
from database.models.model_models import Model
from database.models.metrics_models import UserMetric, ModelMetric, SessionMetric

# Sukuriame žurnalininką
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MetricsCalculator:
    """
    Metrikų skaičiavimo klasė.
    Skirta apskaičiuoti ir generuoti metrikas remiantis naudotojų ir sistemų duomenimis.
    """
    
    def __init__(self, db: Session):
        """
        Inicializuoja metrikų skaičiavimo klasę su duomenų bazės sesija.
        
        Args:
            db: SQLAlchemy sesijos objektas
        """
        self.db = db
        logger.info("Metrikų skaičiavimo modulis inicializuotas")
    
    # ---- Sesijų metrikų skaičiavimas ----
    
    def calculate_session_metrics(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Apskaičiuoja įvairias metrikas vienai sesijai.
        
        Args:
            session_id: Sesijos ID
            
        Returns:
            List[Dict]: Apskaičiuotų metrikų sąrašas
        """
        try:
            # Gauname sesijos informaciją
            session = self.db.query(UserSession).filter(UserSession.id == session_id).first()
            if not session:
                logger.warning(f"Sesija su ID {session_id} nerasta")
                return []
            
            metrics = []
            
            # 1. Apskaičiuojame sesijos trukmės metriką
            if session.end_time and session.start_time:
                duration_seconds = (session.end_time - session.start_time).total_seconds()
                metrics.append({
                    "metric_type": "duration",
                    "metric_name": "session_duration_seconds",
                    "numeric_value": duration_seconds,
                    "session_id": session_id
                })
            
            # 2. Apskaičiuojame sesijos statuso metriką
            metrics.append({
                "metric_type": "status",
                "metric_name": "session_status",
                "string_value": session.status,
                "session_id": session_id
            })
            
            # 3. Metrika apie sesijos tipą
            metrics.append({
                "metric_type": "type",
                "metric_name": "session_type",
                "string_value": session.session_type,
                "session_id": session_id
            })
            
            # Jei tai yra treniravimo sesija, galime pridėti papildomų metrikų
            if session.session_type == "training":
                # Šią metriką reikėtų pakeisti pagal realius duomenis
                metrics.append({
                    "metric_type": "performance",
                    "metric_name": "training_completed",
                    "numeric_value": 1.0 if session.status == "completed" else 0.0,
                    "session_id": session_id
                })
            
            logger.info(f"Apskaičiuotos {len(metrics)} metrikos sesijai {session_id}")
            return metrics
            
        except Exception as e:
            logger.error(f"Klaida skaičiuojant sesijos metrikas: {str(e)}")
            return []
    
    def calculate_user_session_metrics(self, user_id: str, time_period: Optional[int] = 30) -> List[Dict[str, Any]]:
        """
        Apskaičiuoja metrikas visoms naudotojo sesijoms per nurodytą laikotarpį.
        
        Args:
            user_id: Naudotojo ID
            time_period: Laikotarpis dienomis (numatytasis - 30 dienų)
            
        Returns:
            List[Dict]: Apskaičiuotų metrikų sąrašas
        """
        try:
            # Nustatome laiko ribą
            time_limit = datetime.now(timezone.utc) - timedelta(days=time_period)
            
            # Gauname naudotojo sesijas
            sessions = self.db.query(UserSession).filter(
                UserSession.user_id == user_id,
                UserSession.start_time >= time_limit
            ).all()
            
            if not sessions:
                logger.info(f"Naudotojui {user_id} nerasta sesijų per pastarasias {time_period} dienas")
                return []
            
            all_metrics = []
            
            # Apskaičiuojame metrikas kiekvienai sesijai
            for session in sessions:
                session_metrics = self.calculate_session_metrics(session.id)
                all_metrics.extend(session_metrics)
            
            # Pridedame agreguotas metrikas
            aggregated_metrics = self._calculate_aggregated_session_metrics(user_id, sessions)
            all_metrics.extend(aggregated_metrics)
            
            logger.info(f"Apskaičiuotos {len(all_metrics)} metrikos naudotojui {user_id}")
            return all_metrics
            
        except Exception as e:
            logger.error(f"Klaida skaičiuojant naudotojo sesijų metrikas: {str(e)}")
            return []
    
    def _calculate_aggregated_session_metrics(self, user_id: str, sessions: List[UserSession]) -> List[Dict[str, Any]]:
        """
        Apskaičiuoja agreguotas metrikas iš sesijų sąrašo.
        
        Args:
            user_id: Naudotojo ID
            sessions: Sesijų sąrašas
            
        Returns:
            List[Dict]: Apskaičiuotų metrikų sąrašas
        """
        metrics = []
        
        # Jei nėra sesijų, nieko neskaičiuojame
        if not sessions:
            return metrics
        
        # 1. Sesijų skaičius pagal tipą
        session_types = {}
        for session in sessions:
            if session.session_type not in session_types:
                session_types[session.session_type] = 0
            session_types[session.session_type] += 1
        
        for session_type, count in session_types.items():
            metrics.append({
                "metric_type": "usage",
                "metric_name": f"session_count_{session_type}",
                "numeric_value": count,
                "time_period": "monthly",
                "user_id": user_id
            })
        
        # 2. Bendra sesijų trukmė
        total_duration = 0
        completed_sessions = 0
        
        for session in sessions:
            if session.end_time and session.start_time:
                duration = (session.end_time - session.start_time).total_seconds()
                total_duration += duration
                if session.status == "completed":
                    completed_sessions += 1
        
        # Vidutinė sesijos trukmė
        if sessions:
            avg_duration = total_duration / len(sessions)
            metrics.append({
                "metric_type": "performance",
                "metric_name": "average_session_duration_seconds",
                "numeric_value": avg_duration,
                "time_period": "monthly",
                "user_id": user_id
            })
        
        # 3. Sesijų užbaigimo dažnis
        if sessions:
            completion_rate = (completed_sessions / len(sessions)) * 100
            metrics.append({
                "metric_type": "performance",
                "metric_name": "session_completion_rate",
                "numeric_value": completion_rate,
                "time_period": "monthly",
                "user_id": user_id
            })
        
        return metrics
    
    # ---- Metrikų agregavimas pagal laikotarpį ----
    
    def aggregate_metrics_by_period(self, user_id: str, metric_name: str, 
                                   start_date: datetime, end_date: datetime, 
                                   period: str = "daily") -> List[Dict[str, Any]]:
        """
        Agreguoja metrikas pagal nurodytą laikotarpį.
        
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
            # Pasirenkame tinkamą laiko išraišką pagal periodą
            if period == "daily":
                date_part = func.date(UserMetric.timestamp)
            elif period == "weekly":
                # SQLite ir PostgreSQL skirtingi EXTRACT formatai
                # Čia naudojame func.date_trunc, kuris veikia su PostgreSQL
                date_part = func.date_trunc('week', UserMetric.timestamp)
            elif period == "monthly":
                date_part = func.date_trunc('month', UserMetric.timestamp)
            else:
                logger.error(f"Nežinomas periodo tipas: {period}")
                return []
            
            # Sudarome užklausą agreguotoms metrikoms
            query = self.db.query(
                date_part.label('period'),
                func.avg(UserMetric.numeric_value).label('average_value'),
                func.count(UserMetric.id).label('count')
            ).filter(
                UserMetric.user_id == user_id,
                UserMetric.metric_name == metric_name,
                UserMetric.timestamp >= start_date,
                UserMetric.timestamp <= end_date
            ).group_by('period').order_by('period')
            
            results = query.all()
            
            # Formuojame rezultatų sąrašą
            aggregated_metrics = []
            for result in results:
                aggregated_metrics.append({
                    "period": result.period,
                    "average_value": result.average_value,
                    "count": result.count,
                    "metric_name": metric_name
                })
            
            logger.info(f"Agreguotos {len(aggregated_metrics)} metrikos naudotojui {user_id}")
            return aggregated_metrics
            
        except Exception as e:
            logger.error(f"Klaida agreguojant metrikas pagal periodą: {str(e)}")
            return []
    
    # ---- Metrikų tendencijų analizė ----
    
    def calculate_metric_trends(self, user_id: str, metric_name: str, 
                               days: int = 90, comparison_window: int = 30) -> Dict[str, Any]:
        """
        Apskaičiuoja metrikos tendencijas per nurodytą laikotarpį.
        
        Args:
            user_id: Naudotojo ID
            metric_name: Metrikos pavadinimas
            days: Dienų skaičius analizei
            comparison_window: Palyginimo lango dydis dienomis
            
        Returns:
            Dict: Tendencijų analizės rezultatai
        """
        try:
            current_date = datetime.now(timezone.utc)
            past_date = current_date - timedelta(days=days)
            
            # Gauname visas metrikos reikšmes nurodytu laikotarpiu
            metrics = self.db.query(UserMetric).filter(
                UserMetric.user_id == user_id,
                UserMetric.metric_name == metric_name,
                UserMetric.timestamp >= past_date,
                UserMetric.timestamp <= current_date
            ).order_by(UserMetric.timestamp).all()
            
            if not metrics:
                logger.warning(f"Nerasta metrikų '{metric_name}' naudotojui {user_id} per pastarasias {days} dienas")
                return {
                    "status": "no_data",
                    "message": f"Nerasta metrikų duomenų '{metric_name}' per nurodytą laikotarpį"
                }
            
            # Padalijame duomenis į dabartinį ir ankstesnį laikotarpius
            comparison_date = current_date - timedelta(days=comparison_window)
            
            current_period_metrics = [m for m in metrics if m.timestamp >= comparison_date]
            past_period_metrics = [m for m in metrics if m.timestamp < comparison_date]
            
            # Apskaičiuojame vidurkius abiem laikotarpiams
            current_avg = sum(m.numeric_value for m in current_period_metrics) / len(current_period_metrics) if current_period_metrics else 0
            past_avg = sum(m.numeric_value for m in past_period_metrics) / len(past_period_metrics) if past_period_metrics else 0
            
            # Apskaičiuojame pokytį
            change = current_avg - past_avg
            percent_change = (change / past_avg * 100) if past_avg != 0 else 0
            
            # Nustatome tendenciją
            if percent_change > 5:
                trend = "augimas"
            elif percent_change < -5:
                trend = "mažėjimas"
            else:
                trend = "stabili"
            
            # Formuojame rezultatus
            trend_analysis = {
                "metric_name": metric_name,
                "user_id": user_id,
                "current_period_avg": current_avg,
                "past_period_avg": past_avg,
                "absolute_change": change,
                "percent_change": percent_change,
                "trend": trend,
                "current_period_start": comparison_date,
                "current_period_end": current_date,
                "past_period_start": past_date,
                "past_period_end": comparison_date,
                "data_points_count": len(metrics)
            }
            
            logger.info(f"Apskaičiuotos tendencijos metrikoms '{metric_name}' naudotojui {user_id}")
            return trend_analysis
            
        except Exception as e:
            logger.error(f"Klaida skaičiuojant metrikos tendencijas: {str(e)}")
            return {
                "status": "error",
                "message": f"Klaida skaičiuojant tendencijas: {str(e)}"
            }
    
    # ---- Modelių metrikų skaičiavimas ----
    
    def calculate_model_performance_metrics(self, model_id: str, dataset_name: str,
                                          predictions: List[float], actual_values: List[float]) -> List[Dict[str, Any]]:
        """
        Apskaičiuoja modelio veikimo metrikas pagal pateiktus prognozių ir faktinių reikšmių duomenis.
        
        Args:
            model_id: Modelio ID
            dataset_name: Duomenų rinkinio pavadinimas
            predictions: Prognozuotos reikšmės
            actual_values: Faktinės reikšmės
            
        Returns:
            List[Dict]: Apskaičiuotų metrikų sąrašas
        """
        try:
            # Patikriname, ar sąrašų ilgiai sutampa
            if len(predictions) != len(actual_values):
                logger.error("Prognozių ir faktinių reikšmių sąrašų ilgiai nesutampa")
                return []
            
            if len(predictions) == 0:
                logger.error("Pateikti tušti prognozių ir faktinių reikšmių sąrašai")
                return []
            
            metrics = []
            
            # 1. Vidutinė absoliuti paklaida (MAE)
            mae = sum(abs(p - a) for p, a in zip(predictions, actual_values)) / len(predictions)
            metrics.append({
                "metric_type": "accuracy",
                "metric_name": "mae",
                "value": mae,
                "dataset_name": dataset_name,
                "model_id": model_id
            })
            
            # 2. Vidutinė kvadratinė paklaida (MSE)
            mse = sum((p - a) ** 2 for p, a in zip(predictions, actual_values)) / len(predictions)
            metrics.append({
                "metric_type": "accuracy",
                "metric_name": "mse",
                "value": mse,
                "dataset_name": dataset_name,
                "model_id": model_id
            })
            
            # 3. Šaknis iš vidutinės kvadratinės paklaidos (RMSE)
            rmse = mse ** 0.5
            metrics.append({
                "metric_type": "accuracy",
                "metric_name": "rmse",
                "value": rmse,
                "dataset_name": dataset_name,
                "model_id": model_id
            })
            
            # 4. Vidutinė absoliuti procentinė paklaida (MAPE)
            # Vengiame dalybos iš nulio
            mape_values = [abs((a - p) / a) * 100 for p, a in zip(predictions, actual_values) if a != 0]
            if mape_values:
                mape = sum(mape_values) / len(mape_values)
                metrics.append({
                    "metric_type": "accuracy",
                    "metric_name": "mape",
                    "value": mape,
                    "dataset_name": dataset_name,
                    "model_id": model_id
                })
            
            logger.info(f"Apskaičiuotos {len(metrics)} modelio veikimo metrikos modeliui {model_id}")
            return metrics
            
        except Exception as e:
            logger.error(f"Klaida skaičiuojant modelio veikimo metrikas: {str(e)}")
            return []