import os
import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt
import io
import base64
import json
import datetime
from tensorflow.keras.models import load_model

class ModelWeightsService:
    def __init__(self):
        """
        Inicializuojame servisą modelių svoriams analizuoti
        """
        # Nustatome modelių saugojimo aplanką
        self.models_dir = os.path.join('app', 'data', 'models')
        self.training_dir = os.path.join('app', 'data', 'training')
        
        # Sukuriame aplanką, jeigu jis neegzistuoja
        if not os.path.exists(self.models_dir):
            os.makedirs(self.models_dir)
        if not os.path.exists(self.training_dir):
            os.makedirs(self.training_dir)
    
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
    
    def load_model(self, model_name):
        """
        Įkelia modelį
        
        Args:
            model_name (str): Modelio failo pavadinimas
            
        Returns:
            keras.Model: Įkeltas modelis arba None jei klaida
        """
        try:
            # Nustatome pilną kelią iki modelio
            model_path = os.path.join(self.models_dir, model_name)
            
            # Tikriname, ar modelio failas egzistuoja
            if not os.path.exists(model_path):
                return None
            
            # Įkrauname modelį
            model = load_model(model_path)
            return model
        except Exception as e:
            print(f"Klaida įkeliant modelį: {str(e)}")
            return None
    
    def get_model_layers(self, model_name):
        """
        Grąžina modelio sluoksnių informaciją
        
        Args:
            model_name (str): Modelio failo pavadinimas
            
        Returns:
            list: Sluoksnių informacijos sąrašas arba klaidos žodynas
        """
        # Įkeliame modelį
        model = self.load_model(model_name)
        if model is None:
            return {'error': f'Modelis {model_name} nerastas arba negalima įkelti'}
        
        # Surenkame informaciją apie sluoksnius
        layers_info = []
        
        for i, layer in enumerate(model.layers):
            # Pagrindinė informacija apie sluoksnį
            layer_info = {
                'index': i,
                'name': layer.name,
                'type': layer.__class__.__name__,
                'has_weights': len(layer.weights) > 0,
                'weights_count': len(layer.weights),
                'trainable': layer.trainable
            }
            
            # Jei sluoksnis turi svorius, pridedame papildomą informaciją
            if layer_info['has_weights']:
                weights_info = []
                
                for j, weight in enumerate(layer.weights):
                    weight_info = {
                        'name': weight.name,
                        'shape': str(weight.shape),
                        'size': np.prod(weight.shape),
                        'index': j
                    }
                    weights_info.append(weight_info)
                
                layer_info['weights'] = weights_info
            
            layers_info.append(layer_info)
        
        return layers_info
    
    def generate_weights_histogram(self, model_name, layer_index, weight_index=0):
        """
        Generuoja svorių pasiskirstymo histogramą
        
        Args:
            model_name (str): Modelio failo pavadinimas
            layer_index (int): Sluoksnio indeksas
            weight_index (int): Svorio indeksas sluoksnyje
            
        Returns:
            str: Base64 koduotas histogramos paveikslėlis arba klaidos žodynas
        """
        try:
            # Įkeliame modelį
            model = self.load_model(model_name)
            if model is None:
                return {'error': f'Modelis {model_name} nerastas arba negalima įkelti'}
            
            # Tikriname ar sluoksnio indeksas teisingas
            if layer_index < 0 or layer_index >= len(model.layers):
                return {'error': f'Neteisingas sluoksnio indeksas: {layer_index}'}
            
            # Gauname sluoksnį
            layer = model.layers[layer_index]
            
            # Tikriname ar sluoksnis turi svorius
            if len(layer.weights) == 0:
                return {'error': f'Sluoksnis {layer.name} neturi svorių'}
            
            # Tikriname ar svorio indeksas teisingas
            if weight_index < 0 or weight_index >= len(layer.weights):
                return {'error': f'Neteisingas svorio indeksas: {weight_index}'}
            
            # Gauname svorių reikšmes
            weights = layer.weights[weight_index].numpy().flatten()
            
            # Sukuriame histogramą
            plt.figure(figsize=(8, 6))
            plt.hist(weights, bins=50, alpha=0.75, color='#3498db')
            plt.title(f'Sluoksnio "{layer.name}" svorių histograma')
            plt.xlabel('Svorio reikšmė')
            plt.ylabel('Dažnis')
            plt.grid(True, linestyle='--', alpha=0.7)
            
            # Pridedame statistikos informaciją
            plt.axvline(x=np.mean(weights), color='r', linestyle='--', 
                       label=f'Vidurkis: {np.mean(weights):.4f}')
            plt.axvline(x=np.median(weights), color='g', linestyle='-', 
                       label=f'Mediana: {np.median(weights):.4f}')
            plt.legend()
            
            # Konvertuojame grafiką į base64 koduotą paveikslėlį
            buf = io.BytesIO()
            plt.savefig(buf, format='png')
            plt.close()
            buf.seek(0)
            
            # Koduojame paveikslėlį base64 formatu
            img_str = base64.b64encode(buf.read()).decode('utf-8')
            
            return img_str
            
        except Exception as e:
            return {'error': f'Klaida generuojant histogramą: {str(e)}'}
    
    def generate_activations_heatmap(self, model_name, layer_index, sample_input=None):
        """
        Generuoja sluoksnio aktyvacijos šilumos žemėlapį
        
        Args:
            model_name (str): Modelio failo pavadinimas
            layer_index (int): Sluoksnio indeksas
            sample_input (array): Pavyzdinis įvesties masyvas
            
        Returns:
            str: Base64 koduotas šilumos žemėlapio paveikslėlis arba klaidos žodynas
        """
        try:
            # Įkeliame modelį
            model = self.load_model(model_name)
            if model is None:
                return {'error': f'Modelis {model_name} nerastas arba negalima įkelti'}
            
            # Tikriname ar sluoksnio indeksas teisingas
            if layer_index < 0 or layer_index >= len(model.layers):
                return {'error': f'Neteisingas sluoksnio indeksas: {layer_index}'}
            
            # Jei nėra pavyzdinės įvesties, naudojame atsitiktinį masyvą
            if sample_input is None:
                # Gauname įvesties formą
                input_shape = model.layers[0].input_shape
                
                # Jei tai yra sąrašas (kelios įvestys), imame pirmąją
                if isinstance(input_shape, list):
                    input_shape = input_shape[0]
                
                # Pašaliname None iš formos (batch dydis)
                input_shape = [dim if dim is not None else 1 for dim in input_shape]
                
                # Sukuriame atsitiktinę įvestį
                sample_input = np.random.random(input_shape)
                
                # Pridedame batch dimensiją, jei jos dar nėra
                if len(input_shape) == len(model.input.shape) - 1:
                    sample_input = np.expand_dims(sample_input, axis=0)
        
            # Sukuriame dalinį modelį iki nurodyto sluoksnio
            partial_model = tf.keras.models.Model(
                inputs=model.input,
                outputs=model.layers[layer_index].output
            )
            
            # Gauname aktyvacijas
            activations = partial_model.predict(sample_input)
            
            # Jei aktyvacijos yra daugiadimensinės, imame vidurkį per visas dimensijas
            if len(activations.shape) > 2:
                # Suvidurkiname visas dimensijas, išskyrus batch ir paskutinę (kanalai/cepoliai)
                axes_to_mean = tuple(range(1, len(activations.shape) - 1))
                activations = np.mean(activations, axis=axes_to_mean)
            
            # Imame pirmą batch elementą
            activations = activations[0]
            
            # Sukuriame šilumos žemėlapį
            plt.figure(figsize=(10, 6))
            plt.imshow(activations, aspect='auto', cmap='viridis')
            plt.colorbar(label='Aktyvacijos reikšmė')
            plt.title(f'Sluoksnio "{model.layers[layer_index].name}" aktyvacijos')
            plt.xlabel('Neurono indeksas')
            plt.ylabel('Aktyvacijos reikšmė')
            
            # Konvertuojame grafiką į base64 koduotą paveikslėlį
            buf = io.BytesIO()
            plt.savefig(buf, format='png')
            plt.close()
            buf.seek(0)
            
            # Koduojame paveikslėlį base64 formatu
            img_str = base64.b64encode(buf.read()).decode('utf-8')
            
            return img_str
            
        except Exception as e:
            return {'error': f'Klaida generuojant aktyvacijas: {str(e)}'}
    
    def analyze_weights(self, model_name, layer_index, weight_index=0):
        """
        Analizuoja sluoksnio svorius
        
        Args:
            model_name (str): Modelio failo pavadinimas
            layer_index (int): Sluoksnio indeksas
            weight_index (int): Svorio indeksas sluoksnyje
            
        Returns:
            dict: Svorių analizės rezultatai arba klaidos žodynas
        """
        try:
            # Įkeliame modelį
            model = self.load_model(model_name)
            if model is None:
                return {'error': f'Modelis {model_name} nerastas arba negalima įkelti'}
            
            # Tikriname ar sluoksnio indeksas teisingas
            if layer_index < 0 or layer_index >= len(model.layers):
                return {'error': f'Neteisingas sluoksnio indeksas: {layer_index}'}
            
            # Gauname sluoksnį
            layer = model.layers[layer_index]
            
            # Tikriname ar sluoksnis turi svorius
            if len(layer.weights) == 0:
                return {'error': f'Sluoksnis {layer.name} neturi svorių'}
            
            # Tikriname ar svorio indeksas teisingas
            if weight_index < 0 or weight_index >= len(layer.weights):
                return {'error': f'Neteisingas svorio indeksas: {weight_index}'}
            
            # Gauname svorių reikšmes
            weights = layer.weights[weight_index].numpy().flatten()
            
            # Analizuojame svorius
            analysis = {
                'mean': float(np.mean(weights)),
                'std': float(np.std(weights)),
                'min': float(np.min(weights)),
                'max': float(np.max(weights)),
                'median': float(np.median(weights)),
                'sparsity': float((weights == 0).sum() / len(weights)),
                'positive_ratio': float((weights > 0).sum() / len(weights)),
                'negative_ratio': float((weights < 0).sum() / len(weights)),
                'total_elements': int(len(weights)),
                'percentiles': {
                    '1': float(np.percentile(weights, 1)),
                    '10': float(np.percentile(weights, 10)),
                    '25': float(np.percentile(weights, 25)),
                    '50': float(np.percentile(weights, 50)),
                    '75': float(np.percentile(weights, 75)),
                    '90': float(np.percentile(weights, 90)),
                    '99': float(np.percentile(weights, 99))
                }
            }
            
            return analysis
            
        except Exception as e:
            return {'error': f'Klaida analizuojant svorius: {str(e)}'}
    
    def start_continued_training(self, training_id, training_params, model_obj):
        """
        Pradeda modelio tęstinį apmokymą nuo išsaugojimo
        
        Args:
            training_id (str): Apmokymo sesijos ID
            training_params (dict): Apmokymo parametrai
            model_obj: Modelio objektas, užkrautas iš išsaugojimo
        
        Returns:
            bool: Ar pavyko pradėti apmokymą
        """
        try:
            # Sukuriame apmokymo katalogą
            training_dir = os.path.join(self.training_dir, training_id)
            os.makedirs(training_dir, exist_ok=True)
            
            # Išsaugome apmokymo parametrus
            params_path = os.path.join(training_dir, "params.json")
            with open(params_path, 'w') as f:
                json.dump(training_params, f, indent=2)
            
            # Išsaugome pradinį modelį
            initial_model_path = os.path.join(training_dir, "initial_model.h5")
            model_obj.save(initial_model_path)
            
            # Sukuriame apmokymo būsenos failą
            status_path = os.path.join(training_dir, "status.json")
            status = {
                "status": "preparing",
                "start_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "completed_epochs": 0,
                "total_epochs": training_params.get("epochs", 0),
                "current_metrics": {},
                "continued_from_checkpoint": training_params.get("continued_from_checkpoint"),
                "continued_from_epoch": training_params.get("continued_from_epoch", 0)
            }
            
            with open(status_path, 'w') as f:
                json.dump(status, f, indent=2)
            
            # Pradedame apmokymą fone
            import threading
            
            # Funkcija, kuri bus vykdoma atskirame gije
            def train_model_thread():
                try:
                    # Atnaujiname būseną - treniruojama
                    self.update_training_status(training_id, "training")
                    
                    # Nustatome pradinius modelio parametrus
                    model = model_obj  # Jau turime užkrautą modelį iš išsaugojimo
                    
                    # Gauname duomenis apmokymui
                    # Duomenų gavimo logiką reikia pritaikyti pagal jūsų projekto struktūrą
                    from app.services.data_service import DataService
                    data_service = DataService()
                    X_train, y_train = data_service.get_training_data()
                    
                    # Sukuriame papildomus parametrus treniraviui
                    from app.services.model_service import train_model
                    
                    # Tęsiame treniravimą nuo išsaugojimo epochos
                    initial_epoch = training_params.get("continued_from_epoch", 0)
                    
                    # Apmokymo parametrai
                    train_params = {
                        'model': model,
                        'X_train': X_train,
                        'y_train': y_train,
                        'epochs': training_params.get("epochs", 10),
                        'batch_size': training_params.get("batch_size", 32),
                        'validation_split': 0.2,  # Validacijos dalis
                        'early_stopping': training_params.get("early_stopping", True),
                        'patience': training_params.get("patience", 10),
                        'model_id': training_params.get("model_id"),
                        'training_id': training_id,
                        'enable_checkpoints': True,  # Įgalinti išsaugojimus
                        'checkpoint_frequency': 5,  # Išsaugojimų dažnumas
                        'save_best_only': training_params.get("save_best_only", False),
                        'monitor_metric': training_params.get("monitor_metric", "val_loss"),
                        'initial_epoch': initial_epoch  # Pradžios epocha
                    }
                    
                    # Treniruojame modelį
                    training_results = train_model(**train_params)
                    
                    # Išsaugome galutinius rezultatus
                    results_path = os.path.join(training_dir, "results.json")
                    with open(results_path, 'w') as f:
                        # Konvertuojame numpy reikšmes į įprastus tipus
                        results = self._convert_numpy_values(training_results)
                        json.dump(results, f, indent=2)
                    
                    # Išsaugome galutinius modelio svorius
                    final_model_path = os.path.join(training_dir, "final_model.h5")
                    model.save(final_model_path)
                    
                    # Atnaujiname būseną - baigta
                    self.update_training_status(training_id, "completed")
                    
                    # Atnaujiname modelio informaciją
                    model_id = training_params.get("model_id")
                    model_meta_path = os.path.join('app', 'static', 'models', f"{model_id}_meta.json")
                    
                    if os.path.exists(model_meta_path):
                        with open(model_meta_path, 'r') as f:
                            model_info = json.load(f)
                        
                        # Pridedame informaciją apie tęstinį apmokymą
                        if 'training_history' not in model_info:
                            model_info['training_history'] = []
                        
                        model_info['training_history'].append({
                            'training_id': training_id,
                            'start_time': status.get('start_time'),
                            'end_time': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            'initial_epoch': initial_epoch,
                            'final_epoch': initial_epoch + training_results.get('epochs_completed', 0),
                            'continued_from_checkpoint': training_params.get("continued_from_checkpoint"),
                            'final_metrics': training_results.get('history', {})
                        })
                        
                        with open(model_meta_path, 'w') as f:
                            json.dump(model_info, f, indent=2)
                    
                except Exception as e:
                    # Registruojame klaidą ir atnaujiname būseną
                    logger.error(f"Klaida atliekant tęstinį apmokymą: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    
                    # Atnaujiname būseną - klaida
                    self.update_training_status(training_id, "error", str(e))
            
            # Pradedame apmokymo giją
            training_thread = threading.Thread(target=train_model_thread)
            training_thread.daemon = True
            training_thread.start()
            
            return True
        
        except Exception as e:
            # Registruojame klaidą
            logger.error(f"Klaida pradedant tęstinį apmokymą: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def _convert_numpy_values(self, obj):
        """
        Konvertuoja numpy reikšmes į įprastus tipus JSON serializacijai
        
        Args:
            obj: Objektas su galimai numpy reikšmėmis
        
        Returns:
            Konvertuotas objektas
        """
        import numpy as np
        
        if isinstance(obj, dict):
            return {k: self._convert_numpy_values(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_numpy_values(item) for item in obj]
        elif isinstance(obj, (np.int_, np.intc, np.intp, np.int8, np.int16, np.int32, np.int64, np.uint8,
                             np.uint16, np.uint32, np.uint64)):
            return int(obj)
        elif isinstance(obj, (np.float_, np.float16, np.float32, np.float64)):
            return float(obj)
        elif isinstance(obj, (np.ndarray,)):
            return self._convert_numpy_values(obj.tolist())
        else:
            return obj