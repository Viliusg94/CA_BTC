import json
import numpy as np
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)

def serialize_for_template(data):
    """
    Serialize data for use in templates, handling numpy arrays and datetime objects
    """
    def json_serializer(obj):
        """JSON serializer for objects not serializable by default json code"""
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif hasattr(obj, 'to_dict'):
            return obj.to_dict()
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        return str(obj)
    
    try:
        return json.dumps(data, default=json_serializer, ensure_ascii=False)
    except (TypeError, ValueError) as e:
        logger.error(f"JSON serialization error: {e}")
        return json.dumps({})

def safe_json_loads(json_string):
    """
    Safely load JSON string with error handling
    """
    try:
        return json.loads(json_string)
    except (json.JSONDecodeError, TypeError):
        return {}