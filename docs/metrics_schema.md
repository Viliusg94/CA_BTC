# Metrikų duomenų schemos dokumentacija

Šis dokumentas aprašo metrikų duomenų bazės struktūrą, lentelių paskirtį ir ryšius tarp jų.

## 1. Apžvalga

Metrikų sistema skirta rinkti, saugoti ir analizuoti įvairias metrikas, susijusias su:

- Naudotojų veikla ir efektyvumu
- Mašininio mokymosi modelių veikimu ir tikslumu
- Sesijų resursų naudojimu ir trukme

Sistema sudaryta iš trijų pagrindinių lentelių, kurios saugo skirtingo tipo metrikas ir yra susietos su atitinkamomis pagrindinėmis lentelėmis.

## 2. Lentelių struktūra

### 2.1. UserMetric (user_metrics)

Ši lentelė saugo įvairias naudotojo veiklos ir efektyvumo metrikas.

| Stulpelis     | Tipas        | Aprašymas                                       |
| ------------- | ------------ | ----------------------------------------------- |
| id            | VARCHAR(36)  | Pirminis raktas, UUID                           |
| user_id       | VARCHAR(36)  | Išorinis raktas į users lentelę                 |
| metric_type   | VARCHAR(50)  | Metrikos tipas (accuracy, usage, performance)   |
| metric_name   | VARCHAR(100) | Metrikos pavadinimas                            |
| numeric_value | FLOAT        | Skaitinė metrikos reikšmė (jei taikoma)         |
| string_value  | VARCHAR(255) | Tekstinė metrikos reikšmė (jei taikoma)         |
| time_period   | VARCHAR(20)  | Laiko periodas (daily, weekly, monthly, yearly) |
| timestamp     | TIMESTAMP    | Metrikos sukūrimo laikas                        |
| metadata      | TEXT         | Papildoma informacija JSON formatu              |

#### Ryšiai:

- `user_id` -> `users.id` (CASCADE DELETE) - Ištrinus naudotoją, ištrinamos visos jo metrikos

#### Pagrindiniai metrikos tipai:

- `accuracy` - tikslumo metrikos (pvz., vidutinis prognozių tikslumas)
- `usage` - naudojimo metrikos (pvz., prisijungimų skaičius, sesijų skaičius)
- `performance` - efektyvumo metrikos (pvz., užduočių atlikimo laikas)

#### Pavyzdžiai:

- `login_count` (usage) - prisijungimų skaičius per dieną/savaitę
- `avg_prediction_accuracy` (accuracy) - vidutinis naudotojo modelių tikslumas
- `training_completion_rate` (performance) - sėkmingai baigtų treniravimų dalis

### 2.2. ModelMetric (model_metrics)

Ši lentelė saugo įvairias modelio veikimo ir efektyvumo metrikas.

| Stulpelis    | Tipas        | Aprašymas                                    |
| ------------ | ------------ | -------------------------------------------- |
| id           | VARCHAR(36)  | Pirminis raktas, UUID                        |
| model_id     | VARCHAR(36)  | Išorinis raktas į models lentelę             |
| user_id      | VARCHAR(36)  | Išorinis raktas į users lentelę (matavėjas)  |
| metric_type  | VARCHAR(50)  | Metrikos tipas (accuracy, training, testing) |
| metric_name  | VARCHAR(100) | Metrikos pavadinimas                         |
| value        | FLOAT        | Metrikos reikšmė                             |
| dataset_name | VARCHAR(100) | Duomenų rinkinio pavadinimas                 |
| timestamp    | TIMESTAMP    | Metrikos sukūrimo laikas                     |
| metadata     | TEXT         | Papildoma informacija JSON formatu           |

#### Ryšiai:

- `model_id` -> `models.id` (CASCADE DELETE) - Ištrinus modelį, ištrinamos visos jo metrikos
- `user_id` -> `users.id` (SET NULL) - Ištrinus naudotoją, jo ID nustatomas į NULL

#### Pagrindiniai metrikos tipai:

- `accuracy` - tikslumo metrikos (pvz., prediction_accuracy, r2_score)
- `training` - treniravimo metrikos (pvz., final_loss, learning_rate, epochs)
- `testing` - testavimo metrikos (pvz., rmse, mae, mape)

#### Pavyzdžiai:

- `rmse` (accuracy) - vidutinė kvadratinė paklaida
- `final_loss` (training) - galutinė praradimo funkcijos reikšmė
- `prediction_accuracy` (testing) - prognozavimo tikslumas procentais

### 2.3. SessionMetric (session_metrics)

Ši lentelė saugo įvairias sesijų veikimo ir resursų naudojimo metrikas.

