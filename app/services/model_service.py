import os
import json
import logging
import uuid
import re
import copy
import datetime
import csv
from io import StringIO

class ModelService:
    """
    Servisas, atsakingas už modelio konfigūracijos, treniravimo rezultatų ir versijų valdymą.
    """
    
    def __init__(self):
        """
        Inicializuoja ModelService ir sukuria reikalingus aplankus.
        """
        # Nustatome kelią iki duomenų direktorijos
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
        
        # Sukuriame aplanką modelių konfigūracijoms
        self.configs_dir = os.path.join(self.data_dir, 'configs')
        os.makedirs(self.configs_dir, exist_ok=True)
        
        # Sukuriame aplanką modelių rezultatams
        self.results_dir = os.path.join(self.data_dir, 'results')
        os.makedirs(self.results_dir, exist_ok=True)
        
        # Sukuriame aplanką šablonams
        self.templates_dir = os.path.join(self.data_dir, 'templates')
        os.makedirs(self.templates_dir, exist_ok=True)
        
        # Šablonų failo kelias
        self.templates_file = os.path.join(self.templates_dir, 'model_templates.json')
        
        # Sukuriame šablonų failą, jei jis neegzistuoja
        if not os.path.exists(self.templates_file):
            with open(self.templates_file, 'w', encoding='utf-8') as f:
                json.dump({}, f)

    # ===== Modelio konfigūracijos valdymas =====
    
    def get_model_config(self, training_id):
        """
        Gauna modelio konfigūraciją pagal ID
        
        Args:
            training_id (str): Treniravimo sesijos ID
            
        Returns:
            dict: Modelio konfigūracija arba None, jei nerasta
        """
        return self.load_model_config(training_id)
    
    def load_model_config(self, training_id):
        """
        Užkrauna modelio konfigūraciją iš failo
        
        Args:
            training_id (str): Treniravimo sesijos ID
            
        Returns:
            dict: Modelio konfigūracija arba None, jei nerasta
        """
        config_path = os.path.join(self.configs_dir, f"{training_id}.json")
        
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return None
        except Exception as e:
            logging.error(f"Klaida užkraunant modelio konfigūraciją: {str(e)}")
            return None
    
    def save_model_config(self, training_id, config):
        """
        Išsaugo modelio konfigūraciją į failą
        
        Args:
            training_id (str): Treniravimo sesijos ID
            config (dict): Modelio konfigūracija
            
        Returns:
            bool: True jei sėkmingai išsaugota, False jei klaida
        """
        config_path = os.path.join(self.configs_dir, f"{training_id}.json")
        
        try:
            # Pridedame training_id į konfigūraciją
            config['training_id'] = training_id
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            logging.error(f"Klaida išsaugant modelio konfigūraciją: {str(e)}")
            return False
    
    def delete_model(self, training_id):
        """
        Ištrina modelį ir visus susijusius failus
        
        Args:
            training_id (str): Treniravimo sesijos ID
            
        Returns:
            bool: True jei sėkmingai ištrinta, False jei klaida
        """
        try:
            # Triname konfigūracijos failą
            config_path = os.path.join(self.configs_dir, f"{training_id}.json")
            if os.path.exists(config_path):
                os.remove(config_path)
            
            # Triname rezultatų failą
            results_path = os.path.join(self.results_dir, f"{training_id}.json")
            if os.path.exists(results_path):
                os.remove(results_path)
            
            # Triname modelio failą, jei jis egzistuoja
            model_path = self.get_model_file_path(training_id)
            if model_path and os.path.exists(model_path):
                os.remove(model_path)
            
            return True
        except Exception as e:
            logging.error(f"Klaida trinant modelį: {str(e)}")
            return False
    
    def get_model_file_path(self, training_id):
        """
        Gauna modelio failo kelią
        
        Args:
            training_id (str): Treniravimo sesijos ID
            
        Returns:
            str: Modelio failo kelias arba None, jei nėra
        """
        # Patikrinti ar yra SavedModel formato modelis
        saved_model_dir = os.path.join(self.data_dir, 'models', training_id)
        if os.path.exists(saved_model_dir):
            return saved_model_dir
        
        # Patikrinti ar yra H5 formato modelis
        h5_path = os.path.join(self.data_dir, 'models', f"{training_id}.h5")
        if os.path.exists(h5_path):
            return h5_path
        
        return None
    
    # ===== Modelio treniravimo valdymas =====
    
    def start_training(self, training_id, user_id=None):
        """
        Pradeda modelio treniravimą
        
        Args:
            training_id (str): Treniravimo sesijos ID
            user_id (int, optional): Vartotojo ID
            
        Returns:
            bool: True jei treniravimas pradėtas, False jei klaida
        """
        try:
            # Čia būtų realaus treniravimo logika
            # Šiame šablone tik pakeičiame būseną į "training"
            
            status_path = os.path.join(self.data_dir, 'status', f"{training_id}.json")
            os.makedirs(os.path.dirname(status_path), exist_ok=True)
            
            status = {
                'status': 'training',
                'started_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'user_id': user_id,
                'progress': 0
            }
            
            with open(status_path, 'w', encoding='utf-8') as f:
                json.dump(status, f, indent=4, ensure_ascii=False)
            
            return True
        except Exception as e:
            logging.error(f"Klaida pradedant treniravimą: {str(e)}")
            return False
    
    def stop_training(self, training_id, user_id=None):
        """
        Sustabdo modelio treniravimą
        
        Args:
            training_id (str): Treniravimo sesijos ID
            user_id (int, optional): Vartotojo ID
            
        Returns:
            bool: True jei treniravimas sustabdytas, False jei klaida
        """
        try:
            # Čia būtų realaus treniravimo sustabdymo logika
            # Šiame šablone tik pakeičiame būseną į "stopped"
            
            status_path = os.path.join(self.data_dir, 'status', f"{training_id}.json")
            
            if os.path.exists(status_path):
                with open(status_path, 'r', encoding='utf-8') as f:
                    status = json.load(f)
                
                status['status'] = 'stopped'
                status['stopped_at'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                status['stopped_by'] = user_id
                
                with open(status_path, 'w', encoding='utf-8') as f:
                    json.dump(status, f, indent=4, ensure_ascii=False)
            else:
                return False
            
            return True
        except Exception as e:
            logging.error(f"Klaida sustabdant treniravimą: {str(e)}")
            return False
    
    def get_training_status(self, training_id):
        """
        Gauna modelio treniravimo būseną
        
        Args:
            training_id (str): Treniravimo sesijos ID
            
        Returns:
            dict: Treniravimo būsena arba None, jei nerasta
        """
        status_path = os.path.join(self.data_dir, 'status', f"{training_id}.json")
        
        try:
            if os.path.exists(status_path):
                with open(status_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return None
        except Exception as e:
            logging.error(f"Klaida gaunant treniravimo būseną: {str(e)}")
            return None
    
    # ===== Modelio rezultatų valdymas =====
    
    def save_model_results(self, training_id, metrics):
        """
        Išsaugo modelio treniravimo rezultatus
        
        Args:
            training_id (str): Treniravimo sesijos ID
            metrics (dict): Modelio metrikos
            
        Returns:
            bool: True jei sėkmingai išsaugota, False jei klaida
        """
        results_path = os.path.join(self.results_dir, f"{training_id}.json")
        
        try:
            with open(results_path, 'w', encoding='utf-8') as f:
                json.dump(metrics, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            logging.error(f"Klaida išsaugant modelio rezultatus: {str(e)}")
            return False
    
    def get_model_metrics(self, training_id):
        """
        Gauna modelio treniravimo metrikas
        
        Args:
            training_id (str): Treniravimo sesijos ID
            
        Returns:
            list: Metrikų sąrašas arba None, jei nerasta
        """
        results_path = os.path.join(self.results_dir, f"{training_id}.json")
        
        try:
            if os.path.exists(results_path):
                with open(results_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return None
        except Exception as e:
            logging.error(f"Klaida gaunant modelio metrikas: {str(e)}")
            return None
    
    def get_epoch_metrics(self, training_id, epoch):
        """
        Gauna konkrečios epochos metrikas
        
        Args:
            training_id (str): Treniravimo sesijos ID
            epoch (int): Epochos numeris
            
        Returns:
            dict: Epochos metrikos arba None, jei nerasta
        """
        metrics = self.get_model_metrics(training_id)
        
        if not metrics:
            return None
        
        # Ieškome nurodytos epochos metrikų
        for epoch_metrics in metrics:
            if epoch_metrics.get('epoch') == epoch:
                return epoch_metrics
        
        return None
    
    def export_metrics_to_csv(self, training_id, include_changes=True):
        """
        Eksportuoja metrikas į CSV formatą
        
        Args:
            training_id (str): Treniravimo sesijos ID
            include_changes (bool, optional): Ar įtraukti pokyčius. Numatyta True.
            
        Returns:
            str: CSV turinys arba None, jei klaida
        """
        try:
            # Gauname modelio konfigūraciją ir metrikas
            model_config = self.get_model_config(training_id)
            metrics = self.get_model_metrics(training_id)
            
            if not model_config or not metrics:
                return None
            
            # Sukuriame CSV failo turinį
            output = StringIO()
            csv_writer = csv.writer(output)
            
            # Pridedame modelio informaciją
            csv_writer.writerow(['Modelio informacija'])
            csv_writer.writerow(['Pavadinimas', model_config.get('name', 'Nenurodyta')])
            csv_writer.writerow(['Tipas', model_config.get('type', 'Nenurodyta').upper()])
            csv_writer.writerow(['ID', training_id])
            csv_writer.writerow(['Sukurtas', model_config.get('created_at', 'Nenurodyta')])
            csv_writer.writerow([])
            
            # Pridedame modelio parametrus
            csv_writer.writerow(['Modelio parametrai'])
            if 'parameters' in model_config:
                for param, value in model_config['parameters'].items():
                    if param != 'specific':
                        csv_writer.writerow([param, value])
                
                if 'specific' in model_config['parameters']:
                    for param, value in model_config['parameters']['specific'].items():
                        csv_writer.writerow([param, value])
            
            csv_writer.writerow([])
            
            # Pridedame metrikų antraštes
            csv_writer.writerow(['Epocha', 'Loss', 'Accuracy', 'Val Loss', 'Val Accuracy'])
            
            # Pridedame metrikas
            for metric in metrics:
                if isinstance(metric, dict) and 'epoch' in metric:
                    csv_writer.writerow([
                        metric.get('epoch', ''),
                        metric.get('loss', ''),
                        metric.get('accuracy', ''),
                        metric.get('val_loss', ''),
                        metric.get('val_accuracy', '')
                    ])
            
            # Grąžiname CSV turinį
            return output.getvalue()
            
        except Exception as e:
            logging.error(f"Klaida eksportuojant metrikas į CSV: {str(e)}")
            return None
    
    # ===== Modelių istorijos valdymas =====
    
    def get_all_training_history(self):
        """
        Gauna visų treniruotų modelių istoriją
        
        Returns:
            list: Modelių sąrašas
        """
        models = []
        
        try:
            # Pereiname per visus konfigūracijos failus
            for filename in os.listdir(self.configs_dir):
                if filename.endswith('.json'):
                    training_id = filename[:-5]  # Pašaliname '.json' galūnę
                    
                    # Gauname modelio konfigūraciją
                    model_config = self.get_model_config(training_id)
                    
                    if model_config:
                        # Tikriname, ar yra treniravimo rezultatai
                        has_results = os.path.exists(os.path.join(self.results_dir, f"{training_id}.json"))
                        
                        # Pridedame modelį į sąrašą
                        models.append({
                            'training_id': training_id,
                            'name': model_config.get('name', 'Nenurodyta'),
                            'type': model_config.get('type', 'Nenurodyta'),
                            'created_at': model_config.get('created_at', 'Nenurodyta'),
                            'has_results': has_results
                        })
            
            # Rūšiuojame pagal sukūrimo datą (naujausi viršuje)
            models.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            
            return models
        except Exception as e:
            logging.error(f"Klaida gaunant modelių istoriją: {str(e)}")
            return []
    
    # ===== Modelių šablonų valdymas =====
    
    def save_model_template(self, template_name, template_data):
        """
        Išsaugo modelio parametrų šabloną
        
        Args:
            template_name (str): Šablono pavadinimas
            template_data (dict): Šablono duomenys
            
        Returns:
            bool: True jei sėkmingai išsaugota, False jei klaida
        """
        try:
            # Užkrauname esamus šablonus
            templates = self._load_templates()
            
            # Pridedame arba atnaujiname šabloną
            templates[template_name] = template_data
            
            # Išsaugome šablonus
            with open(self.templates_file, 'w', encoding='utf-8') as f:
                json.dump(templates, f, indent=4, ensure_ascii=False)
            
            return True
        except Exception as e:
            logging.error(f"Klaida išsaugant modelio šabloną: {str(e)}")
            return False
    
    def get_model_templates(self):
        """
        Gauna visus modelio parametrų šablonus
        
        Returns:
            dict: Šablonų žodynas
        """
        return self._load_templates()
    
    def delete_model_template(self, template_name):
        """
        Ištrina modelio parametrų šabloną
        
        Args:
            template_name (str): Šablono pavadinimas
            
        Returns:
            bool: True jei sėkmingai ištrinta, False jei klaida
        """
        try:
            # Užkrauname esamus šablonus
            templates = self._load_templates()
            
            # Patikriname, ar šablonas egzistuoja
            if template_name not in templates:
                return False
            
            # Pašaliname šabloną
            del templates[template_name]
            
            # Išsaugome šablonus
            with open(self.templates_file, 'w', encoding='utf-8') as f:
                json.dump(templates, f, indent=4, ensure_ascii=False)
            
            return True
        except Exception as e:
            logging.error(f"Klaida trinant modelio šabloną: {str(e)}")
            return False
    
    def _load_templates(self):
        """
        Užkrauna visus modelio parametrų šablonus
        
        Returns:
            dict: Šablonų žodynas
        """
        try:
            if os.path.exists(self.templates_file):
                with open(self.templates_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logging.error(f"Klaida užkraunant modelio šablonus: {str(e)}")
            return {}
    
    # ===== Modelių versijų valdymas =====
    
    def create_model_version(self, parent_id, version_data):
        """
        Sukuria naują modelio versiją su nurodytais parametrais
        
        Args:
            parent_id (str): Tėvinio modelio ID
            version_data (dict): Naujos versijos duomenys (pvz., name, parameters)
            
        Returns:
            str: Naujos versijos ID arba None, jei nepavyko sukurti
        """
        try:
            # Gauname tėvinio modelio konfigūraciją
            parent_config = self.load_model_config(parent_id)
            if not parent_config:
                logging.error(f"Tėvinis modelis {parent_id} nerastas")
                return None
            
            # Sukuriame naujos versijos ID
            new_version_id = str(uuid.uuid4())
            
            # Paruošiame naujos versijos konfigūraciją
            new_config = copy.deepcopy(parent_config)
            
            # Jei naujas pavadinimas nepateiktas, sugeneruojame
            if not version_data.get('name'):
                # Sugeneruojame pavadinimą pagal tėvinį modelį ir versiją
                # Pirma tikriname, ar tėvinis modelis jau turi versijos numerį
                parent_name = parent_config.get('name', f"Modelis {parent_id[:8]}")
                version_match = re.search(r'v(\d+)$', parent_name)
                
                if version_match:
                    # Jei turi versiją, padidiname ją vienetu
                    current_version = int(version_match.group(1))
                    new_version = current_version + 1
                    base_name = parent_name[:version_match.start()]
                    new_name = f"{base_name}v{new_version}"
                else:
                    # Jei neturi versijos, pridedame v2 (nes tėvinis yra v1)
                    new_name = f"{parent_name} v2"
                
                version_data['name'] = new_name
            
            # Atnaujiname konfigūraciją pagal versijos duomenis
            new_config['name'] = version_data.get('name')
            if 'description' in version_data:
                new_config['description'] = version_data.get('description')
            
            # Atnaujiname parametrus, jei jie pateikti
            if 'parameters' in version_data and version_data['parameters']:
                # Išsaugome originalius parametrus
                original_params = new_config.get('parameters', {})
                
                # Atnaujiname parametrus, išsaugodami nemodifikuotus
                for key, value in version_data['parameters'].items():
                    if key in original_params:
                        original_params[key] = value
            
            # Pridedame versijos informaciją
            if 'versions' not in new_config:
                new_config['versions'] = []
            
            # Pridedame tėvinį modelį kaip priklausomybę
            new_config['parent_id'] = parent_id
            
            # Pridedame sukūrimo datą
            new_config['created_at'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Išsaugome naują versiją
            success = self.save_model_config(new_version_id, new_config)
            
            if not success:
                logging.error(f"Nepavyko išsaugoti naujos versijos konfigūracijos")
                return None
            
            # Pridedame naują versiją į tėvinio modelio versijų sąrašą
            parent_versions = parent_config.get('versions', [])
            parent_versions.append({
                'id': new_version_id,
                'name': new_config['name'],
                'created_at': new_config['created_at']
            })
            parent_config['versions'] = parent_versions;
            
            # Atnaujiname tėvinio modelio konfigūraciją
            self.save_model_config(parent_id, parent_config)
            
            return new_version_id
            
        except Exception as e:
            logging.error(f"Klaida kuriant modelio versiją: {str(e)}")
            return None
    
    def get_model_versions(self, model_id):
        """
        Gauna visas modelio versijas
        
        Args:
            model_id (str): Modelio ID
            
        Returns:
            list: Versijų sąrašas
        """
        try:
            # Gauname modelio konfigūraciją
            model_config = self.load_model_config(model_id)
            if not model_config:
                return []
            
            # Gauname versijų sąrašą
            versions = model_config.get('versions', [])
            
            # Jei modelis turi tėvinį modelį, gauname ir jo informaciją
            parent_id = model_config.get('parent_id')
            
            if parent_id:
                # Gauname tėvinio modelio konfigūraciją
                parent_config = self.load_model_config(parent_id)
                
                if parent_config:
                    # Sukuriame "šeimos medį"
                    family_tree = []
                    
                    # Pirma įtraukiame tėvinį modelį
                    family_tree.append({
                        'id': parent_id,
                        'name': parent_config.get('name', f"Modelis {parent_id[:8]}"),
                        'created_at': parent_config.get('created_at'),
                        'is_parent': True
                    })
                    
                    # Tada įtraukiame "brolius ir seseris" (kitas versijas)
                    for version in parent_config.get('versions', []):
                        if version['id'] != model_id:  # Neįtraukiame dabartinio modelio
                            version['is_sibling'] = True
                            family_tree.append(version)
                    
                    return {
                        'current': {
                            'id': model_id,
                            'name': model_config.get('name', f"Modelis {model_id[:8]}"),
                            'created_at': model_config.get('created_at')
                        },
                        'family_tree': family_tree,
                        'children': versions
                    }
            
            # Jei modelis neturi tėvinio modelio, grąžiname tik jo versijas
            return {
                'current': {
                    'id': model_id,
                    'name': model_config.get('name', f"Modelis {model_id[:8]}"),
                    'created_at': model_config.get('created_at')
                },
                'family_tree': [],
                'children': versions
            }
            
        except Exception as e:
            logging.error(f"Klaida gaunant modelio versijas: {str(e)}")
            return {
                'current': {
                    'id': model_id,
                    'name': f"Modelis {model_id[:8]}",
                    'created_at': 'Nežinoma'
                },
                'family_tree': [],
                'children': []
            }
    
    def generate_model_name(self, model_type=None, purpose=None):
        """
        Sugeneruoja automatinį modelio pavadinimą
        
        Args:
            model_type (str, optional): Modelio tipas (pvz., LSTM, GRU)
            purpose (str, optional): Modelio paskirtis
            
        Returns:
            str: Sugeneruotas pavadinimas
        """
        # Modelių tipų aprašymų žodynas lietuvių kalba
        type_descriptions = {
            'lstm': 'LSTM',
            'gru': 'GRU',
            'cnn': 'CNN',
            'rnn': 'RNN'
        }
        
        # Paskirčių aprašymai
        purpose_descriptions = {
            'prediction': 'Prognozei',
            'analysis': 'Analizei',
            'classification': 'Klasifikavimui'
        }
        
        # Generuojame pagrindinę dalį
        parts = []
        
        # Pridedame modelio tipą
        if model_type and model_type.lower() in type_descriptions:
            parts.append(type_descriptions[model_type.lower()])
        else:
            parts.append("Modelis")
        
        # Pridedame paskirtį
        if purpose and purpose.lower() in purpose_descriptions:
            parts.append(purpose_descriptions[purpose.lower()])
        
        # Pridedame datą
        current_date = datetime.datetime.now().strftime('%Y-%m-%d')
        parts.append(current_date)
        
        # Sugeneruojame unikalų ID
        short_id = str(uuid.uuid4())[:6]
        parts.append(f"ID-{short_id}")
        
        # Sujungiame dalis
        return " - ".join(parts)
    
    def get_all_models(self):
        """
        Gauna visų treniruotų modelių sąrašą, kuriuos galima naudoti vertinimui
        
        Returns:
            list: Modelių sąrašas
        """
        # Inicializuojame tuščią modelių sąrašą
        models = []
        
        try:
            # Pereiname per visus konfigūracijos failus
            for filename in os.listdir(self.configs_dir):
                if filename.endswith('.json'):
                    # Pašaliname '.json' galūnę, kad gautume treniravimo ID
                    training_id = filename[:-5]
                    
                    # Gauname modelio konfigūraciją
                    model_config = self.get_model_config(training_id)
                    
                    if model_config:
                        # Tikriname, ar yra treniravimo rezultatai (tik baigti modeliai)
                        has_results = os.path.exists(os.path.join(self.results_dir, f"{training_id}.json"))
                        
                        # Įtraukiame tik modelius su rezultatais
                        if has_results:
                            # Patikriname, ar egzistuoja modelio failas
                            model_path = self.get_model_file_path(training_id)
                            has_model_file = model_path is not None and os.path.exists(model_path)
                            
                            # Pridedame modelį į sąrašą
                            models.append({
                                'training_id': training_id,
                                'name': model_config.get('name', 'Nenurodyta'),
                                'type': model_config.get('type', 'Nenurodyta').upper(),
                                'created_at': model_config.get('created_at', 'Nenurodyta'),
                                'has_model_file': has_model_file,
                                'accuracy': self._get_model_accuracy(training_id)
                            })
        
            # Rūšiuojame pagal sukūrimo datą (naujausi viršuje)
            models.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        except Exception as e:
            # Užfiksuojame klaidą žurnale
            logging.error(f"Klaida gaunant modelių sąrašą: {str(e)}")
        
        # Grąžiname modelių sąrašą (tuščią jei buvo klaida)
        return models

    def _get_model_accuracy(self, training_id):
        """
        Gauna modelio tikslumą iš treniravimo rezultatų
        
        Args:
            training_id (str): Treniravimo sesijos ID
            
        Returns:
            float: Modelio tikslumas (0-1) arba 0, jei nerasta
        """
        try:
            # Gauname modelio metrikas
            metrics = self.get_model_metrics(training_id)
            
            if not metrics:
                return 0
            
            # Jei metrikos yra žodyne su raktu 'accuracy', grąžiname paskutinę reikšmę
            if isinstance(metrics, dict) and 'accuracy' in metrics:
                if isinstance(metrics['accuracy'], list):
                    return metrics['accuracy'][-1]
                return metrics['accuracy']
            
            # Jei metrikos yra sąraše, grąžiname paskutinio elemento 'accuracy'
            if isinstance(metrics, list) and metrics:
                last_metric = metrics[-1]
                if isinstance(last_metric, dict) and 'accuracy' in last_metric:
                    return last_metric['accuracy']
                elif isinstance(last_metric, dict) and 'val_accuracy' in last_metric:
                    return last_metric['val_accuracy']
            
            # Jei nėra metrikų, grąžiname 0
            return 0
        except Exception as e:
            # Užfiksuojame klaidą žurnale
            logging.error(f"Klaida gaunant modelio tikslumą: {str(e)}")
            return 0
        
    # ===== Modelio vertinimas =====
    
    def evaluate_model_with_dataset(self, training_id, dataset_id):
        """
        Įvertina modelį su nurodytu duomenų rinkiniu
        
        Args:
            training_id (str): Modelio treniravimo ID
            dataset_id (str): Duomenų rinkinio ID
            
        Returns:
            dict: Vertinimo rezultatai arba None, jei įvyko klaida
        """
        try:
            # Tikriname, ar modelis egzistuoja
            model_config = self.get_model_config(training_id)
            if not model_config:
                logging.error(f"Modelis su ID {training_id} nerastas")
                return None
            
            # Čia būtų logika modelio vertinimui su duomenų rinkiniu
            # Simuliuojame vertinimo rezultatus (demonstracijai)
            import random
            import time
            from datetime import datetime
            
            # Apskaičiuojame atsitiktinius rezultatus demonstracijai
            accuracy = round(0.7 + random.random() * 0.25, 4)
            precision = round(0.65 + random.random() * 0.3, 4)
            recall = round(0.6 + random.random() * 0.35, 4)
            f1_score = round(2 * precision * recall / (precision + recall), 4)
            
            # Simuliuojame vertinimo procesą - trumpas laukimas
            time.sleep(1)
            
            # Grąžiname simuliuotus rezultatus
            return {
                'accuracy': accuracy,
                'precision': precision,
                'recall': recall,
                'f1_score': f1_score,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'dataset_id': dataset_id,
                'training_id': training_id
            }
        except Exception as e:
            # Užfiksuojame klaidą žurnale
            logging.error(f"Klaida vertinant modelį: {str(e)}")
            return None

    def save_evaluation_results(self, training_id, dataset_id, results):
        """
        Išsaugo modelio vertinimo rezultatus
        
        Args:
            training_id (str): Modelio treniravimo ID
            dataset_id (str): Duomenų rinkinio ID
            results (dict): Vertinimo rezultatai
            
        Returns:
            bool: True jei sėkmingai išsaugota, False jei klaida
        """
        try:
            # Sukuriame vertinimo rezultatų aplanką, jei jo nėra
            eval_dir = os.path.join(self.data_dir, 'evaluations')
            os.makedirs(eval_dir, exist_ok=True)
            
            # Kelias iki vertinimo rezultatų failo
            eval_file = os.path.join(eval_dir, f"{training_id}_{dataset_id}.json")
            
            # Išsaugome rezultatus
            with open(eval_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=4, ensure_ascii=False)
            
            # Sėkmingai išsaugota
            return True
        except Exception as e:
            # Užfiksuojame klaidą žurnale
            logging.error(f"Klaida išsaugant vertinimo rezultatus: {str(e)}")
            return False

    def get_evaluation_results(self, training_id, dataset_id):
        """
        Gauna modelio vertinimo rezultatus
        
        Args:
            training_id (str): Modelio treniravimo ID
            dataset_id (str): Duomenų rinkinio ID
            
        Returns:
            dict: Vertinimo rezultatai arba None, jei nerasta
        """
        try:
            # Kelias iki vertinimo rezultatų failo
            eval_dir = os.path.join(self.data_dir, 'evaluations')
            eval_file = os.path.join(eval_dir, f"{training_id}_{dataset_id}.json")
            
            # Tikriname, ar failas egzistuoja
            if not os.path.exists(eval_file):
                return None
            
            # Grąžiname rezultatus
            with open(eval_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            # Užfiksuojame klaidą žurnale
            logging.error(f"Klaida gaunant vertinimo rezultatus: {str(e)}")
            return None

    def get_evaluation_history(self, training_id):
        """
        Gauna visus modelio vertinimo rezultatus
        
        Args:
            training_id (str): Modelio treniravimo ID
            
        Returns:
            list: Vertinimo rezultatų sąrašas
        """
        try:
            # Kelias iki vertinimo rezultatų aplanko
            eval_dir = os.path.join(self.data_dir, 'evaluations')
            
            # Tikriname, ar aplankas egzistuoja
            if not os.path.exists(eval_dir):
                return []
            
            # Gauname visus vertinimo rezultatų failus šiam modeliui
            eval_files = [f for f in os.listdir(eval_dir) if f.startswith(f"{training_id}_") and f.endswith(".json")]
            
            # Grąžiname rezultatų sąrašą
            evaluations = []
            for file in eval_files:
                with open(os.path.join(eval_dir, file), 'r', encoding='utf-8') as f:
                    results = json.load(f)
                    evaluations.append(results)
            
            # Rūšiuojame pagal datą (naujausi viršuje)
            evaluations.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            # Grąžiname vertinimų sąrašą
            return evaluations
        except Exception as e:
            # Užfiksuojame klaidą žurnale
            logging.error(f"Klaida gaunant vertinimo istoriją: {str(e)}")
            return []
