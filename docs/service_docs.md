# Servisų metodų dokumentacija

Šiame dokumente aprašomi sistemoje naudojami servisai, jų metodai, parametrai ir galimos klaidos.

## Bendri principai

Visi servisai naudoja repozitorijos šabloną darbui su duomenų baze. Kiekvieno serviso operacijos yra apsaugotos nuo bendrų klaidų per išimčių apdorojimą. Klaidos registruojamos žurnale.

## ModelService

Servisas, skirtas darbui su modeliais.

### Metodai

#### create_model(model_data)

**Paskirtis**: Sukuria naują modelį duomenų bazėje.

**Parametrai**:

- `model_data` (dict): Modelio duomenys, kurie turi atitikti Model lentelės struktūrą.

**Grąžinama reikšmė**:

- Sėkmės atveju: Model objektas, kuris buvo sukurtas.
- Nesėkmės atveju: None.

**Galimos klaidos**:

- Trūksta privalomų laukų (id, name, type).
- Negaliojanti JSON struktūra hyperparameters, input_features, ar performance_metrics laukuose.
- Duomenų bazės ryšio klaidos.

#### get_model(model_id)

**Paskirtis**: Gauna modelį pagal jo ID.

**Parametrai**:

- `model_id` (str): Modelio ID, kurį norime gauti.

**Grąžinama reikšmė**:

- Sėkmės atveju: Model objektas, atitinkantis nurodytą ID.
- Jei modelio nėra: None.

**Galimos klaidos**:

- Negaliojantis modelio ID formatas.
- Duomenų bazės ryšio klaidos.

#### update_model(model_id, model_data)

**Paskirtis**: Atnaujina esamą modelį.

**Parametrai**:

- `model_id` (str): Modelio, kurį norime atnaujinti, ID.
- `model_data` (dict): Nauji modelio duomenys, kurie pakeis esamus.

**Grąžinama reikšmė**:

- Sėkmės atveju: Atnaujintas Model objektas.
- Jei modelis nerastas: None.

**Galimos klaidos**:

- Negaliojantis modelio ID formatas.
- Bandymas atnaujinti neegzistuojantį modelį.
- Negaliojanti JSON struktūra atnaujinant JSON laukus.
- Duomenų bazės ryšio klaidos.

#### delete_model(model_id)

**Paskirtis**: Ištrina modelį ir visus su juo susijusius duomenis (simuliacijas, prognozes).

**Parametrai**:

- `model_id` (str): Modelio, kurį norime ištrinti, ID.

**Grąžinama reikšmė**:

- Sėkmės atveju: True.
- Nesėkmės atveju: False.

**Galimos klaidos**:

- Negalima ištrinti modelio, kuris naudojamas veikiančiose simuliacijose.
- Duomenų bazės ryšio klaidos.

#### list_models(limit=100, offset=0, model_type=None, sort_by="created_at", sort_order="desc")

**Paskirtis**: Gauna modelių sąrašą su galimybe filtruoti ir rikiuoti.

**Parametrai**:

- `limit` (int, optional): Maksimalus grąžinamų modelių skaičius. Numatytoji reikšmė: 100.
- `offset` (int, optional): Praleistų įrašų skaičius (puslapis). Numatytoji reikšmė: 0.
- `model_type` (str, optional): Modelio tipo filtras. Numatytoji reikšmė: None (visi tipai).
- `sort_by` (str, optional): Laukas, pagal kurį rikiuojama. Numatytoji reikšmė: "created_at".
- `sort_order` (str, optional): Rikiavimo tvarka ("asc" - didėjančiai, "desc" - mažėjančiai). Numatytoji reikšmė: "desc".

**Grąžinama reikšmė**:

- Sėkmės atveju: List[Model] - modelių sąrašas.
- Nesėkmės atveju: tuščias sąrašas.

**Galimos klaidos**:

- Neleistinos parametrų reikšmės.
- Duomenų bazės ryšio klaidos.

## SimulationService

Servisas, skirtas darbui su prekybos simuliacijomis.

### Metodai

#### create_simulation(simulation_data)

**Paskirtis**: Sukuria naują prekybos simuliaciją.

**Parametrai**:

- `simulation_data` (dict): Simuliacijos duomenys, atitinkantys Simulation lentelės struktūrą.

