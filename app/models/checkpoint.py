import os
import json
import datetime
import uuid
from pathlib import Path

# Modelio išsaugojimo duomenų klasė

class Checkpoint:
    """
    Modelio išsaugojimo duomenų klasė
    
    Atributai:
        id (str): Išsaugojimo ID
        model_id (str): Modelio ID
        epoch (int): Epocha, kurioje buvo sukurtas išsaugojimas
        timestamp (str): Išsaugojimo sukūrimo laikas
        filepath (str): Kelias iki išsaugojimo failo
        metrics (dict): Metrikos išsaugojimo metu
        is_best (bool): Ar tai geriausias išsaugojimas pagal val_loss
        description (str): Išsaugojimo aprašymas (nebūtinas)
    """
    
    def __init__(self, id, model_id, epoch, timestamp, filepath, metrics=None, is_best=False, description=None):
        """
        Inicializuoja Checkpoint objektą
        
        Args:
            id (str): Išsaugojimo ID
            model_id (str): Modelio ID
            epoch (int): Epocha, kurioje buvo sukurtas išsaugojimas
            timestamp (str): Išsaugojimo sukūrimo laikas
            filepath (str): Kelias iki išsaugojimo failo
            metrics (dict, optional): Metrikos išsaugojimo metu. Numatytoji reikšmė: None
            is_best (bool, optional): Ar tai geriausias išsaugojimas pagal val_loss. Numatytoji reikšmė: False
            description (str, optional): Išsaugojimo aprašymas. Numatytoji reikšmė: None
        """
        self.id = id
        self.model_id = model_id
        self.epoch = epoch
        self.timestamp = timestamp
        self.filepath = filepath
        self.metrics = metrics or {}
        self.is_best = is_best
        self.description = description
        
    def to_dict(self):
        """
        Konvertuoja Checkpoint objektą į žodyną
        
        Returns:
            dict: Išsaugojimo duomenys žodyne
        """
        return {
            'id': self.id,
            'model_id': self.model_id,
            'epoch': self.epoch,
            'timestamp': self.timestamp,
            'filepath': self.filepath,
            'metrics': self.metrics,
            'is_best': self.is_best,
            'description': self.description
        }
    
    @classmethod
    def from_dict(cls, data):
        """
        Sukuria Checkpoint objektą iš žodyno
        
        Args:
            data (dict): Žodynas su išsaugojimo duomenimis
            
        Returns:
            Checkpoint: Sukurtas Checkpoint objektas
        """
        return cls(
            id=data.get('id'),
            model_id=data.get('model_id'),
            epoch=data.get('epoch'),
            timestamp=data.get('timestamp'),
            filepath=data.get('filepath'),
            metrics=data.get('metrics'),
            is_best=data.get('is_best', False),
            description=data.get('description')
        )