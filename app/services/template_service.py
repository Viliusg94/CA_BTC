import json
import os
import logging
from datetime import datetime

class TemplateService:
    """
    Parametrų šablonų valdymo servisas
    """
    
    def __init__(self):
        """
        Inicializuoja šablonų servisą
        """
        # Nustatome kelią iki šablonų direktorijos
        self.TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'templates')
        
        # Sukuriame direktoriją, jei jos nėra
        os.makedirs(self.TEMPLATES_DIR, exist_ok=True)
        
        # Inicializuojame žurnalą
        self.logger = logging.getLogger(__name__)
    
    def get_all_templates(self):
        """
        Grąžina visus šablonus
        
        Returns:
            list: Šablonų objektų sąrašas
        """
        templates = []
        
        try:
            # Perskaitome visus JSON failus šablonų direktorijoje
            for filename in os.listdir(self.TEMPLATES_DIR):
                if filename.endswith('.json'):
                    template_path = os.path.join(self.TEMPLATES_DIR, filename)
                    with open(template_path, 'r', encoding='utf-8') as f:
                        template_data = json.load(f)
                        template_name = os.path.splitext(filename)[0]  # Pašaliname .json plėtinį
                        templates.append({
                            'id': template_name,
                            'name': template_data.get('name', template_name),
                            'description': template_data.get('description', ''),
                            'parameters': template_data.get('parameters', {}),
                            'created_at': template_data.get('created_at', ''),
                            'usage_count': template_data.get('usage_count', 0)
                        })
        except Exception as e:
            self.logger.error(f"Klaida skaitant šablonus: {str(e)}")
        
        # Rūšiuojame šablonus pagal naudojimo skaičių (dažniausiai naudojami pirmiausia)
        templates.sort(key=lambda x: x.get('usage_count', 0), reverse=True)
        
        return templates
    
    def get_template(self, template_id):
        """
        Grąžina šabloną pagal ID
        
        Args:
            template_id (str): Šablono identifikatorius
            
        Returns:
            dict: Šablono duomenys arba None, jei šablonas nerastas
        """
        try:
            template_path = os.path.join(self.TEMPLATES_DIR, f"{template_id}.json")
            
            if not os.path.exists(template_path):
                return None
                
            with open(template_path, 'r', encoding='utf-8') as f:
                template_data = json.load(f)
                
            # Pridedame ID
            template_data['id'] = template_id
            
            return template_data
        except Exception as e:
            self.logger.error(f"Klaida gaunant šabloną {template_id}: {str(e)}")
            return None
    
    def create_template(self, name, description, parameters):
        """
        Sukuria naują šabloną
        
        Args:
            name (str): Šablono pavadinimas
            description (str): Šablono aprašymas
            parameters (dict): Šablono parametrai
            
        Returns:
            str: Sukurto šablono ID arba None, jei nepavyko sukurti
        """
        try:
            # Sukuriame šablono objektą
            template_data = {
                'name': name,
                'description': description,
                'parameters': parameters,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'usage_count': 0
            }
            
            # Sukuriame saugų failo pavadinimą
            safe_name = "".join([c if c.isalnum() else "_" for c in name])
            template_id = f"{safe_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Išsaugome šabloną
            template_path = os.path.join(self.TEMPLATES_DIR, f"{template_id}.json")
            with open(template_path, 'w', encoding='utf-8') as f:
                json.dump(template_data, f, indent=2, ensure_ascii=False)
            
            return template_id
        except Exception as e:
            self.logger.error(f"Klaida kuriant šabloną: {str(e)}")
            return None
    
    def update_template(self, template_id, name=None, description=None, parameters=None):
        """
        Atnaujina esamą šabloną
        
        Args:
            template_id (str): Šablono identifikatorius
            name (str, optional): Naujas pavadinimas
            description (str, optional): Naujas aprašymas
            parameters (dict, optional): Nauji parametrai
            
        Returns:
            bool: True, jei sėkmingai atnaujinta, kitaip False
        """
        try:
            # Patikriname, ar šablonas egzistuoja
            template_path = os.path.join(self.TEMPLATES_DIR, f"{template_id}.json")
            
            if not os.path.exists(template_path):
                return False
                
            # Nuskaitome esamą šabloną
            with open(template_path, 'r', encoding='utf-8') as f:
                template_data = json.load(f)
            
            # Atnaujiname duomenis, jei jie pateikti
            if name is not None:
                template_data['name'] = name
                
            if description is not None:
                template_data['description'] = description
                
            if parameters is not None:
                template_data['parameters'] = parameters
            
            # Atnaujiname modifikavimo datą
            template_data['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Išsaugome atnaujintą šabloną
            with open(template_path, 'w', encoding='utf-8') as f:
                json.dump(template_data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            self.logger.error(f"Klaida atnaujinant šabloną {template_id}: {str(e)}")
            return False
    
    def increment_usage_count(self, template_id):
        """
        Padidina šablono naudojimo skaitliuką
        
        Args:
            template_id (str): Šablono identifikatorius
            
        Returns:
            bool: True, jei sėkmingai atnaujinta, kitaip False
        """
        try:
            # Patikriname, ar šablonas egzistuoja
            template_path = os.path.join(self.TEMPLATES_DIR, f"{template_id}.json")
            
            if not os.path.exists(template_path):
                return False
                
            # Nuskaitome esamą šabloną
            with open(template_path, 'r', encoding='utf-8') as f:
                template_data = json.load(f)
            
            # Padidiname naudojimo skaitliuką
            usage_count = template_data.get('usage_count', 0) + 1
            template_data['usage_count'] = usage_count
            
            # Išsaugome atnaujintą šabloną
            with open(template_path, 'w', encoding='utf-8') as f:
                json.dump(template_data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            self.logger.error(f"Klaida atnaujinant šablono {template_id} naudojimo skaitliuką: {str(e)}")
            return False
    
    def delete_template(self, template_id):
        """
        Ištrina šabloną
        
        Args:
            template_id (str): Šablono identifikatorius
            
        Returns:
            bool: True, jei sėkmingai ištrinta, kitaip False
        """
        try:
            # Patikriname, ar šablonas egzistuoja
            template_path = os.path.join(self.TEMPLATES_DIR, f"{template_id}.json")
            
            if not os.path.exists(template_path):
                return False
                
            # Ištriname šabloną
            os.remove(template_path)
            
            return True
        except Exception as e:
            self.logger.error(f"Klaida trinant šabloną {template_id}: {str(e)}")
            return False