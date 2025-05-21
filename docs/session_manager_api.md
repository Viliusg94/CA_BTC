# Sesijos valdymo serviso API dokumentacija

## Įvadas

Sesijos valdymo servisas (`SessionManagerService`) suteikia aukšto lygio sąsają darbui su naudotojų sesijomis. Servisas leidžia lengvai kurti, atnaujinti ir užbaigti skirtingų tipų sesijas (treniravimo, testavimo, bendros).

## Inicializavimas

```python
from sqlalchemy.orm import Session
from services.session_manager_service import SessionManagerService


Metodai
1. Sesijos pradėjimas
Metodas: start_session

Pradeda naują naudotojo sesiją nurodyto tipo.

Parametrai:
user_id (str): Naudotojo ID
session_type (str): Sesijos tipas (training, testing arba general)
metadata (dict, optional): Papildomi sesijos duomenys
Grąžina:
dict: Sukurtos sesijos informacija arba None, jei įvyko klaida

# Inicializuojame servisą
session_manager = SessionManagerService(db_session)
```

# Pradedame treniravimo sesiją

training_metadata = {
"model_id": "modelio-id",
"dataset_name": "bitcoin_2020_2022",
"total_epochs": 100,
"learning_rate": 0.001
}

result = session_manager.start_session(
user_id="naudotojo-id",
session_type="training",
metadata=training_metadata
)

if result:
training_session_id = result["user_session"]["id"]
print(f"Pradėta treniravimo sesija: {training_session_id}")

2. Sesijos atnaujinimas
   Metodas: update_session

Atnaujina esamą sesiją.

Parametrai:
session_id (str): Naudotojo sesijos ID
update_data (dict): Duomenys, kuriuos reikia atnaujinti
Grąžina:
dict: Atnaujintos sesijos informacija arba None, jei įvyko klaida
Pavyzdys:

# Atnaujiname treniravimo progresą

update_data = {
"current_epoch": 42,
"training_status": "running",
"metadata": {"loss": 0.05, "accuracy": 0.92}
}

result = session_manager.update_session(
session_id="sesijos-id",
update_data=update_data
)

if result:
print(f"Sesija atnaujinta: {result['user_session']['status']}")

3. Sesijos užbaigimas
   Metodas: end_session

Baigia naudotojo sesiją.

Parametrai:
session_id (str): Naudotojo sesijos ID
success (bool, default=True): Ar sesija baigta sėkmingai
results (dict, optional): Sesijos rezultatai (jei yra)
Grąžina:
dict: Baigtos sesijos informacija arba None, jei įvyko klaida
Pavyzdys:

# Baigiame testavimo sesiją su rezultatais

test_results = {
"accuracy": 0.89,
"mae": 245.6,
"rmse": 312.3,
"prediction_time_ms": 120.5
}

result = session_manager.end_session(
session_id="sesijos-id",
success=True,
results=test_results
)

if result:
print(f"Sesija baigta: {result['user_session']['status']}")

4. Sesijos informacijos gavimas
   Metodas: get_session_info

Gauna išsamią informaciją apie sesiją.

Parametrai:
session_id (str): Naudotojo sesijos ID
Grąžina:
dict: Sesijos informacija arba None, jei įvyko klaida
Pavyzdys:

# Gauname sesijos informaciją

session_info = session_manager.get_session_info("sesijos-id")

if session_info:
print(f"Sesijos tipas: {session_info['user_session']['type']}")
print(f"Sesijos būsena: {session_info['user_session']['status']}")
if 'training_session' in session_info:
print(f"Treniravimo progresas: {session_info['training_session']['current_epoch']}/{session_info['training_session']['total_epochs']}")

5. Naudotojo sesijų sąrašo gavimas
   Metodas: list_user_sessions

Gauna naudotojo sesijų sąrašą.

Parametrai:
user_id (str): Naudotojo ID
session_type (str, optional): Filtravimas pagal sesijos tipą
active_only (bool, default=False): Ar grąžinti tik aktyvias sesijas
limit (int, default=100): Maksimalus grąžinamų sesijų skaičius
offset (int, default=0): Kiek sesijų praleisti (puslapis)
Grąžina:
dict: Sesijų sąrašas arba None, jei įvyko klaida
Pavyzdys:

# Gauname aktyvias naudotojo treniravimo sesijas

sessions = session_manager.list_user_sessions(
user_id="naudotojo-id",
session_type="training",
active_only=True
)

if sessions:
print(f"Aktyvių treniravimo sesijų skaičius: {sessions['total']}")
for session in sessions['items']:
print(f"Sesija {session['id']}: {session['status']}")

Sesijų tipai
Servisas palaiko šiuos sesijų tipus:

training - Modelių treniravimo sesijos

Turi papildomus parametrus: model_id, dataset_name, total_epochs, learning_rate, kt.
Gali sekti progresą per current_epoch parametrą
testing - Modelių testavimo sesijos

Turi papildomus parametrus: model_id, dataset_name, test_type, test_params
Gali saugoti testavimo rezultatus results lauke
general - Bendros naudotojo sesijos

Paprastos sesijos be specifinių papildomų laukų
Naudojamos bendram prisijungimui ar kitoms veikloms
Būsenos (Status)
Sesijos gali turėti šias būsenas:

active - Aktyvi sesija
completed - Sėkmingai baigta sesija
failed - Nesėkmingai baigta sesija
expired - Pasibaigusi sesija (pvz., dėl neveiklumo)
Skirtingi sesijų tipai turi savo specifines būsenas:

Treniravimo sesijos: pending, running, completed, failed, stopped
Testavimo sesijos: pending, running, completed, failed
Klaidų apdorojimas
Visi serviso metodai grąžina None klaidos atveju. Rekomenduojama visada tikrinti grąžinamą reikšmę ir apdoroti klaidas:

result = session_manager.start_session(user_id, "training", metadata)
if result is None: # Įvyko klaida pradedant sesiją
print("Nepavyko pradėti sesijos") # Apdorojame klaidą...