**Grąžinama reikšmė**:

- Sėkmės atveju: Simulation objektas, kuris buvo sukurtas.
- Nesėkmės atveju: None.

**Galimos klaidos**:

- Trūksta privalomų laukų (id, initial_capital, start_date, end_date ir kt.).
- Nurodytas neegzistuojantis model_id.
- Pradinės datos reikšmė vėlesnė už pabaigos datą.
- Duomenų bazės ryšio klaidos.

#### get_simulation(simulation_id)

**Paskirtis**: Gauna simuliaciją pagal jos ID.

**Parametrai**:

- `simulation_id` (str): Simuliacijos ID, kurią norime gauti.

**Grąžinama reikšmė**:

- Sėkmės atveju: Simulation objektas, atitinkantis nurodytą ID.
- Jei simuliacijos nėra: None.

**Galimos klaidos**:

- Negaliojantis simuliacijos ID formatas.
- Duomenų bazės ryšio klaidos.

#### update_simulation(simulation_id, simulation_data)

**Paskirtis**: Atnaujina esamą simuliaciją.

**Parametrai**:

- `simulation_id` (str): Simuliacijos, kurią norime atnaujinti, ID.
- `simulation_data` (dict): Nauji simuliacijos duomenys, kurie pakeis esamus.

**Grąžinama reikšmė**:

- Sėkmės atveju: Atnaujintas Simulation objektas.
- Jei simuliacija nerasta: None.

**Galimos klaidos**:

- Negaliojantis simuliacijos ID formatas.
- Bandymas atnaujinti neegzistuojančią simuliaciją.
- Negaliojančios datos (pradžios data vėlesnė už pabaigos datą).
- Duomenų bazės ryšio klaidos.

#### delete_simulation(simulation_id)

**Paskirtis**: Ištrina simuliaciją ir visus su ja susijusius sandorius.

**Parametrai**:

- `simulation_id` (str): Simuliacijos, kurią norime ištrinti, ID.

**Grąžinama reikšmė**:

- Sėkmės atveju: True.
- Nesėkmės atveju: False.

**Galimos klaidos**:

- Negalima ištrinti simuliacijos, kuri naudojama aktyviuose procesuose.
- Ryšio su duomenų baze klaidos.

#### list_simulations(limit=100, offset=0, model_id=None, is_completed=None, sort_by="created_at", sort_order="desc")

**Paskirtis**: Gauna simuliacijų sąrašą su galimybe filtruoti ir rikiuoti.

**Parametrai**:

- `limit` (int, optional): Maksimalus grąžinamų simuliacijų skaičius. Numatytoji reikšmė: 100.
- `offset` (int, optional): Praleistų įrašų skaičius (puslapis). Numatytoji reikšmė: 0.
- `model_id` (str, optional): Filtravimas pagal modelio ID. Numatytoji reikšmė: None.
- `is_completed` (bool, optional): Filtravimas pagal užbaigimo būseną. Numatytoji reikšmė: None (visos simuliacijos).
- `sort_by` (str, optional): Laukas, pagal kurį rikiuojama. Numatytoji reikšmė: "created_at".
- `sort_order` (str, optional): Rikiavimo tvarka ("asc" - didėjančiai, "desc" - mažėjančiai). Numatytoji reikšmė: "desc".

**Grąžinama reikšmė**:

- Sėkmės atveju: List[Simulation] - simuliacijų sąrašas.
- Nesėkmės atveju: tuščias sąrašas.

**Galimos klaidos**:

- Neleistinos parametrų reikšmės.
- Duomenų bazės ryšio klaidos.

#### get_simulation_trades(simulation_id, limit=None, offset=None)

**Paskirtis**: Gauna simuliacijos prekybos sandorius.

**Parametrai**:

- `simulation_id` (str): Simuliacijos ID, kurios sandorius norime gauti.
- `limit` (int, optional): Maksimalus grąžinamų sandorių skaičius. Numatytoji reikšmė: None (visi sandoriai).
- `offset` (int, optional): Praleistų įrašų skaičius. Numatytoji reikšmė: None.

**Grąžinama reikšmė**:

- Sėkmės atveju: List[Trade] - sandorių sąrašas.
- Nesėkmės atveju: tuščias sąrašas.

**Galimos klaidos**:

