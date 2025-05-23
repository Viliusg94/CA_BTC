def get_model_predictions():
    predictions = {}
    try:
        # Gather predictions from different models
        for model_name, model in models.items():
            # Assuming model predictions are returned as dictionaries
            prediction_result = model.predict()
            
            # Store prediction properly - ensuring it's a dict or simple value
            if isinstance(prediction_result, dict):
                # Jau yra žodynas, naudojame jį tiesiogiai
                predictions[model_name] = prediction_result
            else:
                # Konvertuojame į žodyną su value raktu
                predictions[model_name] = {'value': prediction_result}
            
    except Exception as e:
        logging.error(f"Klaida gaunant prognozes: {str(e)}")
    
    # Grąžiname formatą, kurį šablonas galės saugiai naudoti
    return predictions

# The function that uses these predictions should access them properly:
def process_predictions(predictions):
    results = {}
    for model_name, prediction in predictions.items():
        # Check if prediction is a dictionary and access value by key
        if isinstance(prediction, dict) and 'value' in prediction:
            results[model_name] = prediction['value']
        else:
            # Handle the case where prediction is not a dictionary
            results[model_name] = prediction
    
    return results