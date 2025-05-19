import os
import json
import datetime
import matplotlib.pyplot as plt
import io
import base64
from app.models.training_session import TrainingSession

class TrainingHistoryService:
    """
    Servisas, skirtas valdyti treniravimo sesijų istoriją
    """
    
    def __init__(self):
        """
        Inicializuoja treniravimo istorijos servisą
        """
        # Nustatome duomenų saugojimo katalogą
        self.data_dir = os.path.join('app', 'data', 'training_history')
        
        # Sukuriame katalogą, jei jis neegzistuoja
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def create_session(self, name=None, model_architecture=None, hyperparameters=None, description=None):
        """
        Sukuria naują treniravimo sesiją
        
        Args:
            name (str): Sesijos pavadinimas
            model_architecture (str): Modelio architektūros aprašymas
            hyperparameters (dict): Hiperparametrų žodynas
            description (str): Sesijos aprašymas
            
        Returns:
            TrainingSession: Sukurta sesija
        """
        # Sukuriame naują sesiją
        session = TrainingSession(name, model_architecture, hyperparameters, description)
        
        # Išsaugome sesiją
        self._save_session(session)
        
        return session
    
    def get_session(self, session_id):
        """
        Gauna sesiją pagal ID
        
        Args:
            session_id (str): Sesijos ID
            
        Returns:
            TrainingSession: Sesijos objektas arba None, jei sesija nerasta
        """
        # Patikriname, ar egzistuoja sesijos failas
        session_path = os.path.join(self.data_dir, f"{session_id}.json")
        
        if not os.path.exists(session_path):
            return None
        
        # Nuskaitome sesijos duomenis
        try:
            with open(session_path, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
                return TrainingSession.from_dict(session_data)
        except Exception as e:
            print(f"Klaida nuskaitant sesiją: {str(e)}")
            return None
    
    def update_session(self, session):
        """
        Atnaujina sesiją
        
        Args:
            session (TrainingSession): Sesijos objektas
            
        Returns:
            bool: True, jei sėkmingai atnaujinta, False priešingu atveju
        """
        return self._save_session(session)
    
    def delete_session(self, session_id):
        """
        Ištrina sesiją
        
        Args:
            session_id (str): Sesijos ID
            
        Returns:
            bool: True, jei sėkmingai ištrinta, False priešingu atveju
        """
        # Patikriname, ar egzistuoja sesijos failas
        session_path = os.path.join(self.data_dir, f"{session_id}.json")
        
        if not os.path.exists(session_path):
            return False
        
        # Triname failą
        try:
            os.remove(session_path)
            return True
        except Exception as e:
            print(f"Klaida trinant sesiją: {str(e)}")
            return False
    
    def get_all_sessions(self):
        """
        Gauna visas treniravimo sesijas
        
        Returns:
            list: Visų sesijų sąrašas
        """
        sessions = []
        
        # Tikriname, ar katalogas egzistuoja
        if not os.path.exists(self.data_dir):
            return sessions
        
        # Einame per visus JSON failus
        for filename in os.listdir(self.data_dir):
            if not filename.endswith('.json'):
                continue
                
            # Nuskaitome sesijos duomenis
            try:
                session_path = os.path.join(self.data_dir, filename)
                with open(session_path, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                    sessions.append(TrainingSession.from_dict(session_data))
            except Exception as e:
                print(f"Klaida nuskaitant sesiją {filename}: {str(e)}")
        
        # Rikiuojame sesijas pagal sukūrimo datą (naujausios pirma)
        sessions.sort(key=lambda s: s.created_at, reverse=True)
        
        return sessions
    
    def get_filtered_sessions(self, keyword=None, status=None, date_from=None, date_to=None):
        """
        Gauna filtruotas sesijas
        
        Args:
            keyword (str): Raktinis žodis pavadinime arba aprašyme
            status (str): Sesijos statusas
            date_from (datetime): Pradžios data
            date_to (datetime): Pabaigos data
            
        Returns:
            list: Filtruotų sesijų sąrašas
        """
        # Gauname visas sesijas
        sessions = self.get_all_sessions()
        
        # Filtruojame pagal raktinį žodį
        if keyword:
            keyword = keyword.lower()
            sessions = [s for s in sessions if keyword in s.name.lower() or 
                        (s.description and keyword in s.description.lower())]
        
        # Filtruojame pagal statusą
        if status:
            sessions = [s for s in sessions if s.status == status]
        
        # Filtruojame pagal pradžios datą
        if date_from:
            sessions = [s for s in sessions if s.created_at >= date_from]
        
        # Filtruojame pagal pabaigos datą
        if date_to:
            sessions = [s for s in sessions if s.created_at <= date_to]
        
        return sessions
    
    def generate_history_chart(self, session_id, metric='loss'):
        """
        Generuoja mokymosi istorijos grafiką
        
        Args:
            session_id (str): Sesijos ID
            metric (str): Metrika, kurią reikia atvaizduoti (loss, accuracy, val_loss, val_accuracy)
            
        Returns:
            str: Base64 koduotas grafiko paveikslėlis arba None, jei įvyko klaida
        """
        # Gauname sesiją
        session = self.get_session(session_id)
        
        if not session:
            return None
        
        # Patikriname, ar yra istorijos duomenys
        if not session.history or metric not in session.history or not session.history[metric]:
            return None
        
        # Sukuriame grafiką
        plt.figure(figsize=(10, 6))
        plt.plot(session.history[metric], label=metric)
        
        # Jei turime validavimo metriką, atvaizduojame ir ją
        val_metric = f"val_{metric}"
        if val_metric in session.history and session.history[val_metric]:
            plt.plot(session.history[val_metric], label=val_metric)
        
        # Nustatome grafiko parametrus
        plt.title(f"{session.name} - {metric.capitalize()} istorija")
        plt.xlabel("Epocha")
        plt.ylabel(metric.capitalize())
        plt.legend()
        plt.grid(True)
        
        # Konvertuojame grafiką į Base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        plt.close()
        buffer.seek(0)
        
        # Koduojame grafiką Base64 formatu
        return base64.b64encode(buffer.read()).decode('utf-8')
    
    def _save_session(self, session):
        """
        Išsaugo sesiją į failą
        
        Args:
            session (TrainingSession): Sesijos objektas
            
        Returns:
            bool: True, jei sėkmingai išsaugota, False priešingu atveju
        """
        # Konvertuojame sesiją į žodyną
        session_data = session.to_dict()
        
        # Nustatome failo kelią
        session_path = os.path.join(self.data_dir, f"{session.session_id}.json")
        
        # Išsaugome duomenis
        try:
            with open(session_path, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            print(f"Klaida išsaugant sesiją: {str(e)}")
            return False
            
    def generate_comparison_chart(self, session_ids, metric='loss'):
        """
        Generuoja palyginimo grafiką kelioms sesijoms
        
        Args:
            session_ids (list): Sesijų ID sąrašas
            metric (str): Metrika, kurią reikia atvaizduoti (loss, accuracy, val_loss, val_accuracy)
            
        Returns:
            str: Base64 koduotas grafiko paveikslėlis arba None, jei įvyko klaida
        """
        if not session_ids:
            return None
        
        # Sukuriame grafiką
        plt.figure(figsize=(12, 7))
        
        # Einame per visas sesijas
        for session_id in session_ids:
            session = self.get_session(session_id)
            
            if not session or not session.history or metric not in session.history or not session.history[metric]:
                continue
            
            # Atvaizduojame metriką
            plt.plot(session.history[metric], label=f"{session.name} ({metric})")
        
        # Nustatome grafiko parametrus
        plt.title(f"Sesijų palyginimas - {metric.capitalize()}")
        plt.xlabel("Epocha")
        plt.ylabel(metric.capitalize())
        plt.legend()
        plt.grid(True)
        
        # Konvertuojame grafiką į Base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        plt.close()
        buffer.seek(0)
        
        # Koduojame grafiką Base64 formatu
        return base64.b64encode(buffer.read()).decode('utf-8')