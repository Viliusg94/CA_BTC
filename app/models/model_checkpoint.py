import json
import os
import datetime
import uuid
from pathlib import Path
import numpy as np

class ModelCheckpoint:
    """
    Modelio tarpinio išsaugojimo (checkpoint) duomenų modelis.
    Leidžia išsaugoti ir atkurti modelio būseną iš tam tikro apmokymo taško.
    """
    
    def __init__(self, model_id=None, epoch=0, metrics=None, parameters=None):
        """
        Inicializuoja naują modelio išsaugojimą (checkpoint)
        
        Args:
            model_id (str): Modelio, kuriam priklauso išsaugojimas, ID
            epoch (int): Epochos numeris, kurioje buvo sukurtas išsaugojimas
            metrics (dict): Modelio metrikos išsaugojimo metu (loss, accuracy, etc.)
            parameters (dict): Modelio parametrai išsaugojimo metu
        """
        # Generuojame unikalų išsaugojimo ID
        self.checkpoint_id = str(uuid.uuid4())
        
        # Pagrindinė informacija
        self.model_id = model_id
        self.epoch = epoch
        self.metrics = metrics or {}
        self.parameters = parameters or {}
        
        # Būsenos informacija
        self.is_best = False  # Ar tai geriausias išsaugojimas
        self.status = "created"  # created, saved, restored, error
        self.weights_path = None  # Kelias iki svorių failo
        
        # Laiko žymės
        self.created_at = datetime.datetime.now()
        self.updated_at = datetime.datetime.now()
        
        # Pastabos ar komentarai
        self.notes = ""
    
    def to_dict(self):
        """
        Konvertuoja išsaugojimą į žodyną
        
        Returns:
            dict: Išsaugojimo duomenys
        """
        return {
            "checkpoint_id": self.checkpoint_id,
            "model_id": self.model_id,
            "epoch": self.epoch,
            "metrics": self.metrics,
            "parameters": self.parameters,
            "is_best": self.is_best,
            "status": self.status,
            "weights_path": self.weights_path,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "notes": self.notes
        }
    
    @classmethod
    def from_dict(cls, data):
        """
        Sukuria išsaugojimą iš žodyno
        
        Args:
            data (dict): Išsaugojimo duomenys
            
        Returns:
            ModelCheckpoint: Išsaugojimo objektas
        """
        checkpoint = cls()
        
        # Pagrindiniai laukai
        checkpoint.checkpoint_id = data.get("checkpoint_id", str(uuid.uuid4()))
        checkpoint.model_id = data.get("model_id")
        checkpoint.epoch = data.get("epoch", 0)
        checkpoint.metrics = data.get("metrics", {})
        checkpoint.parameters = data.get("parameters", {})
        
        # Būsenos laukai
        checkpoint.is_best = data.get("is_best", False)
        checkpoint.status = data.get("status", "created")
        checkpoint.weights_path = data.get("weights_path")
        checkpoint.notes = data.get("notes", "")
        
        # Laiko žymės
        try:
            checkpoint.created_at = datetime.datetime.fromisoformat(data.get("created_at"))
        except (TypeError, ValueError):
            checkpoint.created_at = datetime.datetime.now()
            
        try:
            checkpoint.updated_at = datetime.datetime.fromisoformat(data.get("updated_at"))
        except (TypeError, ValueError):
            checkpoint.updated_at = datetime.datetime.now()
        
        return checkpoint
    
    def mark_as_best(self):
        """
        Pažymi šį išsaugojimą kaip geriausią
        """
        self.is_best = True
        self.updated_at = datetime.datetime.now()
    
    def update_metrics(self, metrics):
        """
        Atnaujina išsaugojimo metrikas
        
        Args:
            metrics (dict): Naujos metrikos
        """
        self.metrics.update(metrics)
        self.updated_at = datetime.datetime.now()
    
    def add_note(self, note):
        """
        Prideda pastabą prie išsaugojimo
        
        Args:
            note (str): Pastaba
        """
        if self.notes:
            self.notes += f"\n{note}"
        else:
            self.notes = note
        self.updated_at = datetime.datetime.now()
    
    def save(self, base_dir="data/checkpoints", save_weights=True, weights_data=None):
        """
        Išsaugo išsaugojimo metaduomenis į failą
        
        Args:
            base_dir (str): Katalogas, kuriame saugomi išsaugojimai
            save_weights (bool): Ar išsaugoti modelio svorius
            weights_data (object): Modelio svorių duomenys (numpy masyvas arba kitoks formatas)
            
        Returns:
            bool: Ar išsaugojimas pavyko
        """
        try:
            # Sukuriame katalogą, jei jo nėra
            checkpoint_dir = Path(base_dir) / self.model_id
            checkpoint_dir.mkdir(parents=True, exist_ok=True)
            
            # Išsaugome modelio svorius, jei reikalaujama
            if save_weights and weights_data is not None:
                weights_filename = f"{self.checkpoint_id}_weights.npz"
                weights_path = checkpoint_dir / weights_filename
                
                # Išsaugome svorius
                if isinstance(weights_data, dict):
                    np.savez(weights_path, **weights_data)
                elif isinstance(weights_data, (list, np.ndarray)):
                    np.savez(weights_path, weights=weights_data)
                else:
                    # Jei nežinome formato, bandome išsaugoti kaip bendrą objektą
                    np.savez(weights_path, data=weights_data)
                
                # Atnaujiname kelią iki svorių failo
                self.weights_path = str(weights_path)
            
            # Atnaujiname būseną
            self.status = "saved"
            self.updated_at = datetime.datetime.now()
            
            # Išsaugome metaduomenis į JSON failą
            metadata_filename = f"{self.checkpoint_id}.json"
            metadata_path = checkpoint_dir / metadata_filename
            
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(self.to_dict(), f, ensure_ascii=False, indent=4)
            
            return True
        
        except Exception as e:
            # Išsaugojimas nepavyko
            self.status = "error"
            self.add_note(f"Išsaugojimo klaida: {str(e)}")
            return False
    
    @classmethod
    def load(cls, checkpoint_id, model_id=None, base_dir="data/checkpoints"):
        """
        Užkrauna išsaugojimo metaduomenis iš failo
        
        Args:
            checkpoint_id (str): Išsaugojimo ID
            model_id (str, optional): Modelio ID. Reikalingas, jei ieškoma kataloge
            base_dir (str): Katalogas, kuriame saugomi išsaugojimai
            
        Returns:
            ModelCheckpoint: Išsaugojimo objektas arba None, jei nepavyko užkrauti
        """
        try:
            # Jei žinome modelio ID, ieškome tik jo kataloge
            if model_id:
                metadata_path = Path(base_dir) / model_id / f"{checkpoint_id}.json"
                if not metadata_path.exists():
                    return None
                
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                return cls.from_dict(data)
            
            # Jei nežinome modelio ID, ieškome visuose kataloguose
            else:
                # Gauname visus modelių katalogus
                checkpoints_dir = Path(base_dir)
                if not checkpoints_dir.exists():
                    return None
                
                # Einame per visus katalogus
                for model_dir in checkpoints_dir.iterdir():
                    if not model_dir.is_dir():
                        continue
                    
                    # Tikriname, ar yra ieškomos išsaugojimo failo
                    metadata_path = model_dir / f"{checkpoint_id}.json"
                    if metadata_path.exists():
                        with open(metadata_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        return cls.from_dict(data)
                
                # Neradome išsaugojimo
                return None
        
        except Exception as e:
            print(f"Klaida užkraunant išsaugojimą: {str(e)}")
            return None
    
    def load_weights(self):
        """
        Užkrauna išsaugotus modelio svorius
        
        Returns:
            object: Modelio svorių duomenys arba None, jei nepavyko užkrauti
        """
        try:
            # Tikriname, ar turime kelią iki svorių failo
            if not self.weights_path:
                return None
            
            # Užkrauname svorius
            weights_path = Path(self.weights_path)
            if not weights_path.exists():
                return None
            
            # Nuskaitome npz failą
            with np.load(weights_path, allow_pickle=True) as data:
                # Grąžiname žodyną su visais masyvais
                return {key: data[key] for key in data.files}
        
        except Exception as e:
            print(f"Klaida užkraunant svorius: {str(e)}")
            return None
    
    @classmethod
    def list_all_for_model(cls, model_id, base_dir="data/checkpoints", sort_by="epoch"):
        """
        Grąžina visus modelio išsaugojimus
        
        Args:
            model_id (str): Modelio ID
            base_dir (str): Katalogas, kuriame saugomi išsaugojimai
            sort_by (str): Rūšiavimo kriterijus (epoch, created_at)
            
        Returns:
            list: Išsaugojimų sąrašas
        """
        checkpoints = []
        
        try:
            # Tikriname, ar yra modelio katalogas
            model_dir = Path(base_dir) / model_id
            if not model_dir.exists():
                return []
            
            # Einame per visus JSON failus kataloge
            for metadata_path in model_dir.glob("*.json"):
                # Ignoruojame ne-JSON failus
                if not metadata_path.name.endswith(".json"):
                    continue
                
                # Užkrauname išsaugojimą
                try:
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    checkpoint = cls.from_dict(data)
                    checkpoints.append(checkpoint)
                except Exception as e:
                    print(f"Klaida užkraunant išsaugojimą {metadata_path}: {str(e)}")
            
            # Rūšiuojame išsaugojimus
            if sort_by == "epoch":
                checkpoints.sort(key=lambda x: x.epoch)
            elif sort_by == "created_at":
                checkpoints.sort(key=lambda x: x.created_at)
            
            return checkpoints
        
        except Exception as e:
            print(f"Klaida gaunant išsaugojimų sąrašą: {str(e)}")
            return []
    
    def delete(self, base_dir="data/checkpoints"):
        """
        Ištrina išsaugojimo failus
        
        Args:
            base_dir (str): Katalogas, kuriame saugomi išsaugojimai
            
        Returns:
            bool: Ar ištrynimas pavyko
        """
        try:
            # Tikriname, ar turime modelio ID
            if not self.model_id:
                return False
            
            # Gauname kelią iki metaduomenų failo
            metadata_path = Path(base_dir) / self.model_id / f"{self.checkpoint_id}.json"
            
            # Ištriname metaduomenų failą, jei jis egzistuoja
            if metadata_path.exists():
                metadata_path.unlink()
            
            # Ištriname svorių failą, jei jis egzistuoja
            if self.weights_path:
                weights_path = Path(self.weights_path)
                if weights_path.exists():
                    weights_path.unlink()
            
            return True
        
        except Exception as e:
            print(f"Klaida trinant išsaugojimą: {str(e)}")
            return False