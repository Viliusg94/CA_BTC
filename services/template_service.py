# Modelių parametrų šablonų valdymo servisas
import os
import json
import logging
from datetime import datetime

class TemplateService:
    """
    Servisas, skirtas tvarkyti modelių parametrų šablonus
    """
    
    def __init__(self):
        """
        Inicializuoja šablonų servisą
        """
        # Nustatome šablonų direktoriją
        self.TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'templates')
        
        # Sukuriame direktoriją, jei jos dar nėra
        if not os.path.exists(self.TEMPLATES_DIR):
            os.makedirs(self.TEMPLATES_DIR)
            
        # Konfigūruojame logerį
        self.logger = logging.getLogger(__name__)
    
    def save_template(self, template_data):
        """
        Išsaugo naują šabloną
        
        Args:
            template_data (dict): Šablono duomenys
            
        Returns:
            str: Šablono ID arba None, jei įvyko klaida
        """
        try:
            # Jei nėra pavadinimo, grąžiname klaidą
            if 'name' not in template_data or not template_data['name']:
                self.logger.error("Šablonui būtina nurodyti pavadinimą")
                return None
            
            # Sugeneruojame unikalų šablono ID
            template_id = f"template_{int(datetime.now().timestamp())}"
            
            # Pridedame papildomą informaciją
            template_data['template_id'] = template_id
            template_data['created_at'] = datetime.now().isoformat()
            
            # Išsaugome šabloną į failą
            template_path = os.path.join(self.TEMPLATES_DIR, f"{template_id}.json")
            with open(template_path, 'w', encoding='utf-8') as f:
                json.dump(template_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Šablonas '{template_data['name']}' sėkmingai išsaugotas")
            return template_id
            
        except Exception as e:
            self.logger.error(f"Klaida išsaugant šabloną: {str(e)}")
            return None
    
    def get_template(self, template_id):
        """
        Gauna šabloną pagal ID
        
        Args:
            template_id (str): Šablono ID
            
        Returns:
            dict: Šablono duomenys arba None, jei šablonas nerastas
        """
        try:
            template_path = os.path.join(self.TEMPLATES_DIR, f"{template_id}.json")
            if not os.path.exists(template_path):
                self.logger.warning(f"Šablonas su ID {template_id} nerastas")
                return None
            
            with open(template_path, 'r', encoding='utf-8') as f:
                template_data = json.load(f)
            
            return template_data
        
        except Exception as e:
            self.logger.error(f"Klaida gaunant šabloną {template_id}: {str(e)}")
            return None
    
    def update_template(self, template_id, template_data):
        """
        Atnaujina esamą šabloną
        
        Args:
            template_id (str): Šablono ID
            template_data (dict): Nauji šablono duomenys
            
        Returns:
            bool: True, jei atnaujinimas sėkmingas, False - priešingu atveju
        """
        try:
            # Patikriname, ar šablonas egzistuoja
            template_path = os.path.join(self.TEMPLATES_DIR, f"{template_id}.json")
            if not os.path.exists(template_path):
                self.logger.warning(f"Šablonas su ID {template_id} nerastas")
                return False
            
            # Gauname esamą šabloną
            with open(template_path, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
            
            # Atnaujiname duomenis
            existing_data.update(template_data)
            existing_data['updated_at'] = datetime.now().isoformat()
            
            # Išsaugome atnaujintą šabloną
            with open(template_path, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Šablonas '{existing_data['name']}' sėkmingai atnaujintas")
            return True
            
        except Exception as e:
            self.logger.error(f"Klaida atnaujinant šabloną {template_id}: {str(e)}")
            return False
    
    def delete_template(self, template_id):
        """
        Ištrina šabloną
        
        Args:
            template_id (str): Šablono ID
            
        Returns:
            bool: True, jei ištrynimas sėkmingas, False - priešingu atveju
        """
        try:
            # Patikriname, ar šablonas egzistuoja
            template_path = os.path.join(self.TEMPLATES_DIR, f"{template_id}.json")
            if not os.path.exists(template_path):
                self.logger.warning(f"Šablonas su ID {template_id} nerastas")
                return False
            
            # Ištriname šabloną
            os.remove(template_path)
            self.logger.info(f"Šablonas {template_id} sėkmingai ištrintas")
            return True
            
        except Exception as e:
            self.logger.error(f"Klaida trinant šabloną {template_id}: {str(e)}")
            return False
    
    def get_all_templates(self):
        """
        Gauna visų šablonų sąrašą
        
        Returns:
            list: Šablonų sąrašas
        """
        templates = []
        
        try:
            # Gauname visus šablonų failus
            for filename in os.listdir(self.TEMPLATES_DIR):
                if filename.endswith('.json'):
                    template_path = os.path.join(self.TEMPLATES_DIR, filename)
                    
                    with open(template_path, 'r', encoding='utf-8') as f:
                        template_data = json.load(f)
                    
                    templates.append(template_data)
            
            # Rūšiuojame pagal sukūrimo datą (naujausi pirmi)
            templates.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            
            return templates
            
        except Exception as e:
            self.logger.error(f"Klaida gaunant šablonų sąrašą: {str(e)}")
            return []