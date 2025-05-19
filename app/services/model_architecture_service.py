import os
import base64
import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.utils import plot_model
import io
import numpy as np

class ModelArchitectureService:
    def __init__(self):
        """
        Inicijuojame servisą modelių architektūrai vizualizuoti
        """
        # Nustatome modelių saugojimo aplanką
        self.models_dir = os.path.join('app', 'data', 'models')
        
        # Sukuriame aplanką, jeigu jis neegzistuoja
        if not os.path.exists(self.models_dir):
            os.makedirs(self.models_dir)
    
    def get_available_models(self):
        """
        Grąžina visų išsaugotų modelių sąrašą
        
        Returns:
            list: Modelių failų pavadinimų sąrašas
        """
        # Ieškome .h5 failų modelių aplanke
        models = []
        if os.path.exists(self.models_dir):
            for file in os.listdir(self.models_dir):
                if file.endswith('.h5'):
                    models.append(file)
        return models
    
    def load_model_architecture(self, model_name):
        """
        Įkelia modelį ir grąžina jo architektūros informaciją
        
        Args:
            model_name (str): Modelio failo pavadinimas
            
        Returns:
            dict: Modelio architektūros informacija arba klaida
        """
        try:
            # Nustatome pilną kelią iki modelio
            model_path = os.path.join(self.models_dir, model_name)
            
            # Tikriname, ar modelio failas egzistuoja
            if not os.path.exists(model_path):
                return {'error': f'Modelis {model_name} nerastas'}
            
            # Įkrauname modelį
            model = load_model(model_path)
            
            # Gauname informaciją apie sluoksnius
            layers_info = []
            total_params = 0
            
            # Einame per visus sluoksnius
            for layer in model.layers:
                # Skaičiuojame parametrų skaičių sluoksnyje
                params = layer.count_params()
                total_params += params
                
                # Sukuriame sluoksnio informaciją
                layer_info = {
                    'name': layer.name,
                    'type': layer.__class__.__name__,
                    'params': params,
                    'output_shape': str(layer.output_shape),
                    'trainable': layer.trainable
                }
                
                # Tikriname ar sluoksnis turi aktivacijos funkciją
                if hasattr(layer, 'activation'):
                    layer_info['activation'] = layer.activation.__name__
                
                layers_info.append(layer_info)
            
            # Sukuriame modelio santrauką
            model_summary = {
                'name': model_name,
                'layers_count': len(model.layers),
                'total_params': total_params,
                'layers': layers_info
            }
            
            return model_summary
        
        except Exception as e:
            # Klaidos atveju grąžiname informaciją apie klaidą
            return {'error': str(e)}
    
    def generate_model_visualization(self, model_name):
        """
        Sugeneruoja modelio vizualizaciją kaip PNG paveikslėlį
        
        Args:
            model_name (str): Modelio failo pavadinimas
            
        Returns:
            str arba dict: Base64 koduotas paveikslėlis arba klaida
        """
        try:
            # Nustatome pilną kelią iki modelio
            model_path = os.path.join(self.models_dir, model_name)
            
            # Tikriname, ar modelio failas egzistuoja
            if not os.path.exists(model_path):
                return {'error': f'Modelis {model_name} nerastas'}
            
            # Įkrauname modelį
            model = load_model(model_path)
            
            # Sukuriame laikiną failą modelio vizualizacijai
            temp_img_path = os.path.join(self.models_dir, 'temp_visualization.png')
            
            # Generuojame modelio vizualizaciją
            plot_model(model, to_file=temp_img_path, show_shapes=True, 
                       show_layer_names=True, expand_nested=True)
            
            # Nuskaitome paveikslėlį ir konvertuojame į base64
            with open(temp_img_path, "rb") as img_file:
                img_data = base64.b64encode(img_file.read()).decode('utf-8')
            
            # Pašaliname laikiną failą
            if os.path.exists(temp_img_path):
                os.remove(temp_img_path)
            
            return img_data
        
        except Exception as e:
            # Klaidos atveju grąžiname informaciją apie klaidą
            return {'error': str(e)}
    
    def export_as_image(self, model_name, format='png'):
        """
        Eksportuoja modelio vizualizaciją kaip paveikslėlį
        
        Args:
            model_name (str): Modelio failo pavadinimas
            format (str): Eksporto formatas (png arba svg)
            
        Returns:
            tuple: (filename, binary_data) Failo pavadinimas ir duomenys arba klaida
        """
        try:
            # Nustatome pilną kelią iki modelio
            model_path = os.path.join(self.models_dir, model_name)
            
            # Tikriname, ar modelio failas egzistuoja
            if not os.path.exists(model_path):
                return (None, {'error': f'Modelis {model_name} nerastas'})
            
            # Įkrauname modelį
            model = load_model(model_path)
            
            # Sukuriame pavadinimą eksportuojamam failui
            export_filename = f"{os.path.splitext(model_name)[0]}_architecture.{format}"
            temp_path = os.path.join(self.models_dir, export_filename)
            
            # Generuojame modelio vizualizaciją
            plot_model(model, to_file=temp_path, show_shapes=True, 
                       show_layer_names=True, expand_nested=True)
            
            # Nuskaitome paveikslėlį
            with open(temp_path, "rb") as f:
                binary_data = f.read()
            
            # Pašaliname laikiną failą
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
            return (export_filename, binary_data)
        
        except Exception as e:
            # Klaidos atveju grąžiname informaciją apie klaidą
            return (None, {'error': str(e)})
    
    def export_model_summary(self, model_name, format='json'):
        """
        Eksportuoja modelio santraukos duomenis į failą
        
        Args:
            model_name (str): Modelio failo pavadinimas
            format (str): Eksporto formatas (json arba csv)
            
        Returns:
            tuple: (filename, binary_data) Failo pavadinimas ir duomenys arba klaida
        """
        try:
            # Gauname modelio informaciją
            model_info = self.load_model_architecture(model_name)
            
            if 'error' in model_info:
                return (None, model_info)
            
            # Sukuriame eksportuojamo failo pavadinimą
            export_filename = f"{os.path.splitext(model_name)[0]}_summary.{format}"
            
            # Ruošiame duomenis pagal formatą
            if format == 'json':
                import json
                # Konvertuojame į JSON
                binary_data = json.dumps(model_info, indent=4).encode('utf-8')
                mime_type = 'application/json'
            elif format == 'csv':
                import csv
                import io
                
                # Sukuriame CSV failo turinį atmintyje
                output = io.StringIO()
                writer = csv.writer(output)
                
                # Rašome antraštės eilutę
                writer.writerow(['name', 'type', 'params', 'output_shape', 'activation', 'trainable'])
                
                # Rašome sluoksnių duomenis
                for layer in model_info['layers']:
                    writer.writerow([
                        layer['name'],
                        layer['type'],
                        layer['params'],
                        layer['output_shape'],
                        layer.get('activation', ''),
                        layer['trainable']
                    ])
                
                # Gauname CSV duomenis
                binary_data = output.getvalue().encode('utf-8')
                mime_type = 'text/csv'
            else:
                return (None, {'error': f'Nepalaikomas formatas: {format}'})
            
            return (export_filename, binary_data, mime_type)
        
        except Exception as e:
            # Klaidos atveju grąžiname informaciją apie klaidą
            return (None, {'error': str(e)}, None)