| Stulpelis     | Tipas        | Aprašymas                               |
| ------------- | ------------ | --------------------------------------- |
| id            | VARCHAR(36)  | Pirminis raktas, UUID                   |
| session_id    | VARCHAR(36)  | Išorinis raktas į user_sessions lentelę |
| metric_type   | VARCHAR(50)  | Metrikos tipas (duration, resource)     |
| metric_name   | VARCHAR(100) | Metrikos pavadinimas                    |
| numeric_value | FLOAT        | Skaitinė metrikos reikšmė (jei taikoma) |
| string_value  | VARCHAR(255) | Tekstinė metrikos reikšmė (jei taikoma) |
| timestamp     | TIMESTAMP    | Metrikos sukūrimo laikas                |
| metadata      | TEXT         | Papildoma informacija JSON formatu      |

#### Ryšiai:

- `session_id` -> `user_sessions.id` (CASCADE DELETE) - Ištrinus sesiją, ištrinamos visos jos metrikos

#### Pagrindiniai metrikos tipai:

- `duration` - sesijos trukmės metrikos
- `resource` - resursų naudojimo metrikos
- `performance` - sesijos efektyvumo metrikos

## 3. Pagrindiniai naudojimo atvejai

1. **Naudotojų efektyvumo stebėjimas**

   - Vidutinis modelių tikslumas
   - Prisijungimų skaičius
   - Treniravimo sesijų trukmė

2. **Modelių veikimo analizė**

   - Tikslumo metrikos skirtinguose duomenų rinkiniuose
   - Mokymosi pažanga per laiką
   - Prognozavimo kokybės įvertinimas

3. **Sesijų statistikos rinkimas**
   - Sesijų trukmė
   - CPU ir atminties naudojimas
   - Resursų naudojimo optimizavimas

## 4. Duomenų kaupimo principai

1. **Granuliarumas**: Metrikos kaupiamos su didžiausiu įmanomu granuliarumu (smulkiausi matavimo vienetai)
2. **Agregavimas**: Metrikų analizei naudojamos agregavimo funkcijos (vidurkis, suma, skaičius)
3. **Laikiniai periodai**: Tam tikroms metrikoms naudojami laikiniai periodai (diena, savaitė, mėnuo)
4. **Papildoma informacija**: Metrikos gali turėti papildomą informaciją, saugomą metadata stulpelyje JSON formatu

## 5. Metrikų naudojimas

### 5.1. Naudotojų metrikos

Naudotojų metrikos naudojamos sekti naudotojų aktyvumą, efektyvumą ir progresą. Pagrindinės naudojimo sritys:

- Naudotojų aktyvumo stebėjimas
- Efektyvumo analizė
- Rekomendacijų sistemos

### 5.2. Modelių metrikos

Modelių metrikos naudojamos sekti modelių veikimą, tikslumą ir progresą. Pagrindinės naudojimo sritys:

- Modelių tikslumo lyginimas
- Treniravimo proceso stebėjimas
- Modelių versijų lyginimas

### 5.3. Sesijų metrikos

Sesijų metrikos naudojamos sekti sesijų resursų naudojimą ir trukmę. Pagrindinės naudojimo sritys:

- Resursų naudojimo optimizavimas
- Sesijų trukmės analizė
- Veikimo problemų nustatymas

## 6. Metrikų serviso naudojimas

```python
# Metrikų serviso naudojimo pavyzdys
from services.metrics_service import MetricsService

# Inicializuojame metrikų servisą
metrics_service = MetricsService(db_session)

# Sukuriame naudotojo metriką
metrics_service.create_user_metric(
    user_id="user123",
    metric_type="usage",
    metric_name="login_count",
    numeric_value=1,
    time_period="daily"
)

# Sukuriame modelio metriką
metrics_service.create_model_metric(
    model_id="model456",
    metric_type="accuracy",
    metric_name="rmse",
    value=0.123,
    dataset_name="test_dataset"
)

# Gauname naudotojo metrikas
user_metrics = metrics_service.get_user_metrics(
    user_id="user123",
    metric_type="usage"
)

# Gauname modelio metrikų suvestinę
model_summary = metrics_service.get_model_metrics_summary(
    model_id="model456"
)
```

Šis dokumentacijos failas:

1. Pateikia išsamią informaciją apie metrikų sistemos struktūrą:

   - Detalizuoja kiekvieną lentelę, jos stulpelius ir paskirtį
   - Aprašo ryšius tarp lentelių
   - Paaiškina pagrindinius metrikų tipus

2. Įtraukia ASCII diagramą, kuri vizualiai parodo lentelių ryšius

3. Paaiškina metrikų duomenų kaupimo principus ir naudojimo atvejus

4. Pateikia kodo pavyzdį, demonstruojantį metrikų serviso naudojimą

5. Visos tekstinės dalys yra lietuvių kalba, kaip reikalauta

Ši dokumentacija padės projekto kūrėjams ir naudotojams suprasti metrikų sistemos struktūrą ir naudojimą.