- Neegzistuojanti simuliacija.
- Duomenų bazės ryšio klaidos.

## TradeService

Servisas, skirtas darbui su prekybos sandoriais.

### Metodai

#### create_trade(trade_data)

**Paskirtis**: Sukuria naują prekybos sandorį.

**Parametrai**:

- `trade_data` (dict): Prekybos sandorio duomenys, atitinkantys Trade lentelės struktūrą.

**Grąžinama reikšmė**:

- Sėkmės atveju: Trade objektas, kuris buvo sukurtas.
- Nesėkmės atveju: None.

**Galimos klaidos**:

- Trūksta privalomų laukų (portfolio_id, trade_type, btc_amount, price, value).
- Nurodytas neegzistuojantis simulation_id.
- Duomenų bazės ryšio klaidos.

#### get_trade(trade_id)

**Paskirtis**: Gauna prekybos sandorį pagal jo ID.

**Parametrai**:

- `trade_id` (int): Prekybos sandorio ID, kurį norime gauti.

**Grąžinama reikšmė**:

- Sėkmės atveju: Trade objektas, atitinkantis nurodytą ID.
- Jei sandorio nėra: None.

**Galimos klaidos**:

- Negaliojantis sandorio ID formatas.
- Duomenų bazės ryšio klaidos.

#### update_trade(trade_id, trade_data)

**Paskirtis**: Atnaujina esamą prekybos sandorį.

**Parametrai**:

- `trade_id` (int): Sandorio, kurį norime atnaujinti, ID.
- `trade_data` (dict): Nauji sandorio duomenys, kurie pakeis esamus.

**Grąžinama reikšmė**:

- Sėkmės atveju: Atnaujintas Trade objektas.
- Jei sandoris nerastas: None.

**Galimos klaidos**:

- Negaliojantis sandorio ID formatas.
- Bandymas atnaujinti neegzistuojantį sandorį.
- Nurodytas neegzistuojantis simulation_id.
- Duomenų bazės ryšio klaidos.

#### delete_trade(trade_id)

**Paskirtis**: Ištrina prekybos sandorį.

**Parametrai**:

- `trade_id` (int): Sandorio, kurį norime ištrinti, ID.

**Grąžinama reikšmė**:

- Sėkmės atveju: True.
- Nesėkmės atveju: False.

**Galimos klaidos**:

- Negaliojantis sandorio ID formatas.
- Duomenų bazės ryšio klaidos.

#### list_trades(limit=100, offset=0, simulation_id=None, trade_type=None, date_from=None, date_to=None, sort_by="date", sort_order="desc")

**Paskirtis**: Gauna prekybos sandorių sąrašą su galimybe filtruoti ir rikiuoti.

**Parametrai**:

- `limit` (int, optional): Maksimalus grąžinamų sandorių skaičius. Numatytoji reikšmė: 100.
- `offset` (int, optional): Praleistų įrašų skaičius (puslapis). Numatytoji reikšmė: 0.
- `simulation_id` (str, optional): Filtravimas pagal simuliacijos ID. Numatytoji reikšmė: None.
- `trade_type` (str, optional): Filtravimas pagal sandorio tipą. Numatytoji reikšmė: None.
- `date_from` (datetime, optional): Filtravimas pagal pradžios datą. Numatytoji reikšmė: None.
- `date_to` (datetime, optional): Filtravimas pagal pabaigos datą. Numatytoji reikšmė: None.
- `sort_by` (str, optional): Laukas, pagal kurį rikiuojama. Numatytoji reikšmė: "date".
- `sort_order` (str, optional): Rikiavimo tvarka ("asc" - didėjančiai, "desc" - mažėjančiai). Numatytoji reikšmė: "desc".

**Grąžinama reikšmė**:

- Sėkmės atveju: List[Trade] - sandorių sąrašas.
- Nesėkmės atveju: tuščias sąrašas.

**Galimos klaidos**:

- Neleistinos parametrų reikšmės.
- Neteisingas datos formatas filtrų parametruose.
- Duomenų bazės ryšio klaidos.

## PredictionService

Servisas, skirtas darbui su prognozėmis.

### Metodai

#### create_prediction(prediction_data)

**Paskirtis**: Sukuria naują prognozę.

**Parametrai**:

