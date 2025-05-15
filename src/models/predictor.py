import pandas as pd
import numpy as np
import os
import joblib
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.ensemble import RandomForestRegressor

def prepare_data_for_ml(df, target_column='Close', forecast_horizon=1, test_size=0.2):
    """
    Paruošia duomenis mašininio mokymosi modeliams
    
    Parameters:
    -----------
    df : pandas.DataFrame
        Apdorotas duomenų rinkinys su indikatoriais
    target_column : str
        Stulpelis, kurį bandysime prognozuoti
    forecast_horizon : int
        Kiek periodų į priekį prognozuoti
    test_size : float
        Testavimo imties dydis (0-1)
        
    Returns:
    --------
    tuple
        X_train, X_test, y_train, y_test, feature_names, scaler
    """
    print(f"Ruošiami duomenys mašininiam mokymuisi, prognozavimo horizontas: {forecast_horizon}")
    
    # Nukopijuojame duomenų rinkinį
    data = df.copy()
    
    # Sukuriame prognozuojamą stulpelį (target)
    data[f'Target_{forecast_horizon}'] = data[target_column].shift(-forecast_horizon)
    
    # Pašaliname eilutes su NaN reikšmėmis
    data = data.dropna()
    
    # Pasirenkame požymius (features)
    # Pašaliname stulpelius, kurie gali sukelti duomenų nutekėjimą
    features = data.drop([f'Target_{forecast_horizon}'], axis=1)
    target = data[f'Target_{forecast_horizon}']
    
    # Išsaugome požymių pavadinimus
    feature_names = features.columns.tolist()
    
    # Padalijame duomenis į mokymosi ir testavimo rinkinius
    X_train, X_test, y_train, y_test = train_test_split(
        features, target, test_size=test_size, shuffle=False
    )
    
    # Normalizuojame duomenis
    scaler = MinMaxScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    print(f"Mokymosi rinkinys: {X_train_scaled.shape}, Testavimo rinkinys: {X_test_scaled.shape}")
    
    return X_train_scaled, X_test_scaled, y_train, y_test, feature_names, scaler

def train_model(X_train, y_train, model_type='random_forest', params=None):
    """
    Apmoko mašininio mokymosi modelį
    
    Parameters:
    -----------
    X_train : numpy.ndarray
        Mokymosi duomenų rinkinys (požymiai)
    y_train : numpy.ndarray
        Mokymosi duomenų rinkinys (tikslas)
    model_type : str
        Modelio tipas ('random_forest' arba kiti ateityje)
    params : dict
        Modelio hiperparametrai
        
    Returns:
    --------
    object
        Apmokytas modelis
    """
    print(f"Apmokomas modelis: {model_type}")
    
    if model_type == 'random_forest':
        # Numatytieji parametrai, jei nepateikti
        if params is None:
            params = {
                'n_estimators': 100,
                'max_depth': None,
                'min_samples_split': 2,
                'min_samples_leaf': 1,
                'random_state': 42
            }
        
        model = RandomForestRegressor(**params)
    else:
        raise ValueError(f"Nežinomas modelio tipas: {model_type}")
    
    # Apmokome modelį
    model.fit(X_train, y_train)
    print("Modelis sėkmingai apmokytas!")
    
    return model

def evaluate_model(model, X_test, y_test, feature_names=None):
    """
    Įvertina modelio tikslumą
    
    Parameters:
    -----------
    model : object
        Apmokytas modelis
    X_test : numpy.ndarray
        Testavimo duomenų rinkinys (požymiai)
    y_test : numpy.ndarray
        Testavimo duomenų rinkinys (tikslas)
    feature_names : list
        Požymių pavadinimai
        
    Returns:
    --------
    dict
        Įvertinimo metrikos
    """
    print("Vertinamas modelio tikslumas...")
    
    # Prognozuojame testiniam rinkiniui
    y_pred = model.predict(X_test)
    
    # Apskaičiuojame metrikas
    metrics = {
        'MSE': mean_squared_error(y_test, y_pred),
        'RMSE': np.sqrt(mean_squared_error(y_test, y_pred)),
        'MAE': mean_absolute_error(y_test, y_pred),
        'R2': r2_score(y_test, y_pred)
    }
    
    # Išvedame rezultatus
    print(f"Modelio įvertinimo metrikos:")
    for metric_name, metric_value in metrics.items():
        print(f"{metric_name}: {metric_value:.4f}")
    
    # Jei turime požymių pavadinimus ir modelis palaiko feature_importance
    if feature_names and hasattr(model, 'feature_importances_'):
        # Rikiuojame požymius pagal svarbą
        importances = model.feature_importances_
        indices = np.argsort(importances)[::-1]
        
        print("\nPožymių svarba:")
        for i in range(min(10, len(feature_names))):  # Rodome top 10
            print(f"{feature_names[indices[i]]}: {importances[indices[i]]:.4f}")
    
    return metrics

