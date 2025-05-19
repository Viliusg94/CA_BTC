import os
import json
import logging
import tensorflow as tf
from datetime import datetime
import numpy as np
from app.models.model_checkpoint import ModelCheckpoint

logger = logging.getLogger(__name__)

class CheckpointConfig:
    """Klasė skirta išsaugojimų (checkpoints) konfigūracijos valdymui"""
    
    def __init__(self, enable_checkpoints=True, save_frequency=5, max_checkpoints=10, save_best_only=False):
        """
        Inicializuoja išsaugojimų konfigūraciją
        
        Args:
            enable_checkpoints (bool): Ar įgalinti išsaugojimus
            save_frequency (int): Kas kiek epochų atlikti išsaugojimą
            max_checkpoints (int): Maksimalus išsaugojimų skaičius
            save_best_only (bool): Ar saugoti tik geriausią modelį
        """
        self.enable_checkpoints = enable_checkpoints
        self.save_frequency = save_frequency
        self.max_checkpoints = max_checkpoints
        self.save_best_only = save_best_only
    
    def should_save_checkpoint(self, epoch):
        """
        Patikrina, ar reikia išsaugoti modelį šioje epochoje
        
        Args:
            epoch (int): Dabartinė epocha
            
        Returns:
            bool: Ar reikia išsaugoti modelį
        """
        # Jei išsaugojimai išjungti, grąžiname False
        if not self.enable_checkpoints:
            return False
        
        # Jei išsaugoti tik geriausius
        if self.save_best_only and current_metrics and best_metrics:
            # Tikriname, ar dabartinė metrika yra geresnė už geriausią
            metric_improved = False
            
            # Gaunama stebima metrika
            current_value = current_metrics.get(self.metrics_to_monitor)
            best_value = best_metrics.get(self.metrics_to_monitor)
            
            if current_value is not None and best_value is not None:
                # Jei stebima loss metrika, mažesnė reikšmė yra geresnė
                if 'loss' in self.metrics_to_monitor:
                    metric_improved = current_value < best_value
                # Kitoms metrikoms (accuracy ir pan.) didesnė reikšmė geresnė
                else:
                    metric_improved = current_value > best_value
                
                return metric_improved
            
            return False
        
        # Dabar tikriname, ar epocha yra kartotinis save_frequency
        return epoch % self.save_frequency == 0


