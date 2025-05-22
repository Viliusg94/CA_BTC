import os
import shutil
import json
from datetime import datetime

# Šaltinio ir tikslo aplankų keliai
source_dir = 'd:/CA_BTC/models'  # Jūsų esamas aplankas su modeliais
target_base_dir = 'd:/CA_BTC/app/models'  # Tikslo aplankas pagal aplikacijos struktūrą

# Mapping dictionary - kokius modelius ieškome ir kur juos dėti
model_mapping = {
    'lstm': {
        'target_id': '9',
        'patterns': ['lstm', 'LSTM'],  # Modelio failo pavadinimo šablonai
        'scaler_patterns': ['lstm_scaler', 'lstm.*scaler', 'scaler.*lstm']  # Skalerio failo pavadinimo šablonai
    },
    'gru': {
        'target_id': '1',
        'patterns': ['gru', 'GRU'],
        'scaler_patterns': ['gru_scaler', 'gru.*scaler', 'scaler.*gru']
    },
    'transformer': {
        'target_id': '2',
        'patterns': ['transformer', 'Transformer', 'trans'],
        'scaler_patterns': ['transformer_scaler', 'transformer.*scaler', 'scaler.*transformer', 'trans.*scaler']
    }
}

# Gaukime visus failus šaltinio aplanke
if not os.path.exists(source_dir):
    print(f"KLAIDA: Šaltinio aplankas {source_dir} neegzistuoja!")
else:
    files = os.listdir(source_dir)
    print(f"Rasta {len(files)} failų aplanke {source_dir}")

    # Sukurkime tikslo aplankus
    for model_type in model_mapping.keys():
        target_dir = os.path.join(target_base_dir, model_type)
        os.makedirs(target_dir, exist_ok=True)
        print(f"Sukurtas aplankas: {target_dir}")

    # Ieškokime ir kopijuokime modelių failus
    copied_models = []
    for model_type, mapping in model_mapping.items():
        # Ieškome modelio failo
        model_found = False
        for file in files:
            # Tikriname, ar failas atitinka bet kurį modelio šabloną
            if any(pattern.lower() in file.lower() for pattern in mapping['patterns']) and file.endswith('.h5'):
                # Nukopijuokime modelį
                source_path = os.path.join(source_dir, file)
                target_path = os.path.join(target_base_dir, model_type, f"{mapping['target_id']}.h5")
                shutil.copy2(source_path, target_path)
                print(f"Modelis nukopijuotas: {source_path} -> {target_path}")
                model_found = True
                copied_models.append(model_type)
                break
        
        if not model_found:
            print(f"ĮSPĖJIMAS: {model_type} modelio failas nerastas!")
        
        # Ieškome skalerio failo
        scaler_found = False
        for file in files:
            # Tikriname, ar failas atitinka bet kurį skalerio šabloną
            if any(pattern.lower() in file.lower() for pattern in mapping['scaler_patterns']) and file.endswith('.pkl'):
                # Nukopijuokime skalerį
                source_path = os.path.join(source_dir, file)
                target_path = os.path.join(target_base_dir, model_type, f"{mapping['target_id']}_scaler.pkl")
                shutil.copy2(source_path, target_path)
                print(f"Skaleris nukopijuotas: {source_path} -> {target_path}")
                scaler_found = True
                break
        
        if not scaler_found:
            print(f"ĮSPĖJIMAS: {model_type} skalerio failas nerastas!")

    # Sukurkime model_status.json failą
    model_status = {}
    for model_type in model_mapping.keys():
        model_status[model_type] = {
            "status": "Aktyvus" if model_type in copied_models else "Neaktyvus",
            "last_trained": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "performance": f"MAE: {450 + (model_type.count('r') * 20):.1f}",  # Pavyzdinė metrika
            "active_model_id": model_mapping[model_type]['target_id'] if model_type in copied_models else None
        }

    # Išsaugokime JSON failą
    json_path = os.path.join(target_base_dir, 'model_status.json')
    with open(json_path, 'w') as f:
        json.dump(model_status, f, indent=2)
    print(f"model_status.json išsaugotas: {json_path}")

print("Modelių perkėlimas baigtas!")