def save_model(model, scaler, output_dir="data/models", model_name="btc_predictor"):
    """
    Išsaugo apmokytą modelį ir normalizavimo parametrus
    
    Parameters:
    -----------
    model : object
        Apmokytas modelis
    scaler : object
        Požymių normalizavimo objektas
    output_dir : str
        Direktorija, kur išsaugoti modelį
    model_name : str
        Modelio pavadinimas
    """
    # Sukuriame direktoriją, jei jos nėra
    os.makedirs(output_dir, exist_ok=True)
    
    # Išsaugome modelį
    model_path = os.path.join(output_dir, f"{model_name}.joblib")
    joblib.dump(model, model_path)
    
    # Išsaugome normalizavimo parametrus
    scaler_path = os.path.join(output_dir, f"{model_name}_scaler.joblib")
    joblib.dump(scaler, scaler_path)
    
    print(f"Modelis išsaugotas: {model_path}")
    print(f"Normalizavimo parametrai išsaugoti: {scaler_path}")

def predict_next_periods(model, scaler, last_data, feature_names, periods=1):
    """
    Prognozuoja ateinančius periodus
    
    Parameters:
    -----------
    model : object
        Apmokytas modelis
    scaler : object
        Požymių normalizavimo objektas
    last_data : pandas.DataFrame
        Paskutiniai žinomi duomenys
    feature_names : list
        Požymių pavadinimai
    periods : int
        Kiek periodų į priekį prognozuoti
        
    Returns:
    --------
    list
        Prognozuojamos reikšmės
    """
    # Patikriname, ar turime visus reikiamus požymius
    if not all(feature in last_data.columns for feature in feature_names):
        missing = [f for f in feature_names if f not in last_data.columns]
        raise ValueError(f"Trūksta požymių: {missing}")
    
    # Pasiimame tik tuos stulpelius, kuriuos naudojome mokyme
    last_known = last_data[feature_names].iloc[-1:].values
    
    # Normalizuojame duomenis
    last_known_scaled = scaler.transform(last_known)
    
    # Prognozuojame
    prediction = model.predict(last_known_scaled)[0]
    
    return prediction

def train_and_save_model(data_path="data/processed/btc_features.csv", 
                         output_dir="data/models", 
                         forecast_horizon=1,
                         model_type='random_forest',
                         model_params=None):
    """
    Apmoko ir išsaugo modelį
    
    Parameters:
    -----------
    data_path : str
        Kelias iki apdorotų duomenų failo
    output_dir : str
        Direktorija, kur išsaugoti modelį
    forecast_horizon : int
        Kiek periodų į priekį prognozuoti
    model_type : str
        Modelio tipas
    model_params : dict
        Modelio hiperparametrai
    
    Returns:
    --------
    tuple
        model, metrics
    """
    # Tikriname, ar egzistuoja duomenų failas
    if not os.path.exists(data_path):
        print(f"Klaida: nerastas duomenų failas {data_path}")
        return None, None
    
    # Įkeliame apdorotus duomenis
    data = pd.read_csv(data_path, index_col=0, parse_dates=True)
    
    # Paruošiame duomenis
    X_train, X_test, y_train, y_test, feature_names, scaler = prepare_data_for_ml(
        data, forecast_horizon=forecast_horizon
    )
    
    # Apmokome modelį
    model = train_model(X_train, y_train, model_type=model_type, params=model_params)
    
    # Įvertiname modelį
    metrics = evaluate_model(model, X_test, y_test, feature_names)
    
    # Išsaugome modelį
    save_model(model, scaler, output_dir=output_dir, 
              model_name=f"btc_predictor_h{forecast_horizon}")
    
    return model, metrics

if __name__ == "__main__":
    # Pavyzdinis paleidimas
    model, metrics = train_and_save_model()
    
    if model is not None:
        print("Modelio apmokymas sėkmingai baigtas!")