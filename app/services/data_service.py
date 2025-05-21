"""
Duomenų servisas
---------------------------
Šis modulis yra atsakingas už duomenų gavimą, paruošimą ir transformavimą.
"""

import os
import json
import logging
import uuid
from datetime import datetime

class DataService:
    """
    Servisas, atsakingas už duomenų rinkinių valdymą
    """
    
    def __init__(self):
        """
        Inicializuoja DataService ir sukuria reikalingus aplankus
        """
        # Kelias iki duomenų direktorijos
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
        
        # Duomenų rinkinių aplankas
        self.datasets_dir = os.path.join(self.data_dir, 'datasets')
        os.makedirs(self.datasets_dir, exist_ok=True)
        
        # Duomenų rinkinių metaduomenų aplankas
        self.metadata_dir = os.path.join(self.datasets_dir, 'metadata')
        os.makedirs(self.metadata_dir, exist_ok=True)
    
    def get_all_datasets(self):
        """
        Gauna visų duomenų rinkinių sąrašą
        
        Returns:
            list: Duomenų rinkinių sąrašas
        """
        # Inicializuojame tuščią duomenų rinkinių sąrašą
        datasets = []
        
        try:
            # Tikriname, ar yra duomenų rinkinių
            if not os.path.exists(self.metadata_dir):
                # Jei nėra, sukuriame demonstracinius duomenų rinkinius
                self._create_demo_datasets()
            
            # Pereiname per visus metaduomenų failus
            for filename in os.listdir(self.metadata_dir):
                if filename.endswith('.json'):
                    # Pašaliname '.json' galūnę
                    dataset_id = filename[:-5]
                    
                    # Gauname duomenų rinkinio metaduomenis
                    dataset = self.get_dataset(dataset_id)
                    
                    if dataset:
                        datasets.append(dataset)
            
            # Rūšiuojame pagal sukūrimo datą (naujausi viršuje)
            datasets.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        except Exception as e:
            # Užfiksuojame klaidą žurnale
            logging.error(f"Klaida gaunant duomenų rinkinių sąrašą: {str(e)}")
        
        # Grąžiname duomenų rinkinių sąrašą
        return datasets
    
    def get_dataset(self, dataset_id):
        """
        Gauna duomenų rinkinio metaduomenis
        
        Args:
            dataset_id (str): Duomenų rinkinio ID
            
        Returns:
            dict: Duomenų rinkinio metaduomenys arba None, jei nerasta
        """
        try:
            # Kelias iki metaduomenų failo
            metadata_file = os.path.join(self.metadata_dir, f"{dataset_id}.json")
            
            # Tikriname, ar failas egzistuoja
            if not os.path.exists(metadata_file):
                return None
            
            # Grąžiname metaduomenis
            with open(metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            # Užfiksuojame klaidą žurnale
            logging.error(f"Klaida gaunant duomenų rinkinį: {str(e)}")
            return None
    
    def _create_demo_datasets(self):
        """
        Sukuria demonstracinius duomenų rinkinius
        """
        try:
            # Sukuriame kelis demonstracinius duomenų rinkinius
            demo_datasets = [
                {
                    'id': str(uuid.uuid4()),
                    'name': 'Bitcoin 2022 kainų duomenys',
                    'description': 'Bitcoin kainų duomenys iš 2022 metų, 1 dienos intervalu',
                    'source': 'Yahoo Finance',
                    'format': 'CSV',
                    'rows': 365,
                    'columns': 7,
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'type': 'istoriniai',
                    'features': ['date', 'open', 'high', 'low', 'close', 'volume', 'adj_close']
                },
                {
                    'id': str(uuid.uuid4()),
                    'name': 'Ethereum 2022-2023 kainų duomenys',
                    'description': 'Ethereum kainų duomenys iš 2022-2023 metų, 1 dienos intervalu',
                    'source': 'CoinMarketCap',
                    'format': 'CSV',
                    'rows': 730,
                    'columns': 7,
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'type': 'istoriniai',
                    'features': ['date', 'open', 'high', 'low', 'close', 'volume', 'market_cap']
                },
                {
                    'id': str(uuid.uuid4()),
                    'name': 'Kriptovaliutų koreliacija 2023',
                    'description': 'Pagrindinių kriptovaliutų kainų koreliacija 2023 metais',
                    'source': 'CoinGecko',
                    'format': 'JSON',
                    'rows': 100,
                    'columns': 10,
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'type': 'analitinis',
                    'features': ['date', 'btc', 'eth', 'xrp', 'ltc', 'ada', 'dot', 'link', 'sol', 'doge']
                }
            ]
            
            # Išsaugome demonstracinius duomenų rinkinius
            for dataset in demo_datasets:
                # Gaukime duomenų rinkinio ID
                dataset_id = dataset['id']
                # Kelias iki metaduomenų failo
                metadata_file = os.path.join(self.metadata_dir, f"{dataset_id}.json")
                
                # Įrašome duomenis į failą
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(dataset, f, indent=4, ensure_ascii=False)
        except Exception as e:
            # Užfiksuojame klaidą žurnale
            logging.error(f"Klaida kuriant demonstracinius duomenų rinkinius: {str(e)}")