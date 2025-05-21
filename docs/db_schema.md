# Duomenų bazės schema

## Lentelės

Šiame dokumente aprašoma projekto duomenų bazės schema, įskaitant lenteles, stulpelius ir ryšius tarp jų.

### Models lentelė

Ši lentelė skirta saugoti duomenis apie prognozinius modelius.

| Stulpelis           | Tipas        | Gali būti NULL | Aprašymas                                             |
| ------------------- | ------------ | -------------- | ----------------------------------------------------- |
| id                  | VARCHAR(50)  | Ne             | Pagrindinis raktas, unikalus modelio identifikatorius |
| name                | VARCHAR(100) | Ne             | Modelio pavadinimas                                   |
| description         | TEXT         | Taip           | Modelio aprašymas                                     |
| type                | VARCHAR(50)  | Ne             | Modelio tipas (pvz., lstm, gru, transformer)          |
| hyperparameters     | JSON         | Taip           | Modelio hiperparametrai JSON formatu                  |
| input_features      | JSON         | Taip           | Įvesties požymiai JSON formatu                        |
| performance_metrics | JSON         | Taip           | Modelio veikimo metrikos JSON formatu                 |
| created_at          | DATETIME     | Ne             | Modelio sukūrimo data ir laikas                       |

### Simulations lentelė

Ši lentelė skirta saugoti prekybos simuliacijų duomenis.

| Stulpelis       | Tipas        | Gali būti NULL | Aprašymas                                                  |
| --------------- | ------------ | -------------- | ---------------------------------------------------------- |
| id              | VARCHAR(50)  | Ne             | Pagrindinis raktas, unikalus simuliacijos identifikatorius |
| name            | VARCHAR(100) | Taip           | Simuliacijos pavadinimas                                   |
| model_id        | VARCHAR(50)  | Taip           | Išorinis raktas į models lentelę                           |
| initial_capital | FLOAT        | Ne             | Pradinis simuliacijos kapitalas                            |
| fees            | FLOAT        | Taip           | Prekybos mokesčiai                                         |
| start_date      | DATETIME     | Ne             | Simuliacijos pradžios data                                 |
| end_date        | DATETIME     | Ne             | Simuliacijos pabaigos data                                 |
| strategy_type   | VARCHAR(50)  | Taip           | Naudojamos prekybos strategijos tipas                      |
| strategy_params | TEXT         | Taip           | Strategijos parametrai                                     |
| final_balance   | FLOAT        | Ne             | Galutinis balansas simuliacijos pabaigoje                  |
| profit_loss     | FLOAT        | Ne             | Bendras pelnas/nuostolis                                   |
| roi             | FLOAT        | Ne             | Investicijų grąža (ROI)                                    |
| max_drawdown    | FLOAT        | Taip           | Maksimalus nuosmukis                                       |
| total_trades    | INTEGER      | Taip           | Bendras sandorių skaičius                                  |
| winning_trades  | INTEGER      | Taip           | Pelningų sandorių skaičius                                 |
| losing_trades   | INTEGER      | Taip           | Nuostolingų sandorių skaičius                              |
| is_completed    | TINYINT      | Taip           | Požymis, ar simuliacija baigta (1) ar ne (0)               |
| created_at      | DATETIME     | Ne             | Simuliacijos sukūrimo data ir laikas                       |
| updated_at      | DATETIME     | Taip           | Paskutinio simuliacijos atnaujinimo data ir laikas         |

### Trades lentelė

Ši lentelė skirta saugoti simuliacijos prekybos sandorių duomenis.