class CheckpointService:
    """Servisas skirtas išsaugojimų valdymui"""
    
    def __init__(self, model_id, base_dir="data/checkpoints"):
        """
        Inicializuoja išsaugojimų servisą
        
        Args:
            model_id (str): Modelio ID, kuriam bus atliekami išsaugojimai
            base_dir (str): Bazinis katalogas išsaugojimams
        """
        # Pagrindiniai nustatymai
        self.model_id = model_id
        self.base_dir = base_dir
        
        # Išsaugojimų konfigūracija
        self.save_interval = 5  # Kas kiek epochų atlikti išsaugojimą
        self.max_checkpoints = 10  # Maksimalus išsaugojimų skaičius
        self.metric_to_monitor = 'val_loss'  # Metrika, pagal kurią nustatomas geriausias modelis
        self.monitor_mode = 'min'  # 'min' arba 'max' - ar mažesnė metrika geresnė, ar didesnė
        
        # Sukuriame katalogą, jei jo nėra
        checkpoint_dir = Path(base_dir) / model_id
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        # Sekimo kintamieji
        self.best_metric_value = float('inf') if self.monitor_mode == 'min' else float('-inf')
        self.best_checkpoint_id = None
    
    def configure(self, save_interval=5, max_checkpoints=10, metric_to_monitor='val_loss', monitor_mode='min'):
        """
        Konfigūruoja išsaugojimų servisą
        
        Args:
            save_interval (int): Kas kiek epochų atlikti išsaugojimą
            max_checkpoints (int): Maksimalus išsaugojimų skaičius
            metric_to_monitor (str): Metrika, pagal kurią nustatomas geriausias modelis
            monitor_mode (str): 'min' arba 'max' - ar mažesnė metrika geresnė, ar didesnė
        """
        # Atnaujiname konfigūraciją
        self.save_interval = save_interval
        self.max_checkpoints = max_checkpoints
        self.metric_to_monitor = metric_to_monitor
        self.monitor_mode = monitor_mode
        
        # Nustatome pradinę geriausios metrikos reikšmę
        self.best_metric_value = float('inf') if self.monitor_mode == 'min' else float('-inf')
    
    def should_save_checkpoint(self, epoch):
        """
        Patikrina, ar reikia išsaugoti modelį šioje epochoje
        
        Args:
            epoch (int): Dabartinė epocha
            
        Returns:
            bool: Ar reikia išsaugoti
        """
        # Išsaugome pirmąją epochą
        if epoch == 0:
            return True
        
        # Išsaugome kas nustatytą intervalą
        if epoch % self.save_interval == 0:
            return True
        
        return False
    
    def is_better_checkpoint(self, metrics):
        """
        Patikrina, ar dabartinis modelis yra geresnis pagal stebimą metriką
        
        Args:
            metrics (dict): Modelio metrikos
            
        Returns:
            bool: Ar dabartinis modelis yra geresnis
        """
        # Tikriname, ar yra stebima metrika
        if self.metric_to_monitor not in metrics:
            return False
        
        # Gauname dabartinę metrikos reikšmę
        current_value = metrics[self.metric_to_monitor]
        
        # Praleidžiame NaN reikšmes
        if isinstance(current_value, (np.ndarray, np.generic)):
            current_value = current_value.item()  # Konvertuojame į Python tipą
        
        if np.isnan(current_value):
            return False
        
        # Tikriname, ar tai geresnė reikšmė
        if self.monitor_mode == 'min':
            return current_value < self.best_metric_value
        else:
            return current_value > self.best_metric_value
    
    def save_checkpoint(self, epoch, metrics, parameters, weights_data=None):
        """
        Išsaugo modelio būseną kaip checkpoint
        
        Args:
            epoch (int): Dabartinė epocha
            metrics (dict): Modelio metrikos
            parameters (dict): Modelio parametrai
            weights_data (object): Modelio svorių duomenys
            
        Returns:
            ModelCheckpoint: Išsaugojimo objektas arba None, jei išsaugojimas nepavyko
        """
        try:
            # Sukuriame naują išsaugojimą
            checkpoint = ModelCheckpoint(
                model_id=self.model_id,
                epoch=epoch,
                metrics=metrics,
                parameters=parameters
            )
            
            # Patikriname, ar tai geriausias modelis
            is_best = self.is_better_checkpoint(metrics)
            
            # Jei tai geriausias modelis, atnaujiname stebimos metrikos reikšmę ir ID
            if is_best:
                self.best_metric_value = metrics[self.metric_to_monitor]
                self.best_checkpoint_id = checkpoint.checkpoint_id
                checkpoint.mark_as_best()
                checkpoint.add_note(f"Geriausias modelis pagal {self.metric_to_monitor}")
            
            # Išsaugoame išsaugojimą
            success = checkpoint.save(
                base_dir=self.base_dir, 
                save_weights=weights_data is not None,
                weights_data=weights_data
            )
            
            if success:
                print(f"Išsaugotas modelio tarpinis išsaugojimas (checkpoint) epochoje {epoch}: ID={checkpoint.checkpoint_id}")
                
                # Atnaujinti buvusius "geriausius" išsaugojimus, jei reikia
                if is_best:
                    self._update_previous_best_checkpoints()
                
                # Valome senus išsaugojimus, jei viršijome limitą
                self._cleanup_old_checkpoints()
                
                return checkpoint
            else:
                print(f"Nepavyko išsaugoti modelio išsaugojimo epochoje {epoch}")
                return None
        
        except Exception as e:
            print(f"Klaida išsaugant modelio išsaugojimą: {str(e)}")
            return None
    
    def _update_previous_best_checkpoints(self):
        """
        Atnaujina ankstesnius "geriausius" išsaugojimus, kad tik vienas būtų pažymėtas kaip geriausias
        """
        try:
            # Gauname visus modelio išsaugojimus
            checkpoints = ModelCheckpoint.list_all_for_model(self.model_id, self.base_dir)
            
            # Einame per visus išsaugojimus ir nuimame "geriauso" žymą, išskyrus dabartinį
            for checkpoint in checkpoints:
                if checkpoint.checkpoint_id != self.best_checkpoint_id and checkpoint.is_best:
                    checkpoint.is_best = False
                    checkpoint.save(base_dir=self.base_dir, save_weights=False)
        
        except Exception as e:
            print(f"Klaida atnaujinant ankstesnius geriausius išsaugojimus: {str(e)}")
    
    def _cleanup_old_checkpoints(self):
        """
        Išvalo senus išsaugojimus, kai jų skaičius viršija nustatytą limitą
        """
        try:
            # Gauname visus modelio išsaugojimus
            checkpoints = ModelCheckpoint.list_all_for_model(self.model_id, self.base_dir, sort_by="created_at")
            
            # Jei išsaugojimų skaičius viršija limitą, šaliname seniausius
            if len(checkpoints) > self.max_checkpoints:
                # Rūšiuojame pagal sukūrimo laiką (seniausi pradžioje)
                checkpoints_to_delete = checkpoints[:(len(checkpoints) - self.max_checkpoints)]
                
                # Ištriname senus išsaugojimus, išskyrus pažymėtus kaip geriausius
                for checkpoint in checkpoints_to_delete:
                    if not checkpoint.is_best:
                        checkpoint.delete(base_dir=self.base_dir)
                        print(f"Ištrintas senas išsaugojimas: ID={checkpoint.checkpoint_id}, epocha={checkpoint.epoch}")
        
        except Exception as e:
            print(f"Klaida valant senus išsaugojimus: {str(e)}")
    
    def load_best_checkpoint(self):
        """
        Užkrauna geriausią modelio išsaugojimą
        
        Returns:
            ModelCheckpoint: Geriausias išsaugojimas arba None, jei nerasta
        """
        try:
            # Jei nežinome geriausio išsaugojimo ID, ieškome pagal žymą
            if not self.best_checkpoint_id:
                # Gauname visus modelio išsaugojimus
                checkpoints = ModelCheckpoint.list_all_for_model(self.model_id, self.base_dir)
                
                # Ieškome pažymėto kaip geriausio
                for checkpoint in checkpoints:
                    if checkpoint.is_best:
                        self.best_checkpoint_id = checkpoint.checkpoint_id
                        break
            
            # Jei vis dar nežinome geriausio išsaugojimo ID, reiškia nėra geriauso
            if not self.best_checkpoint_id:
                return None
            
            # Užkrauname geriausią išsaugojimą
            return ModelCheckpoint.load(self.best_checkpoint_id, self.model_id, self.base_dir)
        
        except Exception as e:
            print(f"Klaida užkraunant geriausią išsaugojimą: {str(e)}")
            return None
    
    def load_checkpoint_by_epoch(self, epoch):
        """
        Užkrauna išsaugojimą pagal epochos numerį
        
        Args:
            epoch (int): Epochos numeris
            
        Returns:
            ModelCheckpoint: Išsaugojimas arba None, jei nerasta
        """
        try:
            # Gauname visus modelio išsaugojimus
            checkpoints = ModelCheckpoint.list_all_for_model(self.model_id, self.base_dir)
            
            # Ieškome išsaugojimo su nurodyta epocha
            for checkpoint in checkpoints:
                if checkpoint.epoch == epoch:
                    return checkpoint
            
            # Neradome išsaugojimo su nurodyta epocha
            return None
        
        except Exception as e:
            print(f"Klaida užkraunant išsaugojimą pagal epochą: {str(e)}")
            return None
    
    def get_checkpoint_stats(self):
        """
        Grąžina išsaugojimų statistiką
        
        Returns:
            dict: Išsaugojimų statistika
        """
        try:
            # Gauname visus modelio išsaugojimus
            checkpoints = ModelCheckpoint.list_all_for_model(self.model_id, self.base_dir)
            
            # Paskaičiuojame statistiką
            total_checkpoints = len(checkpoints)
            best_checkpoint = None
            
            # Randame geriausią išsaugojimą
            for checkpoint in checkpoints:
                if checkpoint.is_best:
                    best_checkpoint = checkpoint
                    break
            
            # Priskiriame paskutinį išsaugojimą kaip naujausią
            latest_checkpoint = checkpoints[-1] if checkpoints else None
            
            # Grąžiname statistiką
            return {
                "total_checkpoints": total_checkpoints,
                "best_checkpoint": best_checkpoint.to_dict() if best_checkpoint else None,
                "latest_checkpoint": latest_checkpoint.to_dict() if latest_checkpoint else None,
            }
        
        except Exception as e:
            print(f"Klaida gaunant išsaugojimų statistiką: {str(e)}")
            return {
                "total_checkpoints": 0,
                "best_checkpoint": None,
                "latest_checkpoint": None,
            }
    
    def save_checkpoint_v2(self, model, epoch, metrics, model_filename=None, training_id=None):
        """
        Išsaugo modelio tarpinį tašką (v2)
        
        Args:
            model: Modelio objektas
            epoch (int): Epochos numeris
            metrics (dict): Metrikos reikšmės
            model_filename (str): Modelio failo pavadinimas (jei None, sukuriamas automatiškai)
            training_id (str): Treniravimo sesijos ID
            
        Returns:
            str: Išsaugojimo kelias
        """
        try:
            # Sukuriame modelio išsaugojimo katalogą
            model_dir = os.path.join(self.checkpoints_dir, model_filename or 'model')
            os.makedirs(model_dir, exist_ok=True)
            
            # Sukuriame išsaugojimo pavadinimą
            checkpoint_name = f"checkpoint_epoch_{epoch}"
            checkpoint_path = os.path.join(model_dir, f"{checkpoint_name}.h5")
            
            # Išsaugome modelį
            model.save(checkpoint_path)
            
            # Išsaugojame metrikos informaciją
            metrics_path = os.path.join(model_dir, f"{checkpoint_name}_metrics.json")
            
            # Pridedame papildomą informaciją
            metrics_info = {
                'epoch': epoch,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'training_id': training_id,
                'metrics': metrics
            }
            
            with open(metrics_path, 'w') as f:
                json.dump(metrics_info, f, indent=4)
            
            # Patikriname, ar reikia ištrinti senus išsaugojimus
            self._cleanup_old_checkpoints(model_dir)
            
            # Grąžiname kelią
            return checkpoint_path
            
        except Exception as e:
            logger.error(f"Klaida išsaugant modelio tarpinį tašką: {e}")
            return None
    
    def _cleanup_old_checkpoints(self, model_dir):
        """
        Išvalo senus išsaugojimus, jei viršijamas maksimalus skaičius
        
        Args:
            model_dir (str): Modelio direktorija
        """
        try:
            # Gauname visus .h5 failus
            h5_files = [f for f in os.listdir(model_dir) if f.endswith('.h5')]
            
            # Jei jų mažiau nei maksimumas, nieko nedarome
            if len(h5_files) <= self.max_checkpoints:
                return
            
            # Rūšiuojame pagal epoch numerį (randamas iš failo pavadinimo)
            def get_epoch(filename):
                try:
                    return int(filename.split('_')[-1].split('.')[0])
                except:
                    return 0
            
            h5_files.sort(key=get_epoch)
            
            # Ištriname seniausius išsaugojimus
            files_to_remove = h5_files[:-self.max_checkpoints]
            
            for filename in files_to_remove:
                # Ištrinti .h5 failą
                os.remove(os.path.join(model_dir, filename))
                
                # Taip pat ištrinti susijusį metrics.json failą
                metrics_filename = filename.replace('.h5', '_metrics.json')
                metrics_path = os.path.join(model_dir, metrics_filename)
                
                if os.path.exists(metrics_path):
                    os.remove(metrics_path)
                    
            logger.info(f"Ištrinta {len(files_to_remove)} senų išsaugojimų")
            
        except Exception as e:
            logger.error(f"Klaida tvarkant senus išsaugojimus: {e}")
    
    def get_checkpoints(self, model_filename):
        """
        Gauna visus modelio išsaugojimus
        
        Args:
            model_filename (str): Modelio failo pavadinimas
            
        Returns:
            list: Išsaugojimų sąrašas
        """
        try:
            model_dir = os.path.join(self.checkpoints_dir, model_filename)
            
            # Jei katalogo nėra, grąžiname tuščią sąrašą
            if not os.path.exists(model_dir):
                return []
            
            # Gauname visus .h5 failus
            h5_files = [f for f in os.listdir(model_dir) if f.endswith('.h5')]
            
            checkpoints = []
            
            for h5_file in h5_files:
                # Gauname epochos numerį
                try:
                    epoch = int(h5_file.split('_')[-1].split('.')[0])
                except:
                    epoch = 0
                
                # Gauname metrikos failą
                metrics_file = h5_file.replace('.h5', '_metrics.json')
                metrics_path = os.path.join(model_dir, metrics_file)
                
                metrics = {}
                if os.path.exists(metrics_path):
                    with open(metrics_path, 'r') as f:
                        metrics = json.load(f)
                
                # Sukuriame išsaugojimo informaciją
                checkpoint_info = {
                    'filename': h5_file,
                    'path': os.path.join(model_dir, h5_file),
                    'epoch': epoch,
                    'metrics': metrics.get('metrics', {}),
                    'timestamp': metrics.get('timestamp', '')
                }
                
                checkpoints.append(checkpoint_info)
            
            # Rūšiuojame pagal epochą (didžiausia pirma)
            checkpoints.sort(key=lambda x: x['epoch'], reverse=True)
            
            return checkpoints
            
        except Exception as e:
            logger.error(f"Klaida gaunant modelio išsaugojimus: {e}")
            return []
    
    def get_best_checkpoint(self, model_filename):
        """
        Gauna geriausią modelio išsaugojimą pagal stebimą metriką
        
        Args:
            model_filename (str): Modelio failo pavadinimas
            
        Returns:
            dict: Geriausio išsaugojimo informacija arba None, jei nėra išsaugojimų
        """
        try:
            # Gauname visus išsaugojimus
            checkpoints = self.get_checkpoints(model_filename)
            
            if not checkpoints:
                return None
            
            # Rūšiuojame pagal stebimą metriką
            metric = self.metric_to_monitor
            
            def get_metric_value(checkpoint):
                return checkpoint['metrics'].get(metric, float('inf') if self.monitor_mode == 'min' else -float('inf'))
            
            if self.monitor_mode == 'min':
                checkpoints.sort(key=get_metric_value)
            else:
                checkpoints.sort(key=get_metric_value, reverse=True)
            
            # Grąžiname geriausią
            return checkpoints[0]
            
        except Exception as e:
            logger.error(f"Klaida gaunant geriausią modelio išsaugojimą: {e}")
            return None
    
    def delete_checkpoint(self, model_filename, checkpoint_filename):
        """
        Ištrina modelio išsaugojimą
        
        Args:
            model_filename (str): Modelio failo pavadinimas
            checkpoint_filename (str): Išsaugojimo failo pavadinimas
            
        Returns:
            bool: Ar pavyko ištrinti
        """
        try:
            model_dir = os.path.join(self.checkpoints_dir, model_filename)
            checkpoint_path = os.path.join(model_dir, checkpoint_filename)
            
            # Patikriname, ar failas egzistuoja
            if not os.path.exists(checkpoint_path):
                return False
            
            # Ištriname .h5 failą
            os.remove(checkpoint_path)
            
            # Taip pat ištriname susijusį metrics.json failą
            metrics_filename = checkpoint_filename.replace('.h5', '_metrics.json')
            metrics_path = os.path.join(model_dir, metrics_filename)
            
            if os.path.exists(metrics_path):
                os.remove(metrics_path)
            
            return True
            
        except Exception as e:
            logger.error(f"Klaida trinant modelio išsaugojimą: {e}")
            return False
        
        # Pridėti naują metodą išsaugojimo gavimui ir modelio atkūrimui

    def get_checkpoint(self, model_id, checkpoint_id):
        """
        Gauna konkretų modelio išsaugojimą
        
        Args:
            model_id (str): Modelio ID
            checkpoint_id (str): Išsaugojimo ID
            
        Returns:
            dict: Išsaugojimo informacija arba None, jei nerastas
        """
        try:
            # Bandome rasti išsaugojimą pagal ID
            checkpoint = self.load_checkpoint(checkpoint_id, model_id)
            
            if not checkpoint:
                return None
            
            # Grąžiname išsaugojimo duomenis
            return checkpoint.to_dict()
        
        except Exception as e:
            logger.error(f"Klaida gaunant išsaugojimą: {str(e)}")
            return None

    def restore_model(self, model_id, checkpoint_id):
        """
        Atkuria modelį iš išsaugojimo
        
        Args:
            model_id (str): Modelio ID
            checkpoint_id (str): Išsaugojimo ID
            
        Returns:
            tuple: (success, message) - operacijos rezultatas
        """
        try:
            # Gauname išsaugojimą
            checkpoint = self.load_checkpoint(checkpoint_id, model_id)
            
            if not checkpoint:
                return False, "Išsaugojimas nerastas"
            
            # Tikriname, ar yra svorių failas
            if not checkpoint.weights_path or not os.path.exists(checkpoint.weights_path):
                return False, "Išsaugojimo svorių failas nerastas"
            
            # Užkrauname modelį (čia reikėtų pritaikyti pagal jūsų sistemą)
            try:
                # Užkrauname svorius
                weights_data = checkpoint.load_weights()
                
                if not weights_data:
                    return False, "Nepavyko užkrauti modelio svorių"
                
                # Atkuriame modelį iš svorių
                # Čia reikėtų pritaikyti pagal jūsų modelio atkūrimo logiką
                
                # Atnaujiname išsaugojimo būseną
                checkpoint.status = "restored"
                checkpoint.updated_at = datetime.datetime.now()
                checkpoint.add_note(f"Modelis atkurtas iš išsaugojimo {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                checkpoint.save(save_weights=False)
                
                return True, "Modelis sėkmingai atkurtas iš išsaugojimo"
            
            except Exception as e:
                logger.error(f"Klaida atkuriant modelį: {str(e)}")
                return False, f"Klaida atkuriant modelį: {str(e)}"
        
        except Exception as e:
            logger.error(f"Klaida atkuriant modelį iš išsaugojimo: {str(e)}")
            return False, f"Klaida: {str(e)}"
    
    def restore_model_from_checkpoint(self, model_id, checkpoint_id):
        """
        Atkuria modelį iš išsaugojimo taško (checkpoint)
        
        Args:
            model_id (str): Modelio ID
            checkpoint_id (str): Išsaugojimo taško ID
        
        Returns:
            tuple: (bool, str) - (sėkmė, pranešimas)
        """
        try:
            # Inicializuojame atstatymo būseną
            self._update_restore_status(
                model_id, checkpoint_id, 
                'initializing', 25, 
                'Inicijuojamas modelio atstatymas', 
                'Pradedamas modelio atstatymas iš išsaugojimo'
            )
            
            # Gauname išsaugojimo informaciją
            checkpoint = self.get_checkpoint(model_id, checkpoint_id)
            
            if not checkpoint:
                self._update_restore_status(
                    model_id, checkpoint_id, 
                    'failed', 0, 
                    'Išsaugojimas nerastas', 
                    'Klaida: Nurodytas išsaugojimas nerastas'
                )
                return False, "Nurodytas išsaugojimas nerastas"
            
            # Tikriname, ar išsaugojimas turi svorių failo kelią
            if not checkpoint.get('weights_path') or not os.path.exists(checkpoint['weights_path']):
                self._update_restore_status(
                    model_id, checkpoint_id, 
                    'failed', 0, 
                    'Išsaugojimo svorių failas nerastas', 
                    'Klaida: Išsaugojimo svorių failas nerastas'
                )
                return False, "Išsaugojimo svorių failas nerastas"
            
            # Atnaujiname būseną - atkuriami svoriai
            self._update_restore_status(
                model_id, checkpoint_id, 
                'loading_weights', 50, 
                'Atkuriami modelio svoriai', 
                f"Atkuriami modelio svoriai iš failo: {checkpoint['weights_path']}"
            )
            
            try:
                # Atkuriame modelį (Čia reikėtų pritaikyti pagal jūsų TensorFlow/Keras naudojimą)
                import tensorflow as tf
                
                # Užkrauname modelį iš išsaugojimo
                model = tf.keras.models.load_model(checkpoint['weights_path'])
                
                # Išsaugome modelį į pagrindinį modelio failą
                model_path = os.path.join('app', 'static', 'models', f"{model_id}.h5")
                model.save(model_path)
                
                # Atnaujiname būseną - atnaujinami metaduomenys
                self._update_restore_status(
                    model_id, checkpoint_id, 
                    'updating_metadata', 75, 
                    'Atnaujinama modelio meta informacija', 
                    'Modelio svoriai atkurti, atnaujinama meta informacija'
                )
                
                # Atnaujiname modelio meta informaciją
                model_meta_path = os.path.join('app', 'static', 'models', f"{model_id}_meta.json")
                
                if os.path.exists(model_meta_path):
                    with open(model_meta_path, 'r') as f:
                        model_info = json.load(f)
                    
                    # Pridedame informaciją apie atstatymą
                    model_info['restored_from'] = {
                        'checkpoint_id': checkpoint_id,
                        'epoch': checkpoint['epoch'],
                        'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'metrics': checkpoint.get('metrics', {})
                    }
                    
                    # Išsaugome atnaujintą informaciją
                    with open(model_meta_path, 'w') as f:
                        json.dump(model_info, f, indent=2)
                
                # Atnaujiname būseną - baigta
                self._update_restore_status(
                    model_id, checkpoint_id, 
                    'completed', 100, 
                    'Modelis sėkmingai atstatytas', 
                    'Modelis sėkmingai atstatytas iš išsaugojimo'
                )
                
                return True, "Modelis sėkmingai atstatytas iš išsaugojimo"
                
            except Exception as e:
                # Registruojame klaidą
                logger.error(f"Klaida atkuriant modelį: {str(e)}")
                
                # Atnaujiname būseną - klaida
                self._update_restore_status(
                    model_id, checkpoint_id, 
                    'failed', 0, 
                    f"Klaida atkuriant modelį: {str(e)}", 
                    f"Klaida: {str(e)}"
                )
                
                return False, f"Klaida atkuriant modelį: {str(e)}"
    
        except Exception as e:
            # Registruojame klaidą
            logger.error(f"Klaida atkuriant modelį: {str(e)}")
            
            # Atnaujiname būseną - klaida
            self._update_restore_status(
                model_id, checkpoint_id, 
                'failed', 0, 
                f"Klaida: {str(e)}", 
                f"Klaida: {str(e)}"
            )
            
            return False, f"Klaida: {str(e)}"
    
    # Pridėti naujus metodus atstatymo būsenos stebėjimui

    def get_restore_status(self, model_id, checkpoint_id):
        """
        Gauna modelio atstatymo būseną
        
        Args:
            model_id (str): Modelio ID
            checkpoint_id (str): Išsaugojimo ID
        
        Returns:
            tuple: (status, progress, message, logs)
                status (str): Operacijos būsena
                progress (int): Operacijos progresas (0-100)
                message (str): Pranešimas
                logs (list): Operacijos logai
        """
        try:
            # Tikriname, ar yra atstatymo būsenos failas
            restore_status_path = os.path.join('app', 'static', 'restore_operations', f"{model_id}_{checkpoint_id}.json")
            
            if os.path.exists(restore_status_path):
                with open(restore_status_path, 'r') as f:
                    status_data = json.load(f)
                
                return (
                    status_data.get('status', 'unknown'),
                    status_data.get('progress', 0),
                    status_data.get('message', ''),
                    status_data.get('logs', [])
                )
            else:
                # Jei nėra būsenos failo, grąžiname pradinę būseną
                return ('initializing', 0, 'Operacija dar neprasidėjo', [])
        
        except Exception as e:
            logger.error(f"Klaida gaunant atstatymo būseną: {str(e)}")
            return ('failed', 0, f"Klaida: {str(e)}", [])

    def cancel_restore(self, model_id, checkpoint_id):
        """
        Nutraukia modelio atstatymo operaciją
        
        Args:
            model_id (str): Modelio ID
            checkpoint_id (str): Išsaugojimo ID
        
        Returns:
            tuple: (success, message) - operacijos rezultatas
        """
        try:
            # Tikriname, ar yra atstatymo būsenos failas
            restore_status_path = os.path.join('app', 'static', 'restore_operations', f"{model_id}_{checkpoint_id}.json")
            
            if os.path.exists(restore_status_path):
                with open(restore_status_path, 'r') as f:
                    status_data = json.load(f)
                
                # Jei operacija jau baigta arba nepavyko, grąžiname pranešimą
                if status_data.get('status') in ['completed', 'failed']:
                    return False, "Operacija jau baigta arba nepavyko"
                
                # Atnaujiname būseną
                status_data['status'] = 'failed'
                status_data['message'] = 'Operacija nutraukta vartotojo'
                status_data['logs'].append('[INFO] Operacija nutraukta vartotojo')
                
                with open(restore_status_path, 'w') as f:
                    json.dump(status_data, f, indent=2)
                
                return True, "Operacija sėkmingai nutraukta"
            else:
                return False, "Operacija nerasta"
        
        except Exception as e:
            logger.error(f"Klaida nutraukiant atstatymą: {str(e)}")
            return False, f"Klaida: {str(e)}"

    def _update_restore_status(self, model_id, checkpoint_id, status, progress, message=None, log=None):
        """
        Atnaujina modelio atstatymo būseną
        
        Args:
            model_id (str): Modelio ID
            checkpoint_id (str): Išsaugojimo ID
            status (str): Nauja būsena
            progress (int): Naujas progresas (0-100)
            message (str, optional): Naujas pranešimas
            log (str, optional): Naujas log įrašas
        """
        try:
            # Sukuriame būsenos failų katalogą, jei jo nėra
            os.makedirs(os.path.join('app', 'static', 'restore_operations'), exist_ok=True)
            
            # Būsenos failo kelias
            restore_status_path = os.path.join('app', 'static', 'restore_operations', f"{model_id}_{checkpoint_id}.json")
            
            # Jei failas egzistuoja, užkrauname esamus duomenis
            if os.path.exists(restore_status_path):
                with open(restore_status_path, 'r') as f:
                    status_data = json.load(f)
            else:
                # Sukuriame naują būsenos objektą
                status_data = {
                    'model_id': model_id,
                    'checkpoint_id': checkpoint_id,
                    'status': 'initializing',
                    'progress': 0,
                    'message': '',
                    'logs': [],
                    'start_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'update_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            
            # Atnaujiname būseną
            status_data['status'] = status
            status_data['progress'] = progress
            status_data['update_time'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            if message:
                status_data['message'] = message
            
            if log:
                timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                status_data['logs'].append(f"[{timestamp}] {log}")
            
            # Išsaugome atnaujintą būseną
            with open(restore_status_path, 'w') as f:
                json.dump(status_data, f, indent=2)
        
        except Exception as e:
            logger.error(f"Klaida atnaujinant atstatymo būseną: {str(e)}")

    def get_checkpoint_comparison(self, model_id, checkpoint1_id, checkpoint2_id):
        """
        Gauna dviejų išsaugojimų palyginimo informaciją
        
        Args:
            model_id (str): Modelio ID
            checkpoint1_id (str): Pirmo išsaugojimo ID
            checkpoint2_id (str): Antro išsaugojimo ID
        
        Returns:
            dict: Palyginimo rezultatai
        """
        try:
            # Gauname išsaugojimus
            checkpoint1 = self.get_checkpoint(model_id, checkpoint1_id)
            checkpoint2 = self.get_checkpoint(model_id, checkpoint2_id)
            
            if not checkpoint1 or not checkpoint2:
                logger.error("Nepavyko rasti vieno ar abiejų išsaugojimų")
                return None
            
            # Skaičiuojame metrikų pokyčius
            metrics_comparison = {}
            
            # Surenkame visus metrikų pavadinimus
            all_metrics = set()
            
            for metric in checkpoint1.get('metrics', {}).keys():
                all_metrics.add(metric)
            
            for metric in checkpoint2.get('metrics', {}).keys():
                all_metrics.add(metric)
            
            # Skaičiuojame pokyčius kiekvienai metrikai
            for metric in all_metrics:
                value1 = checkpoint1.get('metrics', {}).get(metric)
                value2 = checkpoint2.get('metrics', {}).get(metric)
                
                # Jei nėra reikšmių, praleidiame
                if value1 is None or value2 is None:
                    continue
                
                # Skaičiuojame absoliutų pokytį
                absolute_change = value2 - value1
                
                # Skaičiuojame procentinį pokytį (jei įmanoma)
                if value1 != 0:
                    percentage_change = (absolute_change / value1) * 100
                else:
                    percentage_change = 0
                
                # Nustatome, ar pokytis yra teigiamas (kai kurių metrikų atveju didesnė reikšmė geresnė)
                is_higher_better = metric.endswith('accuracy') or metric.endswith('precision') or metric.endswith('recall') or metric.endswith('f1')
                is_improved = (is_higher_better and absolute_change > 0) or (not is_higher_better and absolute_change < 0)
                
                # Sukuriame palyginimo informaciją
                metrics_comparison[metric] = {
                    'value1': value1,
                    'value2': value2,
                    'absolute_change': absolute_change,
                    'percentage_change': percentage_change,
                    'is_improved': is_improved,
                    'is_higher_better': is_higher_better
                }
            
            # Grąžiname bendrą palyginimo rezultatą
            return {
                'checkpoint1': checkpoint1,
                'checkpoint2': checkpoint2,
                'metrics_comparison': metrics_comparison,
                'epoch_difference': checkpoint2.get('epoch', 0) - checkpoint1.get('epoch', 0),
                'is_consecutive': checkpoint2.get('epoch', 0) - checkpoint1.get('epoch', 0) == 1
            }
        
        except Exception as e:
            logger.error(f"Klaida lyginant išsaugojimus: {str(e)}")
            return None

    def get_model_checkpoint_range(self, model_id, start_epoch, end_epoch):
        """
        Gauna modelio išsaugojimų informaciją nurodytame epochų intervale
        
        Args:
            model_id (str): Modelio ID
            start_epoch (int): Pradžios epocha
            end_epoch (int): Pabaigos epocha
        
        Returns:
            list: Išsaugojimų sąrašas nurodytame intervale
        """
        try:
            # Gauname visus modelio išsaugojimus
            all_checkpoints = self.get_checkpoints(model_id)
            
            # Filtruojame pagal epochų intervalą
            range_checkpoints = [
                cp for cp in all_checkpoints 
                if cp.get('epoch', 0) >= start_epoch and cp.get('epoch', 0) <= end_epoch
            ]
            
            # Rūšiuojame pagal epochų didėjimą
            range_checkpoints.sort(key=lambda x: x.get('epoch', 0))
            
            return range_checkpoints
        
        except Exception as e:
            logger.error(f"Klaida gaunant išsaugojimų intervalą: {str(e)}")
            return []

    def analyze_checkpoint_evolution(self, model_id):
        """
        Analizuoja išsaugojimų evoliuciją per laiką
        
        Args:
            model_id (str): Modelio ID
        
        Returns:
            dict: Analizės rezultatai
        """
        try:
            # Gauname visus modelio išsaugojimus
            checkpoints = self.get_checkpoints(model_id)
            
            # Jei išsaugojimų nėra arba per mažai, grąžiname tuščią rezultatą
            if not checkpoints or len(checkpoints) < 2:
                return {
                    'has_enough_data': False,
                    'trends': {},
                    'significant_changes': []
                }
            
            # Rūšiuojame pagal epochą
            checkpoints.sort(key=lambda x: x.get('epoch', 0))
            
            # Analizuojame metrikų tendencijas
            trends = {}
            significant_changes = []
            
            # Surenkame visus metrikų pavadinimus
            all_metrics = set()
            for cp in checkpoints:
                for metric in cp.get('metrics', {}).keys():
                    if cp.get('metrics', {}).get(metric) is not None:
                        all_metrics.add(metric)
            
            # Analizuojame kiekvienos metrikos tendenciją
            for metric in all_metrics:
                # Surenkame visas metrikos reikšmes
                values = [cp.get('metrics', {}).get(metric) for cp in checkpoints if cp.get('metrics', {}).get(metric) is not None]
                
                if not values or len(values) < 2:
                    continue
                
                # Skaičiuojame tendenciją (sumažėjimas, padidėjimas, svyravimas)
                first_value = values[0]
                last_value = values[-1]
                min_value = min(values)
                max_value = max(values)
                
                # Nustatome, ar aukštesnės reikšmės yra geresnės šiai metrikai
                is_higher_better = metric.endswith('accuracy') or metric.endswith('precision') or metric.endswith('recall') or metric.endswith('f1')
                
                # Skaičiuojame absoliutų pokytį nuo pradžios iki pabaigos
                total_change = last_value - first_value
                
                # Skaičiuojame procentinį pokytį
                if first_value != 0:
                    percentage_change = (total_change / first_value) * 100
                else:
                    percentage_change = 0
                
                # Nustatome tendenciją
                trend_direction = 'improved' if (is_higher_better and total_change > 0) or (not is_higher_better and total_change < 0) else 'worsened'
                
                # Analizuojame svyravimus
                has_fluctuations = len(values) >= 3 and max_value != last_value and min_value != last_value
                
                # Surenkame reikšmingus pokyčius (daugiau nei 10% pokytis tarp gretimų epochų)
                for i in range(1, len(values)):
                    prev_value = values[i-1]
                    curr_value = values[i]
                    
                    if prev_value == 0:
                        continue
                    
                    change = curr_value - prev_value
                    change_percent = (change / prev_value) * 100
                    
                    # Jei pokytis didesnis nei 10%, laikome jį reikšmingu
                    if abs(change_percent) > 10:
                        significant_changes.append({
                            'metric': metric,
                            'epoch': checkpoints[i].get('epoch', 0),
                            'previous_value': prev_value,
                            'current_value': curr_value,
                            'change_percent': change_percent,
                            'is_improvement': (is_higher_better and change > 0) or (not is_higher_better and change < 0)
                        })
                
                # Saugome tendencijos informaciją
                trends[metric] = {
                    'first_value': first_value,
                    'last_value': last_value,
                    'min_value': min_value,
                    'max_value': max_value,
                    'total_change': total_change,
                    'percentage_change': percentage_change,
                    'trend_direction': trend_direction,
                    'has_fluctuations': has_fluctuations,
                    'is_higher_better': is_higher_better
                }
            
            # Rūšiuojame reikšmingus pokyčius pagal mažėjantį pokytį
            significant_changes.sort(key=lambda x: abs(x.get('change_percent', 0)), reverse=True)
            
            return {
                'has_enough_data': True,
                'trends': trends,
                'significant_changes': significant_changes
            }
        
        except Exception as e:
            logger.error(f"Klaida analizuojant išsaugojimų evoliuciją: {str(e)}")
            return {
                'has_enough_data': False,
                'trends': {},
                'significant_changes': []
            }
    
    # Pridėti metodą parametrų pokyčiams analizuoti

    def analyze_model_parameters(self, model_id, checkpoint1_id, checkpoint2_id):
        """
        Analizuoja modelio parametrų pokyčius tarp dviejų išsaugojimų
        
        Args:
            model_id: Modelio ID
            checkpoint1_id: Pirmojo išsaugojimo ID
            checkpoint2_id: Antrojo išsaugojimo ID
            
        Returns:
            dict: Parametrų pokyčių analizės rezultatai
        """
        try:
            # Importuojame TensorFlow
            import tensorflow as tf
            import numpy as np
            
            # Gauname išsaugojimų informaciją
            checkpoint1 = self.get_checkpoint(model_id, checkpoint1_id)
            checkpoint2 = self.get_checkpoint(model_id, checkpoint2_id)
            
            if not checkpoint1 or not checkpoint2:
                return {
                    "success": False,
                    "message": "Nepavyko rasti vieno ar abiejų išsaugojimų"
                }
            
            # Tikriname, ar egzistuoja svorių failai
            if not checkpoint1.get('weights_path') or not os.path.exists(checkpoint1['weights_path']) or \
               not checkpoint2.get('weights_path') or not os.path.exists(checkpoint2['weights_path']):
                return {
                    "success": False,
                    "message": "Vieno ar abiejų išsaugojimų svorių failai nerasti"
                }
                
            # Užkrauname modelius
            try:
                model1 = tf.keras.models.load_model(checkpoint1['weights_path'])
                model2 = tf.keras.models.load_model(checkpoint2['weights_path'])
            except Exception as e:
                return {
                    "success": False,
                    "message": f"Klaida užkraunant modelius: {str(e)}"
                }
            
            # Analizuojame parametrų skaičių
            params1 = model1.count_params()
            params2 = model2.count_params()
            params_diff = params2 - params1
            
            # Analizuojame sluoksnių struktūrą
            layers1 = len(model1.layers)
            layers2 = len(model2.layers)
            layers_diff = layers2 - layers1
            
            # Analizuojame svorių pokyčius
            layer_weights_analysis = []
            
            # Tikriname tik bendrus sluoksnius
            common_layers = min(layers1, layers2)
            
            for i in range(common_layers):
                layer1 = model1.layers[i]
                layer2 = model2.layers[i]
                
                # Jei sluoksnis turi svorius
                if len(layer1.weights) > 0 and len(layer2.weights) > 0:
                    layer_name = layer1.name
                    
                    # Analizuojame kiekvieną svorių masyvą sluoksnyje
                    for j in range(min(len(layer1.weights), len(layer2.weights))):
                        weight1 = layer1.weights[j].numpy()
                        weight2 = layer2.weights[j].numpy()
                        
                        # Jei formos skiriasi, praleidžiame
                        if weight1.shape != weight2.shape:
                            continue
                        
                        # Apskaičiuojame statistiką
                        weight_diff = weight2 - weight1
                        abs_diff = np.abs(weight_diff)
                        mean_diff = np.mean(abs_diff)
                        max_diff = np.max(abs_diff)
                        variance = np.var(weight_diff)
                        
                        # Procentinis pokytis
                        non_zero_mask = weight1 != 0
                        if np.any(non_zero_mask):
                            percent_change = np.mean(np.abs(weight_diff[non_zero_mask] / weight1[non_zero_mask]) * 100)
                        else:
                            percent_change = 0
                        
                        weight_info = {
                            "layer_name": layer_name,
                            "weight_name": layer1.weights[j].name,
                            "shape": list(weight1.shape),
                            "mean_diff": float(mean_diff),
                            "max_diff": float(max_diff),
                            "variance": float(variance),
                            "percent_change": float(percent_change)
                        }
                        
                        layer_weights_analysis.append(weight_info)
            
            # Gauname modelio dydį (MB)
            import tempfile
            
            # Išsaugome modelius į laikinus failus ir gauname jų dydžius
            with tempfile.NamedTemporaryFile(suffix=".h5") as f1, tempfile.NamedTemporaryFile(suffix=".h5") as f2:
                model1.save(f1.name)
                model2.save(f2.name)
                
                size1 = os.path.getsize(f1.name) / (1024 * 1024)  # Dydis MB
                size2 = os.path.getsize(f2.name) / (1024 * 1024)  # Dydis MB
            
            size_diff = size2 - size1
            size_percent = (size_diff / size1 * 100) if size1 > 0 else 0
            
            # Grąžiname analizės rezultatus
            return {
                "success": True,
                "params_analysis": {
                    "params1": params1,
                    "params2": params2,
                    "params_diff": params_diff,
                    "params_percent": (params_diff / params1 * 100) if params1 > 0 else 0
                },
                "layers_analysis": {
                    "layers1": layers1,
                    "layers2": layers2,
                    "layers_diff": layers_diff
                },
                "weights_analysis": layer_weights_analysis,
                "size_analysis": {
                    "size1": size1,
                    "size2": size2,
                    "size_diff": size_diff,
                    "size_percent": size_percent
                }
            }
        
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": f"Klaida analizuojant parametrus: {str(e)}"
            }