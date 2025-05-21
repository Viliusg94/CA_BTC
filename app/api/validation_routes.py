from flask import Blueprint, jsonify, request, current_app
from app.services.model_service import ModelService
from app.services.evaluation_service import get_model_validation_data

# Inicializuojame API maršrutus
api_validation = Blueprint('api_validation', __name__)

@api_validation.route('/api/model/<model_id>/validation-data', methods=['GET'])
def get_validation_data(model_id):
    """
    Grąžina modelio validavimo duomenis
    
    Args:
        model_id (str): Modelio ID
        
    Returns:
        dict: Validavimo duomenys JSON formatu
    """
    try:
        model_service = ModelService()
        # Gauname modelį pagal ID
        model = model_service.get_model_config(model_id)
        
        if not model:
            return jsonify({'error': 'Modelis nerastas'}), 404
        
        # Gauname validavimo duomenis
        validation_data = get_model_validation_data(model)
        
        # Grąžiname duomenis
        return jsonify(validation_data)
    
    except Exception as e:
        current_app.logger.error(f"Klaida gaunant validavimo duomenis: {str(e)}")
        return jsonify({'error': 'Įvyko klaida gaunant validavimo duomenis', 'details': str(e)}), 500