| Stulpelis     | Tipas       | Gali būti NULL | Aprašymas                                                               |
| ------------- | ----------- | -------------- | ----------------------------------------------------------------------- |
| id            | INTEGER     | Ne             | Pagrindinis raktas, unikalus sandorio identifikatorius (auto-increment) |
| portfolio_id  | INTEGER     | Ne             | Portfelio identifikatorius                                              |
| trade_type    | VARCHAR(10) | Ne             | Sandorio tipas                                                          |
| btc_amount    | FLOAT       | Ne             | BTC kiekis                                                              |
| price         | FLOAT       | Ne             | Kaina                                                                   |
| value         | FLOAT       | Ne             | Vertė (kaina \* kiekis)                                                 |
| timestamp     | DATETIME    | Taip           | Sandorio laiko žyma                                                     |
| simulation_id | VARCHAR(50) | Taip           | Išorinis raktas į simulations lentelę                                   |
| date          | DATETIME    | Taip           | Sandorio data                                                           |
| type          | VARCHAR(10) | Taip           | Sandorio tipas (buy/sell)                                               |
| amount        | FLOAT       | Taip           | Kiekis                                                                  |
| fee           | FLOAT       | Taip           | Sandorio mokestis                                                       |
| profit_loss   | FLOAT       | Taip           | Sandorio pelnas/nuostolis                                               |
| created_at    | DATETIME    | Taip           | Sandorio įrašo sukūrimo data ir laikas                                  |

### Predictions lentelė

Ši lentelė skirta saugoti modelių prognozių duomenis.

| Stulpelis       | Tipas       | Gali būti NULL | Aprašymas                                               |
| --------------- | ----------- | -------------- | ------------------------------------------------------- |
| id              | VARCHAR(50) | Ne             | Pagrindinis raktas, unikalus prognozės identifikatorius |
| model_id        | VARCHAR(50) | Ne             | Išorinis raktas į models lentelę                        |
| prediction_date | DATETIME    | Ne             | Prognozės sukūrimo data                                 |
| target_date     | DATETIME    | Ne             | Data, kuriai atliekama prognozė                         |
| predicted_value | FLOAT       | Ne             | Prognozuojama vertė                                     |
| actual_value    | FLOAT       | Taip           | Faktinė vertė (pildoma vėliau)                          |
| interval        | VARCHAR(10) | Ne             | Prognozės intervalas (pvz., 1h, 4h, 1d, 1w)             |
| confidence      | FLOAT       | Taip           | Pasitikėjimo lygis (0-1)                                |
| created_at      | DATETIME    | Ne             | Įrašo sukūrimo data ir laikas                           |

## Lentelių ryšiai

### One-to-Many ryšiai:

1. **Model -> Simulation**:

   - Vienas modelis gali būti naudojamas daugelyje simuliacijų.
   - Ryšys realizuojamas per `model_id` stulpelį `simulations` lentelėje, kuris yra išorinis raktas, rodantis į `models` lentelės `id` stulpelį.

2. **Model -> Prediction**:

   - Vienas modelis gali turėti daug prognozių.
   - Ryšys realizuojamas per `model_id` stulpelį `predictions` lentelėje, kuris yra išorinis raktas, rodantis į `models` lentelės `id` stulpelį.

3. **Simulation -> Trade**:
   - Viena simuliacija gali turėti daug prekybos sandorių.
   - Ryšys realizuojamas per `simulation_id` stulpelį `trades` lentelėje, kuris yra išorinis raktas, rodantis į `simulations` lentelės `id` stulpelį.

## Kaskadinis trynimas

Kaskadinis trynimas duomenų bazėje leidžia automatiškai pašalinti visus susijusius įrašus, kai ištrinamas pirminis įrašas.

Šioje sistemoje kaskadinis trynimas veikia taip:

1. **Kai ištrinamas Model įrašas**:

   - Automatiškai ištrinamos visos susijusios Simulation eilutės (tos, kurios turi atitinkamą `model_id`).
   - Automatiškai ištrinamos visos susijusios Prediction eilutės (tos, kurios turi atitinkamą `model_id`).

2. **Kai ištrinamas Simulation įrašas**:
   - Automatiškai ištrinamos visos susijusios Trade eilutės (tos, kurios turi atitinkamą `simulation_id`).

Kaskadinis trynimas realizuojamas naudojant `ON DELETE CASCADE` apribojimą išoriniams raktams. Tai reiškia, kad kai ištrinamas įrašas iš pagrindinės lentelės, duomenų bazės valdymo sistema automatiškai ištrina susijusius įrašus iš susijusių lentelių, nereikalaujant papildomo programinio kodo.

Testuose (`tests/test_relationship.py`) taip pat patikrinamas kaskadinio trynimo veikimas, užtikrinant, kad ištrynus simuliaciją, būtų ištrinti visi susiję prekybos sandoriai.
