import os
import json
from app.models.parameter_template import ParameterTemplate

class ParameterTemplateService:
    """
    Servisas darbui su parametrų šablonais
    """
    
    def __init__(self, storage_dir):
        """
        Inicializuoja servisą
        
        Args:
            storage_dir (str): Direktorija šablonams saugoti
        """
        self.storage_dir = storage_dir
        
        # Sukuriame direktoriją, jei ji neegzistuoja
        os.makedirs(storage_dir, exist_ok=True)
        
    def save_template(self, template):
        """
        Išsaugo parametrų šabloną
        
        Args:
            template (ParameterTemplate): Parametrų šablonas
            
        Returns:
            bool: True, jei išsaugota sėkmingai
        """
        # Konvertuojame šabloną į žodyną
        data = template.to_dict()
        
        # Išsaugome failą
        filename = os.path.join(self.storage_dir, f"{template.template_id}.json")
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Klaida išsaugant šabloną: {e}")
            return False
            
    def load_template(self, template_id):
        """
        Užkrauna parametrų šabloną
        
        Args:
            template_id (str): Šablono ID
            
        Returns:
            ParameterTemplate: Užkrautas šablonas arba None
        """
        filename = os.path.join(self.storage_dir, f"{template_id}.json")
        
        if not os.path.exists(filename):
            return None
            
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Sukuriame šabloną iš žodyno
            return ParameterTemplate.from_dict(data)
        except Exception as e:
            print(f"Klaida užkraunant šabloną: {e}")
            return None
            
    def delete_template(self, template_id):
        """
        Ištrina parametrų šabloną
        
        Args:
            template_id (str): Šablono ID
            
        Returns:
            bool: True, jei ištrinta sėkmingai
        """
        filename = os.path.join(self.storage_dir, f"{template_id}.json")
        
        if not os.path.exists(filename):
            return False
            
        try:
            os.remove(filename)
            return True
        except Exception as e:
            print(f"Klaida ištrinant šabloną: {e}")
            return False
            
    def get_all_templates(self):
        """
        Grąžina visus parametrų šablonus
        
        Returns:
            list: Šablonų sąrašas
        """
        templates = []
        
        # Ieškome visų .json failų direktorijoje
        for filename in os.listdir(self.storage_dir):
            if filename.endswith('.json'):
                template_id = filename[:-5]  # Pašaliname .json galūnę
                template = self.load_template(template_id)
                
                if template:
                    templates.append(template)
                    
        # Rikiuojame pagal sukūrimo datą (naujausi viršuje)
        templates.sort(key=lambda x: x.created_at, reverse=True)
        
        return templates
        
    def create_from_optimization(self, session, name=None):
        """
        Sukuria ir išsaugo šabloną iš optimizavimo sesijos
        
        Args:
            session (OptimizationSession): Optimizavimo sesija
            name (str): Pasirinktinis šablono pavadinimas
            
        Returns:
            ParameterTemplate: Sukurtas šablonas arba None
        """
        try:
            # Sukuriame šabloną
            template = ParameterTemplate.from_optimization_session(session, name)
            
            # Išsaugome šabloną
            if self.save_template(template):
                return template
        except Exception as e:
            print(f"Klaida kuriant šabloną iš optimizavimo: {e}")
            
        return None