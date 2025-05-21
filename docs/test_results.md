# Testavimo rezultatai

Šiame dokumente aprašomi projekto testavimo rezultatai, išvados ir rekomendacijos.

## 1. Duomenų bazės ryšių testavimas

### 1.1. Testavimo tikslas

Duomenų bazės ryšių testavimo tikslas buvo patikrinti, ar teisingai sukonfigūruoti reliaciniai ryšiai tarp lentelių:

- Model -> Simulation (one-to-many)
- Simulation -> Trade (one-to-many)
- Model -> Prediction (one-to-many)

### 1.2. Testavimo metodika

Ryšių testavimui naudojome `tests/test_relationship.py` testavimo skriptą, kuris:

1. Sukuria testinį modelį.
2. Sukuria testinę simuliaciją, susietą su modeliu.
3. Sukuria testinius prekybos sandorius, susietus su simuliacija.
4. Patikrina, ar galima pasiekti susijusius objektus per ryšius.

### 1.3. Testavimo rezultatai

| Testas                    | Rezultatas | Pastabos                                                        |
| ------------------------- | ---------- | --------------------------------------------------------------- |
| Model -> Simulation ryšys | ✅ Pavyko  | Iš modelio objekto galima gauti visas susijusias simuliacijas   |
| Simulation -> Trade ryšys | ✅ Pavyko  | Iš simuliacijos objekto galima gauti visus susijusius sandorius |
| Simulation -> Model ryšys | ✅ Pavyko  | Iš simuliacijos galima gauti susietą modelį                     |
| Trade -> Simulation ryšys | ✅ Pavyko  | Iš sandorio galima gauti susietą simuliaciją                    |

### 1.4. Išvados

Visi duomenų bazės ryšiai veikia teisingai. SQLAlchemy ORM sėkmingai susieja objektus pagal apibrėžtus ryšius.

## 2. Kaskadinio trynimo testavimas

### 2.1. Testavimo tikslas

Kaskadinio trynimo testavimo tikslas buvo patikrinti, ar ištrynus pagrindinį objektą (pvz., modelį arba simuliaciją), automatiškai ištrinami ir visi su juo susiję priklausomi objektai.

### 2.2. Testavimo metodika

Kaskadinio trynimo testavimui naudojome `examples/delete_example.py` skriptą, kuris:

1. Pasirenka esamą simuliaciją iš duomenų bazės.
2. Patikrina, kiek ji turi susijusių sandorių.
3. Ištrina simuliaciją.
4. Patikrina, ar buvo ištrinti visi susiję sandoriai.

Taip pat panašiai testuojame modelio trynimą ir su juo susijusių simuliacijų ištrynimą.

### 2.3. Testavimo rezultatai

| Testas                                      | Rezultatas | Pastabos                                             |
| ------------------------------------------- | ---------- | ---------------------------------------------------- |
| Simuliacijos ir jos sandorių ištrynimas     | ✅ Pavyko  | Visi susiję sandoriai buvo ištrinti                  |
| Modelio ir jo simuliacijų ištrynimas        | ✅ Pavyko  | Visos susijusios simuliacijos buvo ištrintos         |
| Modelio, simuliacijų ir sandorių ištrynimas | ✅ Pavyko  | Ištrinti visi susiję objektai per kelis ryšių lygius |

### 2.4. Išvados

Kaskadinis trynimas veikia teisingai visuose testuotuose scenarijuose. SQLAlchemy teisingai pritaiko `cascade="all, delete-orphan"` nustatymą.

## 3. Aptikti defektai ir jų pataisymai

### 3.1. Trūkstami būtini laukai

| Defektas                                                                                 | Pataisymas                                                 | Statusas     |
| ---------------------------------------------------------------------------------------- | ---------------------------------------------------------- | ------------ |
| Kuriant naują sandorį (Trade), nebuvo tikrinama, ar nurodytas privalomas `portfolio_id`  | Pridėtas patikrinimas `TradeService.create_trade()` metode | ✅ Ištaisyta |
| Simuliacijos sukūrimo metu nebuvo tikrinama, ar pradžios data ankstesnė už pabaigos datą | Pridėtas datos validavimo patikrinimas                     | ✅ Ištaisyta |

### 3.2. Neteisingi ryšių konfigūravimai

| Defektas                                                               | Pataisymas                          | Statusas     |
| ---------------------------------------------------------------------- | ----------------------------------- | ------------ |
| Model klasėje nebuvo apibrėžtas dvikryptis ryšys su Prediction         | Pridėtas `relationship` apibrėžimas | ✅ Ištaisyta |
| Simulation klasėje buvo neteisingai apibrėžtas išorinis raktas į Model | Pataisytas ForeignKey apibrėžimas   | ✅ Ištaisyta |

### 3.3. Kitos problemos

| Defektas                                                               | Pataisymas                                                   | Statusas     |
| ---------------------------------------------------------------------- | ------------------------------------------------------------ | ------------ |
| Trynimo operacijose nebuvo naudojamas sesijos `commit()` po `delete()` | Pridėtas `session.commit()` po kiekvienos trynimo operacijos | ✅ Ištaisyta |
| Nebūdavo atšaukiama (rollback) transakcija klaidos atveju              | Pridėti try-except blokai su session.rollback()              | ✅ Ištaisyta |

## 4. Testavimo išvados ir rekomendacijos

### 4.1. Išvados

1. **Duomenų bazės schema**: Duomenų bazės schema gerai suprojektuota ir veikia tinkamai. Ryšiai tarp lentelių teisingai apibrėžti ir veikia pagal reikalavimus.

2. **Kaskadinis trynimas**: Kaskadinis duomenų trynimas veikia tinkamai, kas užtikrina duomenų bazės vientisumą.

3. **Servisų funkcionalumas**: Visi servisų metodai veikia teisingai ir tinkamai apdoroja klaidas.

### 4.2. Rekomendacijos

1. **Išplėsti testų aprėptį**:

   - Pridėti testus, kurie tikrintų neteisingų duomenų apdorojimą.
   - Sukurti testus ribiniams atvejams (pavyzdžiui, labai dideliems duomenų kiekiams).

2. **Pagerinti klaidų valdymą**:

   - Patobulinti klaidų pranešimus, kad jie būtų informatyvesni.
   - Sukurti atskirą klaidų žurnalą, skirtą tik duomenų operacijoms.

3. **Patobulinti transakcijų valdymą**:

   - Įgyvendinti atominį operacijų vykdymą sudėtingiems scenarijams.
   - Pridėti užraktų mechanizmus, kad būtų išvengta konkurencijos problemų.

4. **Papildomi saugumo testai**:

   - Patikrinti SQL injekcijų prevencijos mechanizmus.
   - Testuoti prieigos kontrolės mechanizmus.

5. **Veikimo optimizavimas**:
   - Pridėti indeksus dažniausiai naudojamiems paieškos laukams.
   - Optimizuoti sudėtingas užklausas, kurios apima kelis ryšius.

### 4.3. Tolesni veiksmai

1. Įgyvendinti rekomenduotus patobulinimus pagal prioritetus.
2. Reguliariai kartoti testus po kiekvieno reikšmingo pakeitimo.
3. Automatizuoti testavimo procesą integruojant jį į CI/CD vamzdį.
