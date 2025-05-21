"""
Metrikų eksportavimo ir vizualizacijos modulis.
Skirtas metrikų duomenų eksportavimui įvairiais formatais ir paruošimui vizualizacijoms.
"""
import os
import json
import csv
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
import pandas as pd
from sqlalchemy.orm import Session

# Importuojame reikalingus modelius
from database.models.metrics_models import UserMetric, ModelMetric, SessionMetric
from services.metrics_calculator import MetricsCalculator

# Sukuriame žurnalininką
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MetricsVisualization:
    """
    Metrikų eksportavimo ir vizualizacijos klasė.
    Teikia funkcijas metrikų duomenų eksportavimui ir paruošimui vizualizacijoms.
    """
    
    def __init__(self, db: Session):
        """
        Inicializuoja metrikų vizualizacijos klasę su duomenų bazės sesija.
        
        Args:
            db: SQLAlchemy sesijos objektas
        """
        self.db = db
        self.calculator = MetricsCalculator(db)
        logger.info("Metrikų vizualizacijos modulis inicializuotas")
    
    # ----- Eksportavimo funkcijos -----
    
    def export_user_metrics_to_csv(self, user_id: str, output_path: str, 
                                 metric_type: str = None, 
                                 start_date: datetime = None,
                                 end_date: datetime = None) -> str:
        """
        Eksportuoja naudotojo metrikas į CSV failą.
        
        Args:
            user_id: Naudotojo ID
            output_path: Kelias, kur išsaugoti CSV failą
            metric_type: Metrikos tipas filtravimui (neprivalomas)
            start_date: Pradžios data filtravimui (neprivaloma)
            end_date: Pabaigos data filtravimui (neprivaloma)
            
        Returns:
            str: Išsaugoto failo kelias
        """
        try:
            # Sukuriame užklausą
            query = self.db.query(UserMetric).filter(UserMetric.user_id == user_id)
            
            # Pritaikome filtrus, jei jie nurodyti
            if metric_type:
                query = query.filter(UserMetric.metric_type == metric_type)
            if start_date:
                query = query.filter(UserMetric.timestamp >= start_date)
            if end_date:
                query = query.filter(UserMetric.timestamp <= end_date)
            
            # Vykdome užklausą
            metrics = query.order_by(UserMetric.timestamp.desc()).all()
            
            if not metrics:
                logger.warning(f"Nerasta metrikų naudotojui {user_id} pagal nurodytus filtrus")
                return ""
            
            # Sukuriame direktorijas, jei jų nėra
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Atidarome CSV failą rašymui
            with open(output_path, 'w', newline='', encoding='utf-8') as csv_file:
                # Sukuriame CSV rašytuvą
                writer = csv.writer(csv_file)
                
                # Rašome antraštę
                writer.writerow(['id', 'user_id', 'metric_type', 'metric_name', 'numeric_value', 
                                'string_value', 'time_period', 'timestamp', 'metadata'])
                
                # Rašome metrikų duomenis
                for metric in metrics:
                    writer.writerow([
                        metric.id,
                        metric.user_id,
                        metric.metric_type,
                        metric.metric_name,
                        metric.numeric_value,
                        metric.string_value,
                        metric.time_period,
                        metric.timestamp,
                        metric.metadata
                    ])
            
            logger.info(f"Eksportuotos {len(metrics)} naudotojo {user_id} metrikos į {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Klaida eksportuojant naudotojo metrikas į CSV: {str(e)}")
            return ""
    
    def export_model_metrics_to_csv(self, model_id: str, output_path: str,
                                  metric_type: str = None,
                                  dataset_name: str = None) -> str:
        """
        Eksportuoja modelio metrikas į CSV failą.
        
        Args:
            model_id: Modelio ID
            output_path: Kelias, kur išsaugoti CSV failą
            metric_type: Metrikos tipas filtravimui (neprivalomas)
            dataset_name: Duomenų rinkinio pavadinimas filtravimui (neprivalomas)
            
        Returns:
            str: Išsaugoto failo kelias
        """
        try:
            # Sukuriame užklausą
            query = self.db.query(ModelMetric).filter(ModelMetric.model_id == model_id)
            
            # Pritaikome filtrus, jei jie nurodyti
            if metric_type:
                query = query.filter(ModelMetric.metric_type == metric_type)
            if dataset_name:
                query = query.filter(ModelMetric.dataset_name == dataset_name)
            
            # Vykdome užklausą
            metrics = query.order_by(ModelMetric.timestamp.desc()).all()
            
            if not metrics:
                logger.warning(f"Nerasta metrikų modeliui {model_id} pagal nurodytus filtrus")
                return ""
            
            # Sukuriame direktorijas, jei jų nėra
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Atidarome CSV failą rašymui
            with open(output_path, 'w', newline='', encoding='utf-8') as csv_file:
                # Sukuriame CSV rašytuvą
                writer = csv.writer(csv_file)
                
                # Rašome antraštę
                writer.writerow(['id', 'model_id', 'user_id', 'metric_type', 'metric_name', 
                                'value', 'dataset_name', 'timestamp', 'metadata'])
                
                # Rašome metrikų duomenis
                for metric in metrics:
                    writer.writerow([
                        metric.id,
                        metric.model_id,
                        metric.user_id,
                        metric.metric_type,
                        metric.metric_name,
                        metric.value,
                        metric.dataset_name,
                        metric.timestamp,
                        metric.metadata
                    ])
            
            logger.info(f"Eksportuotos {len(metrics)} modelio {model_id} metrikos į {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Klaida eksportuojant modelio metrikas į CSV: {str(e)}")
            return ""
    
    def export_metrics_to_json(self, metrics: List[Any], output_path: str) -> str:
        """
        Eksportuoja metrikas į JSON failą.
        
        Args:
            metrics: Metrikų sąrašas
            output_path: Kelias, kur išsaugoti JSON failą
            
        Returns:
            str: Išsaugoto failo kelias
        """
        try:
            if not metrics:
                logger.warning("Nėra metrikų eksportavimui į JSON")
                return ""
            
            # Sukuriame direktorijas, jei jų nėra
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Konvertuojame metrikas į žodynus
            metrics_data = []
            for metric in metrics:
                metric_dict = {c.name: getattr(metric, c.name) for c in metric.__table__.columns}
                
                # Konvertuojame datą į string
                if 'timestamp' in metric_dict and metric_dict['timestamp']:
                    metric_dict['timestamp'] = metric_dict['timestamp'].isoformat()
                
                # Konvertuojame metadata string į žodyną, jei tai JSON
                if 'metadata' in metric_dict and metric_dict['metadata']:
                    try:
                        metric_dict['metadata'] = json.loads(metric_dict['metadata'])
                    except:
                        pass  # Jei nepavyksta JSON parse, paliekame kaip string
                
                metrics_data.append(metric_dict)
            
            # Rašome į JSON failą
            with open(output_path, 'w', encoding='utf-8') as json_file:
                json.dump(metrics_data, json_file, indent=4, ensure_ascii=False)
            
            logger.info(f"Eksportuotos {len(metrics)} metrikos į {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Klaida eksportuojant metrikas į JSON: {str(e)}")
            return ""
    
    def export_metrics_to_excel(self, metrics: List[Any], output_path: str) -> str:
        """
        Eksportuoja metrikas į Excel failą.
        
        Args:
            metrics: Metrikų sąrašas
            output_path: Kelias, kur išsaugoti Excel failą
            
        Returns:
            str: Išsaugoto failo kelias
        """
        try:
            if not metrics:
                logger.warning("Nėra metrikų eksportavimui į Excel")
                return ""
            
            # Sukuriame direktorijas, jei jų nėra
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Konvertuojame metrikas į žodynus
            metrics_data = []
            for metric in metrics:
                metric_dict = {c.name: getattr(metric, c.name) for c in metric.__table__.columns}
                metrics_data.append(metric_dict)
            
            # Sukuriame pandas DataFrame
            df = pd.DataFrame(metrics_data)
            
            # Išsaugome į Excel
            df.to_excel(output_path, index=False)
            
            logger.info(f"Eksportuotos {len(metrics)} metrikos į {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Klaida eksportuojant metrikas į Excel: {str(e)}")
            return ""
    
    # ----- Duomenų paruošimas vizualizacijoms -----
    
    def prepare_time_series_data(self, user_id: str, metric_name: str,
                               start_date: datetime, end_date: datetime,
                               period: str = "daily") -> Dict[str, Any]:
        """
        Paruošia laiko eilutės duomenis vizualizacijoms.
        
        Args:
            user_id: Naudotojo ID
            metric_name: Metrikos pavadinimas
            start_date: Pradžios data
            end_date: Pabaigos data
            period: Agregavimo periodas ("daily", "weekly", "monthly")
            
        Returns:
            Dict: Duomenys, paruošti laiko eilutės vizualizacijai
        """
        try:
            # Naudojame metrikų skaičiuoklės agregatoriaus funkciją
            aggregated_metrics = self.calculator.aggregate_metrics_by_period(
                user_id, metric_name, start_date, end_date, period
            )
            
            if not aggregated_metrics:
                logger.warning(f"Nerasta duomenų metrikoms '{metric_name}' laiko eilutės vizualizacijai")
                return {
                    "labels": [],
                    "values": [],
                    "title": f"{metric_name} ({period})",
                    "status": "no_data"
                }
            
            # Formuojame duomenis vizualizacijai
            labels = []
            values = []
            
            for metric in aggregated_metrics:
                # Formatuojame datą pagal periodą
                if period == "daily":
                    label = metric['period'].strftime("%Y-%m-%d")
                elif period == "weekly":
                    label = f"{metric['period'].strftime('%Y-%m-%d')} savaitė"
                elif period == "monthly":
                    label = metric['period'].strftime("%Y-%m")
                else:
                    label = str(metric['period'])
                
                labels.append(label)
                values.append(metric['average_value'])
            
            # Sukuriame vizualizacijos duomenų žodyną
            viz_data = {
                "labels": labels,
                "values": values,
                "title": f"{metric_name} ({period})",
                "status": "success"
            }
            
            logger.info(f"Paruošti laiko eilutės duomenys metrikoms '{metric_name}'")
            return viz_data
            
        except Exception as e:
            logger.error(f"Klaida ruošiant laiko eilutės duomenis: {str(e)}")
            return {
                "labels": [],
                "values": [],
                "title": f"{metric_name} ({period})",
                "status": "error",
                "message": str(e)
            }
    
    def prepare_comparison_data(self, model_ids: List[str], metric_name: str,
                              dataset_name: str = None) -> Dict[str, Any]:
        """
        Paruošia modelių palyginimo duomenis vizualizacijoms.
        
        Args:
            model_ids: Modelių ID sąrašas
            metric_name: Metrikos pavadinimas
            dataset_name: Duomenų rinkinio pavadinimas filtravimui (neprivalomas)
            
        Returns:
            Dict: Duomenys, paruošti modelių palyginimo vizualizacijai
        """
        try:
            if not model_ids:
                logger.warning("Nepateikta modelių ID palyginimui")
                return {
                    "labels": [],
                    "values": [],
                    "title": f"{metric_name} modelių palyginimas",
                    "status": "no_data"
                }
            
            # Paruošiame duomenis kiekvienam modeliui
            labels = []
            values = []
            
            for model_id in model_ids:
                # Gauname naujausią metrikos reikšmę modeliui
                query = self.db.query(ModelMetric).filter(
                    ModelMetric.model_id == model_id,
                    ModelMetric.metric_name == metric_name
                )
                
                if dataset_name:
                    query = query.filter(ModelMetric.dataset_name == dataset_name)
                
                latest_metric = query.order_by(ModelMetric.timestamp.desc()).first()
                
                if latest_metric:
                    # Gauname modelio pavadinimą
                    from database.models.model_models import Model
                    model = self.db.query(Model).filter(Model.id == model_id).first()
                    model_name = model.name if model else model_id
                    
                    labels.append(model_name)
                    values.append(latest_metric.value)
            
            if not labels:
                logger.warning(f"Nerasta duomenų metrikoms '{metric_name}' modelių palyginimui")
                return {
                    "labels": [],
                    "values": [],
                    "title": f"{metric_name} modelių palyginimas",
                    "status": "no_data"
                }
            
            # Sukuriame vizualizacijos duomenų žodyną
            viz_data = {
                "labels": labels,
                "values": values,
                "title": f"{metric_name} modelių palyginimas" + (f" ({dataset_name})" if dataset_name else ""),
                "status": "success"
            }
            
            logger.info(f"Paruošti modelių palyginimo duomenys metrikoms '{metric_name}'")
            return viz_data
            
        except Exception as e:
            logger.error(f"Klaida ruošiant modelių palyginimo duomenis: {str(e)}")
            return {
                "labels": [],
                "values": [],
                "title": f"{metric_name} modelių palyginimas",
                "status": "error",
                "message": str(e)
            }
    
    def prepare_distribution_data(self, user_id: str, metric_name: str,
                                start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Paruošia metrikos reikšmių pasiskirstymo duomenis vizualizacijoms.
        
        Args:
            user_id: Naudotojo ID
            metric_name: Metrikos pavadinimas
            start_date: Pradžios data
            end_date: Pabaigos data
            
        Returns:
            Dict: Duomenys, paruošti pasiskirstymo vizualizacijai
        """
        try:
            # Gauname visas metrikos reikšmes nurodytu laikotarpiu
            metrics = self.db.query(UserMetric).filter(
                UserMetric.user_id == user_id,
                UserMetric.metric_name == metric_name,
                UserMetric.timestamp >= start_date,
                UserMetric.timestamp <= end_date
            ).all()
            
            if not metrics:
                logger.warning(f"Nerasta duomenų metrikoms '{metric_name}' pasiskirstymo vizualizacijai")
                return {
                    "values": [],
                    "title": f"{metric_name} reikšmių pasiskirstymas",
                    "status": "no_data"
                }
            
            # Gauname visas skaitines reikšmes
            values = [m.numeric_value for m in metrics if m.numeric_value is not None]
            
            if not values:
                logger.warning(f"Nerasta skaitinių reikšmių metrikoms '{metric_name}' pasiskirstymo vizualizacijai")
                return {
                    "values": [],
                    "title": f"{metric_name} reikšmių pasiskirstymas",
                    "status": "no_data"
                }
            
            # Sukuriame vizualizacijos duomenų žodyną
            viz_data = {
                "values": values,
                "title": f"{metric_name} reikšmių pasiskirstymas",
                "status": "success",
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values),
                "median": sorted(values)[len(values) // 2]  # Paprastas medianos skaičiavimas
            }
            
            logger.info(f"Paruošti pasiskirstymo duomenys metrikoms '{metric_name}'")
            return viz_data
            
        except Exception as e:
            logger.error(f"Klaida ruošiant pasiskirstymo duomenis: {str(e)}")
            return {
                "values": [],
                "title": f"{metric_name} reikšmių pasiskirstymas",
                "status": "error",
                "message": str(e)
            }