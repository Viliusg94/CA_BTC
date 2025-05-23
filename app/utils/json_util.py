import json
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)

def serialize_for_template(data):
    """
    Konvertuoja visus duomenis, kad būtų tinkama perduoti į Flask šabloną.
    Sprendžia datetime ir function tipo objektų serializacijos problemas.
    """
    if data is None:
        return None
    
    # Jei yra žodynas, apdorojame kiekvieną reikšmę
    if isinstance(data, dict):
        return {k: serialize_for_template(v) for k, v in data.items()}
    
    # Jei yra sąrašas arba tuple, apdorojame kiekvieną elementą
    if isinstance(data, (list, tuple)):
        return [serialize_for_template(item) for item in data]
    
    # Apdorojame datetime objektus
    if isinstance(data, (datetime, date)):
        return data.isoformat()
    
    # Apdorojame callable objektus (funkcijas ar metodus)
    if callable(data):
        logger.warning(f"Found callable object in template data: {data}")
        return str(data)
    
    # Grąžiname nekeistą reikšmę, jei nebuvo poreikio konvertuoti
    return data