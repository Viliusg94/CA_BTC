import os
import csv
import pandas as pd
from datetime import datetime

class ModelMetrics:
    def __init__(self):
        """
        Inicializuojame klasę modelių metrikų saugojimui
        """
        # Nustatome CSV failo kelią
        self.metrics_file = 'app/data/model_metrics.csv'
        
        # Sukuriame aplanką, jeigu jis neegzistuoja
        os.makedirs('app/data', exist_ok=True)
        
        # Sukuriame failą su stulpelių antraštėmis, jeigu jis neegzistuoja
        if not os.path.exists(self.metrics_file):
            with open(self.metrics_file, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['model_id', 'model_name', 'date_created', 'accuracy', 
                                'loss', 'val_accuracy', 'val_loss', 'epochs', 'description'])
    
    def save_metrics(self, model_name, accuracy, loss, val_accuracy, val_loss, epochs, description=""):
        """
        Išsaugo modelio metrikas į CSV failą
        
        Args:
            model_name (str): Modelio pavadinimas
            accuracy (float): Tikslumas
            loss (float): Nuostoliai
            val_accuracy (float): Validavimo tikslumas
            val_loss (float): Validavimo nuostoliai
            epochs (int): Epochų skaičius
            description (str): Modelio aprašymas
            
        Returns:
            int: Sukurto modelio ID
        """
        # Sugeneruojame unikalų ID
        model_id = self._generate_id()
        
        # Gauname dabartinę datą
        date_created = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Išsaugome eilutę CSV faile
        with open(self.metrics_file, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([model_id, model_name, date_created, accuracy, loss, 
                            val_accuracy, val_loss, epochs, description])
        
        return model_id
    
    def get_all_models(self):
        """
        Grąžina visus modelius iš CSV failo
        
        Returns:
            list: Modelių sąrašas
        """
        try:
            # Nuskaitome CSV failą į pandas DataFrame
            df = pd.read_csv(self.metrics_file)
            
            # Konvertuojame DataFrame į žodyną
            return df.to_dict('records')
        except:
            # Klaidos atveju grąžiname tuščią sąrašą
            return []
    
    def get_model(self, model_id):
        """
        Grąžina konkretų modelį pagal ID
        
        Args:
            model_id (int): Modelio ID
            
        Returns:
            dict: Modelio duomenys arba None, jei modelis nerastas
        """
        try:
            # Nuskaitome CSV failą į pandas DataFrame
            df = pd.read_csv(self.metrics_file)
            
            # Filtruojame pagal modelio ID
            model = df[df['model_id'] == model_id]
            
            # Jei modelis rastas, grąžiname jo duomenis
            if not model.empty:
                return model.to_dict('records')[0]
            
            # Jei modelis nerastas, grąžiname None
            return None
        except:
            # Klaidos atveju grąžiname None
            return None
    
    def delete_model(self, model_id):
        """
        Ištrina modelį pagal ID
        
        Args:
            model_id (int): Modelio ID
            
        Returns:
            bool: True, jei ištrinta sėkmingai, False - priešingu atveju
        """
        try:
            # Nuskaitome CSV failą į pandas DataFrame
            df = pd.read_csv(self.metrics_file)
            
            # Filtruojame, kad pašalintume modelį
            df = df[df['model_id'] != model_id]
            
            # Rašome atnaujintą DataFrame atgal į CSV
            df.to_csv(self.metrics_file, index=False)
            
            return True
        except:
            # Klaidos atveju grąžiname False
            return False
            
    def _generate_id(self):
        """
        Sugeneruoja unikalų ID naujam modeliui
        
        Returns:
            int: Naujas unikalus ID
        """
        try:
            # Nuskaitome CSV failą į pandas DataFrame
            df = pd.read_csv(self.metrics_file)
            
            # Jei nėra įrašų, pradedame nuo 1
            if df.empty:
                return 1
            
            # Kitu atveju - didžiausias ID + 1
            return int(df['model_id'].max()) + 1
        except:
            # Klaidos atveju arba jei failas tuščias, pradedame nuo 1
            return 1