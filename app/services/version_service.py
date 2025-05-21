import os
import json
import logging
from datetime import datetime
import re

class VersionService:
    """
    Modelių versijų valdymo servisas
    """
    
    def __init__(self):
        """
        Inicializuojame VersionService
        """
        # Nustatome kelią iki versijų direktorijos
        self.versions_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'versions')
        os.makedirs(self.versions_dir, exist_ok=True)
        
        # Versijų sąryšių failo kelias
        self.versions_file = os.path.join(self.versions_dir, 'model_versions.json')
        
        # Sukuriame versijų failą, jei jis neegzistuoja
        if not os.path.exists(self.versions_file):
            self._save_versions({})
    
    def get_model_versions(self, base_model_id=None):
        """
        Gauna visas modelių versijas arba konkretaus modelio versijas
        
        Args:
            base_model_id (str, optional): Bazinio modelio ID
            
        Returns:
            dict: Modelių versijų žodynas
        """
        try:
            versions = self._load_versions()
            
            if base_model_id:
                # Grąžiname tik nurodyto modelio versijas
                return versions.get(base_model_id, {})
            else:
                # Grąžiname visas versijas
                return versions
        except Exception as e:
            logging.error(f"Klaida gaunant modelių versijas: {str(e)}")
            return {}
    
    def create_model_version(self, base_model_id, parent_version_id, model_config):
        """
        Sukuriame naują modelio versiją
        
        Args:
            base_model_id (str): Bazinio modelio ID
            parent_version_id (str): Tėvinės versijos ID (gali būti None jei tai pirma versija)
            model_config (dict): Naujos versijos modelio konfigūracija
            
        Returns:
            str: Naujos versijos ID arba None jei nepavyko sukurti
        """
        try:
            versions = self._load_versions()
            
            # Jei bazinis modelis neegzistuoja, sukuriame naują įrašą
            if base_model_id not in versions:
                versions[base_model_id] = {}
            
            # Sugeneruojame naujos versijos ID
            version_id = model_config.get('training_id')
            
            # Gauname versijos numerį
            version_number = self._get_next_version_number(versions[base_model_id])
            
            # Bazinį modelio pavadinimą išgauname iš parent versijos arba iš naujojo modelio
            if parent_version_id and parent_version_id in versions[base_model_id]:
                base_name = versions[base_model_id][parent_version_id].get('base_name', model_config.get('name', 'Modelis'))
            else:
                base_name = model_config.get('name', 'Modelis')
            
            # Sugeneruojame versijos pavadinimą
            version_name = self._generate_version_name(base_name, version_number)
            
            # Sukuriame versijos informaciją
            version_info = {
                'version_number': version_number,
                'base_name': base_name,
                'version_name': version_name,
                'parent_id': parent_version_id,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'changes': model_config.get('changes', []),
                'parameters': model_config.get('parameters', {})
            }
            
            # Išsaugome versiją
            versions[base_model_id][version_id] = version_info
            self._save_versions(versions)
            
            # Grąžiname naujos versijos ID
            return version_id
            
        except Exception as e:
            logging.error(f"Klaida kuriant modelio versiją: {str(e)}")
            return None
    
    def get_model_version_tree(self, base_model_id):
        """
        Gauna modelio versijų medį hierarchine forma
        
        Args:
            base_model_id (str): Bazinio modelio ID
            
        Returns:
            dict: Hierarchinis versijų medis
        """
        try:
            versions = self._load_versions()
            
            if base_model_id not in versions:
                return {}
            
            # Randame pagrindinę (root) versiją (be tėvinio ID)
            root_versions = [v_id for v_id, v_info in versions[base_model_id].items() if not v_info.get('parent_id')]
            
            # Jei nėra pagrindinės versijos, grąžiname tuščią medį
            if not root_versions:
                return {}
            
            # Statome medį nuo pagrindinės versijos
            return self._build_version_tree(versions[base_model_id], root_versions[0])
            
        except Exception as e:
            logging.error(f"Klaida gaunant modelio versijų medį: {str(e)}")
            return {}
    
    def generate_version_name_for_model(self, model_name, version_number=None):
        """
        Sugeneruoja versijos pavadinimą modeliui
        
        Args:
            model_name (str): Modelio pavadinimas
            version_number (int, optional): Versijos numeris
            
        Returns:
            str: Sugeneruotas versijos pavadinimas
        """
        if version_number is None:
            version_number = 1
        
        return self._generate_version_name(model_name, version_number)
    
    def _generate_version_name(self, base_name, version_number):
        """
        Sugeneruoja versijos pavadinimą modeliui
        
        Args:
            base_name (str): Bazinis modelio pavadinimas
            version_number (int): Versijos numeris
            
        Returns:
            str: Sugeneruotas versijos pavadinimas
        """
        # Patikriname, ar jau turi versijos pavadinimą
        if re.search(r'v\d+$', base_name):
            # Pašaliname versijos dalį
            base_name = re.sub(r'\s*v\d+$', '', base_name)
        
        # Grąžiname naują pavadinimą su versijos numeriu
        return f"{base_name} v{version_number}"
    
    def _get_next_version_number(self, versions_dict):
        """
        Gauna sekantį versijos numerį
        
        Args:
            versions_dict (dict): Modelio versijų žodynas
            
        Returns:
            int: Sekantis versijos numeris
        """
        # Jei nėra versijų, grąžiname 1
        if not versions_dict:
            return 1
        
        # Randame didžiausią versijos numerį
        max_version = max([v.get('version_number', 0) for v in versions_dict.values()])
        
        # Grąžiname sekantį numerį
        return max_version + 1
    
    def _build_version_tree(self, versions, root_id):
        """
        Rekursyviai sukuria hierarchinį versijų medį
        
        Args:
            versions (dict): Modelio versijų žodynas
            root_id (str): Pagrindinės (root) versijos ID
            
        Returns:
            dict: Hierarchinis versijų medis
        """
        if root_id not in versions:
            return {}
        
        # Formuojame pagrindinės versijos informaciją
        node = {
            'id': root_id,
            'version_number': versions[root_id].get('version_number', 1),
            'version_name': versions[root_id].get('version_name', 'Nežinoma versija'),
            'created_at': versions[root_id].get('created_at', 'Nežinoma data'),
            'children': []
        }
        
        # Randame vaikus (versijas, kurių tėvinis ID yra root_id)
        children = [v_id for v_id, v_info in versions.items() if v_info.get('parent_id') == root_id]
        
        # Rekursyviai statome vaikų medžius
        for child_id in children:
            node['children'].append(self._build_version_tree(versions, child_id))
        
        return node
    
    def _load_versions(self):
        """
        Užkrauna modelių versijas iš failo
        
        Returns:
            dict: Modelių versijų žodynas
        """
        try:
            if os.path.exists(self.versions_file):
                with open(self.versions_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logging.error(f"Klaida užkraunant versijas: {str(e)}")
            return {}
    
    def _save_versions(self, versions):
        """
        Išsaugo modelių versijas į failą
        
        Args:
            versions (dict): Modelių versijų žodynas
            
        Returns:
            bool: True jei sėkmingai išsaugota, False jei klaida
        """
        try:
            with open(self.versions_file, 'w', encoding='utf-8') as f:
                json.dump(versions, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            logging.error(f"Klaida išsaugant versijas: {str(e)}")
            return False