import json
import datetime
import uuid
import os
from pathlib import Path

class ParameterTemplate:
    """
    Modelis hiperparametrų šablonams saugoti
    """
    
    def __init__(self, name=None, model_type=None, parameters=None, source='manual'):
        """
        Inicializuoja parametrų šabloną
        
        Args:
            name (str): Šablono pavadinimas
            model_type (str): Modelio tipas, kuriam taikomi parametrai
            parameters (dict): Parametrų reikšmių žodynas
            source (str): Šablono šaltinis (manual, optimization)
        """
        # Generuojame unikalų ID
        self.template_id = str(uuid.uuid4())
        
        # Pagrindinė informacija
        self.name = name or f"Šablonas-{datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}"
        self.model_type = model_type
        self.parameters = parameters or {}
        self.source = source
        
        # Laiko žymės
        self.created_at = datetime.datetime.now()
        self.updated_at = datetime.datetime.now()
    
    def to_dict(self):
        """
        Konvertuoja šabloną į žodyną
        
        Returns:
            dict: Šablono duomenys
        """
        return {
            "template_id": self.template_id,
            "name": self.name,
            "model_type": self.model_type,
            "parameters": self.parameters,
            "source": self.source,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data):
        """
        Sukuria šabloną iš žodyno
        
        Args:
            data (dict): Šablono duomenys
            
        Returns:
            ParameterTemplate: Sukurtas šablonas
        """
        template = cls()
        
        template.template_id = data.get("template_id", str(uuid.uuid4()))
        template.name = data.get("name", "")
        template.model_type = data.get("model_type", "")
        template.parameters = data.get("parameters", {})
        template.source = data.get("source", "manual")
        
        # Konvertuojame laiko žymes
        if "created_at" in data:
            try:
                template.created_at = datetime.datetime.fromisoformat(data["created_at"])
            except (ValueError, TypeError):
                template.created_at = datetime.datetime.now()
        
        if "updated_at" in data:
            try:
                template.updated_at = datetime.datetime.fromisoformat(data["updated_at"])
            except (ValueError, TypeError):
                template.updated_at = datetime.datetime.now()
        
        return template
    
    def save(self, base_dir="data/templates"):
        """
        Išsaugo šabloną į failą
        
        Args:
            base_dir (str): Katalogas, kuriame saugomi šablonai
            
        Returns:
            bool: Ar išsaugojimas pavyko
        """
        try:
            # Sukuriame katalogą, jei jo nėra
            path = Path(base_dir)
            path.mkdir(parents=True, exist_ok=True)
            
            # Atnaujiname laiko žymę
            self.updated_at = datetime.datetime.now()
            
            # Išsaugome į failą
            file_path = path / f"{self.template_id}.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.to_dict(), f, ensure_ascii=False, indent=4)
            
            return True
        except Exception as e:
            print(f"Klaida išsaugant šabloną: {e}")
            return False
    
    @classmethod
    def load(cls, template_id, base_dir="data/templates"):
        """
        Užkrauna šabloną iš failo
        
        Args:
            template_id (str): Šablono ID
            base_dir (str): Katalogas, kuriame saugomi šablonai
            
        Returns:
            ParameterTemplate: Užkrautas šablonas arba None, jei šablonas nerastas
        """
        try:
            file_path = Path(base_dir) / f"{template_id}.json"
            
            if not file_path.exists():
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return cls.from_dict(data)
        except Exception as e:
            print(f"Klaida užkraunant šabloną: {e}")
            return None
    
    @classmethod
    def list_all(cls, base_dir="data/templates"):
        """
        Grąžina visų išsaugotų šablonų sąrašą
        
        Args:
            base_dir (str): Katalogas, kuriame saugomi šablonai
            
        Returns:
            list: Šablonų sąrašas
        """
        templates = []
        path = Path(base_dir)
        
        if not path.exists():
            return templates
        
        for file_path in path.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                template = cls.from_dict(data)
                templates.append(template)
            except Exception as e:
                print(f"Klaida užkraunant šabloną {file_path}: {e}")
        
        # Rūšiuojame pagal sukūrimo datą (naujausi viršuje)
        templates.sort(key=lambda x: x.created_at, reverse=True)
        
        return templates
    
    def delete(self, base_dir="data/templates"):
        """
        Ištrina šabloną
        
        Args:
            base_dir (str): Katalogas, kuriame saugomi šablonai
            
        Returns:
            bool: Ar ištrynimas pavyko
        """
        try:
            file_path = Path(base_dir) / f"{self.template_id}.json"
            
            if file_path.exists():
                file_path.unlink()
            
            return True
        except Exception as e:
            print(f"Klaida trinant šabloną: {e}")
            return False
    
    @classmethod
    def from_optimization_session(cls, session, name=None):
        """
        Sukuria šabloną iš optimizavimo sesijos
        
        Args:
            session (OptimizationSession): Optimizavimo sesija
            name (str): Pasirinktinis šablono pavadinimas
            
        Returns:
            ParameterTemplate: Sukurtas šablonas
        """
        # Patikriname, ar sesija turi geriausius parametrus
        if not session.best_params:
            raise ValueError("Optimizavimo sesija neturi geriausių parametrų")
        
        # Sukuriame šabloną
        template = cls()
        template.name = name or f"{session.model_type} optimizuoti parametrai"
        template.model_type = session.model_type
        template.parameters = session.best_params.copy()
        template.source = "optimization"
        template.source_id = session.session_id
        template.best_score = session.best_score
        
        return template