- `prediction_data` (dict): Prognozės duomenys, atitinkantys Prediction lentelės struktūrą.

**Grąžinama reikšmė**:

- Sėkmės atveju: Prediction objektas, kuris buvo sukurtas.
- Nesėkmės atveju: None.

**Galimos klaidos**:

- Trūksta privalomų laukų (id, model_id, prediction_date, target_date, predicted_value, interval).
- Nurodytas neegzistuojantis model_id.
- Duomenų bazės ryšio klaidos.

#### get_prediction(prediction_id)

**Paskirtis**: Gauna prognozę pagal jos ID.

**Parametrai**:

- `prediction_id` (str): Prognozės ID, kurią norime gauti.

**Grąžinama reikšmė**:

- Sėkmės atveju: Prediction objektas, atitinkantis nurodytą ID.
- Jei prognozės nėra: None.

**Galimos klaidos**:

- Negaliojantis prognozės ID formatas.
- Duomenų bazės ryšio klaidos.

#### update_prediction(prediction_id, prediction_data)

**Paskirtis**: Atnaujina esamą prognozę.

**Parametrai**:

- `prediction_id` (str): Prognozės, kurią norime atnaujinti, ID.
- `prediction_data` (dict): Nauji prognozės duomenys, kurie pakeis esamus.

**Grąžinama reikšmė**:

- Sėkmės atveju: Atnaujintas Prediction objektas.
- Jei prognozė nerasta: None.

**Galimos klaidos**:

- Negaliojantis prognozės ID formatas.
- Bandymas atnaujinti neegzistuojančią prognozę.
- Nurodytas neegzistuojantis model_id.
- Duomenų bazės ryšio klaidos.

#### delete_prediction(prediction_id)

**Paskirtis**: Ištrina prognozę.

**Parametrai**:

- `prediction_id` (str): Prognozės, kurią norime ištrinti, ID.

**Grąžinama reikšmė**:

- Sėkmės atveju: True.
- Nesėkmės atveju: False.

**Galimos klaidos**:

- Negaliojantis prognozės ID formatas.
- Duomenų bazės ryšio klaidos.

#### list_predictions(limit=100, offset=0, model_id=None, interval=None, date_from=None, date_to=None, sort_by="prediction_date", sort_order="desc")

**Paskirtis**: Gauna prognozių sąrašą su galimybe filtruoti ir rikiuoti.

**Parametrai**:

- `limit` (int, optional): Maksimalus grąžinamų prognozių skaičius. Numatytoji reikšmė: 100.
- `offset` (int, optional): Praleistų įrašų skaičius (puslapis). Numatytoji reikšmė: 0.
- `model_id` (str, optional): Filtravimas pagal modelio ID. Numatytoji reikšmė: None.
- `interval` (str, optional): Filtravimas pagal laiko intervalą. Numatytoji reikšmė: None.
- `date_from` (datetime, optional): Filtravimas pagal pradžios datą. Numatytoji reikšmė: None.
- `date_to` (datetime, optional): Filtravimas pagal pabaigos datą. Numatytoji reikšmė: None.
- `sort_by` (str, optional): Laukas, pagal kurį rikiuojama. Numatytoji reikšmė: "prediction_date".
- `sort_order` (str, optional): Rikiavimo tvarka ("asc" - didėjančiai, "desc" - mažėjančiai). Numatytoji reikšmė: "desc".

**Grąžinama reikšmė**:

- Sėkmės atveju: List[Prediction] - prognozių sąrašas.
- Nesėkmės atveju: tuščias sąrašas.

**Galimos klaidos**:

- Neleistinos parametrų reikšmės.
- Neteisingas datos formatas filtrų parametruose.
- Duomenų bazės ryšio klaidos.

#### update_actual_value(prediction_id, actual_value)

**Paskirtis**: Atnaujina prognozės faktinę vertę (kada jau žinoma tikroji kaina).

**Parametrai**:

- `prediction_id` (str): Prognozės, kurią norime atnaujinti, ID.
- `actual_value` (float): Faktinė (tikroji) kaina.

**Grąžinama reikšmė**:

- Sėkmės atveju: Atnaujintas Prediction objektas.
- Jei prognozė nerasta: None.

**Galimos klaidos**:

- Negaliojantis prognozės ID formatas.
- Duomenų bazės ryšio klaidos.
