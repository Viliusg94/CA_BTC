from app.models.model_metrics import ModelMetrics

def add_sample_models():
    """
    Prideda pavyzdinius modelius testavimui
    """
    # Sukuriame ModelMetrics objektą
    metrics = ModelMetrics()
    
    # Patikriname, ar jau turime duomenų
    models = metrics.get_all_models()
    if len(models) > 0:
        # Jei jau yra modelių, nebekuriame naujų
        return
    
    # Pridedame keletą pavyzdinių modelių
    
    # LSTM modelis
    metrics.save_metrics(
        model_name="LSTM_BTC_v1", 
        accuracy=0.85, 
        loss=0.23, 
        val_accuracy=0.82, 
        val_loss=0.25, 
        epochs=50,
        description="LSTM modelis Bitcoin kainų prognozavimui, 2 sluoksniai"
    )
    
    # GRU modelis
    metrics.save_metrics(
        model_name="GRU_BTC_v1", 
        accuracy=0.87, 
        loss=0.20, 
        val_accuracy=0.84, 
        val_loss=0.22, 
        epochs=50,
        description="GRU modelis su dropout=0.2, optimizuotas Bitcoin kainoms"
    )
    
    # Dense modelis
    metrics.save_metrics(
        model_name="Dense_NN_v1", 
        accuracy=0.78, 
        loss=0.35, 
        val_accuracy=0.75, 
        val_loss=0.38, 
        epochs=30,
        description="Paprastas Dense neural network modelis"
    )
    
    # CNN modelis
    metrics.save_metrics(
        model_name="CNN_BTC_v1", 
        accuracy=0.82, 
        loss=0.28, 
        val_accuracy=0.79, 
        val_loss=0.31, 
        epochs=40,
        description="1D CNN modelis su 3 sluoksniais"
    )
    
    # Patobulinta LSTM versija
    metrics.save_metrics(
        model_name="LSTM_BTC_v2", 
        accuracy=0.88, 
        loss=0.19, 
        val_accuracy=0.84, 
        val_loss=0.21, 
        epochs=70,
        description="Patobulinta LSTM versija su daugiau epochų"
    )