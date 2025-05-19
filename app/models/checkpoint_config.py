import os
import datetime

class CheckpointConfig:
    """
    Klasė, skirta valdyti modelio tarpinių išsaugojimų (checkpoint) konfigūraciją
    """
    
    def __init__(self, 
                 enable_checkpoints=True, 
                 save_frequency=5, 
                 max_checkpoints=10, 
                 save_best_only=False,
                 save_weights_only=False):
        """
        Inicializuojame checkpoint konfigūraciją
        
        Args:
            enable_checkpoints (bool): Ar įjungti tarpinių modelių išsaugojimą
            save_frequency (int): Co kiek epochų išsaugoti modelį
            max_checkpoints (int): Maksimalus išsaugomų modelių skaičius
            save_best_only (bool): Ar išsaugoti tik geriausius modelius pagal validavimo nuostolį
            save_weights_only (bool): Ar išsaugoti tik modelio svorius, ne pilną modelį
        """
        self.enable_checkpoints = enable_checkpoints
        self.save_frequency = max(1, save_frequency)  # Minimalus dažnis - 1 epocha
        self.max_checkpoints = max(1, max_checkpoints)  # Bent 1 checkpoint turi būti išsaugotas
        self.save_best_only = save_best_only
        self.save_weights_only = save_weights_only
        
    def get_checkpoint_path(self, model_id, checkpoint_dir="checkpoints"):
        """
        Grąžina kelią, kur išsaugoti tarpinį modelį
        
        Args:
            model_id (str): Modelio identifikatorius
            checkpoint_dir (str): Bazinis katalogo kelias išsaugojimams
            
        Returns:
            str: Kelias į checkpoint katalogą
        """
        # Sukuriame unikalų katalogo kelią modeliui
        model_checkpoint_dir = os.path.join(checkpoint_dir, model_id)
        
        # Sukuriame katalogą, jei jo nėra
        if not os.path.exists(model_checkpoint_dir):
            os.makedirs(model_checkpoint_dir, exist_ok=True)
            
        return model_checkpoint_dir
        
    def get_checkpoint_filename(self, epoch, val_loss=None, model_id=None):
        """
        Sugeneruoja tarpinio modelio failo pavadinimą
        
        Args:
            epoch (int): Epochos numeris
            val_loss (float, optional): Validavimo nuostolis
            model_id (str, optional): Modelio identifikatorius
            
        Returns:
            str: Tarpinio modelio failo pavadinimas
        """
        # Gauname dabartinę datą ir laiką
        date_str = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Sukuriame failo pavadinimą
        if val_loss is not None:
            filename = f"checkpoint_epoch_{epoch:03d}_valloss_{val_loss:.4f}_{date_str}.h5"
        else:
            filename = f"checkpoint_epoch_{epoch:03d}_{date_str}.h5"
            
        return filename
    
    def should_save_checkpoint(self, epoch):
        """
        Patikrina, ar šioje epochoje reikia išsaugoti tarpinį modelį
        
        Args:
            epoch (int): Dabartinė epocha
            
        Returns:
            bool: Ar reikia išsaugoti
        """
        if not self.enable_checkpoints:
            return False
            
        # Tikriname, ar epocha yra dali iš išsaugojimo dažnio
        # Pradedame nuo 1, ne nuo 0, kad būtų intuityviau
        # Pvz., jei save_frequency=5, tada išsaugojimas vykdomas epochose 5, 10, 15, ...
        return (epoch % self.save_frequency == 0) or (epoch == 1)