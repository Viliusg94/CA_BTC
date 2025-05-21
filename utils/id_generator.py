"""
ID generavimo utilitas.
Pateikia funkcijas unikalių ID generavimui ir validavimui.
"""
import uuid
import logging
import time
import random
import hashlib
from typing import Optional, Callable
from sqlalchemy.orm import Session

# Sukonfigūruojame logerį
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_uuid() -> str:
    """
    Generuoja standartinį UUID v4 ID.
    
    Returns:
        str: Sugeneruotas UUID v4 kaip tekstinė eilutė
    """
    return str(uuid.uuid4())

def generate_simple_id(prefix: str = "", length: int = 10) -> str:
    """
    Generuoja paprastą skaitinį-raidinį ID su pasirenkamu prefiksu.
    
    Args:
        prefix: ID prefiksas (pvz., "USR", "TST")
        length: ID ilgis be prefikso
        
    Returns:
        str: Sugeneruotas ID
    """
    # Leistini simboliai ID (didžiosios, mažosios raidės ir skaičiai)
    allowed_chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    
    # Generuojame atsitiktinį ID
    random_part = ''.join(random.choice(allowed_chars) for _ in range(length))
    
    # Pridedame laiko žymą, kad būtų didesnis unikalumas
    timestamp = int(time.time())
    
    # Sukuriame ID
    if prefix:
        return f"{prefix}_{timestamp}_{random_part}"
    else:
        return f"{timestamp}_{random_part}"

def generate_hash_id(prefix: str = "", salt: str = "") -> str:
    """
    Generuoja ID paremtą hash funkcija.
    
    Args:
        prefix: ID prefiksas (pvz., "USR", "TST")
        salt: Papildoma eilutė unikalumui užtikrinti
        
    Returns:
        str: Sugeneruotas ID
    """
    # Naudojame dabartinį laiką, atsitiktinį skaičių ir salt kaip seed
    seed = f"{time.time()}_{random.randint(1, 1000000)}_{salt}"
    
    # Generuojame hash naudojant SHA-256
    hash_obj = hashlib.sha256(seed.encode())
    hash_hex = hash_obj.hexdigest()
    
    # Sukuriame ID
    if prefix:
        return f"{prefix}_{hash_hex[:32]}"
    else:
        return hash_hex[:32]

def generate_session_id(session_type: str = "general") -> str:
    """
    Generuoja ID naudotojo sesijai.
    
    Args:
        session_type: Sesijos tipas (training/testing/general)
        
    Returns:
        str: Sugeneruotas sesijos ID
    """
    # Nustatome prefiksą pagal sesijos tipą
    if session_type == "training":
        prefix = "TRN"
    elif session_type == "testing":
        prefix = "TST"
    else:
        prefix = "SES"
    
    # Generuojame ID
    return generate_hash_id(prefix)

def ensure_unique_id(session: Session, model_class, id_generator: Callable = generate_uuid, max_attempts: int = 5, **kwargs) -> Optional[str]:
    """
    Generuoja unikalų ID ir patikrina, ar jis jau egzistuoja duomenų bazėje.
    Jei ID jau egzistuoja, bando dar kartą (iki max_attempts kartų).
    
    Args:
        session: SQLAlchemy sesijos objektas
        model_class: Modelio klasė, kurioje tikrinsime ID (pvz., User, UserSession)
        id_generator: Funkcija, generuojanti ID
        max_attempts: Maksimalus bandymų skaičius
        **kwargs: Papildomi argumentai perduodami ID generatoriui
        
    Returns:
        str: Sugeneruotas unikalus ID arba None, jei nepavyko
    """
    attempts = 0
    
    while attempts < max_attempts:
        # Generuojame ID
        new_id = id_generator(**kwargs)
        
        # Tikriname, ar ID jau egzistuoja duomenų bazėje
        exists = session.query(model_class).filter(model_class.id == new_id).first() is not None
        
        if not exists:
            # ID unikalus, grąžiname jį
            return new_id
        
        # ID jau egzistuoja, bandome dar kartą
        attempts += 1
        logger.warning(f"ID {new_id} jau egzistuoja. Bandymas {attempts}/{max_attempts}")
    
    # Nepavyko sugeneruoti unikalaus ID
    logger.error(f"Nepavyko sugeneruoti unikalaus ID po {max_attempts} bandymų")
    return None