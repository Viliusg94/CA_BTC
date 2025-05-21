# Bitcoin Prekybos Simuliatorius

## Apie projektą

Bitcoin Prekybos Simuliatorius yra įrankis, leidžiantis prognozuoti Bitcoin kainos pokyčius ir testuoti įvairias prekybos strategijas. Sistema naudoja mašininio mokymosi modelius kainų prognozavimui ir simuliuoja prekybos sandorius pagal nurodytas strategijas.

## Pagrindinės funkcijos

- 📈 **Kainų prognozavimas**: Įvairių mašininio mokymosi modelių (LSTM, GRU, Transformer) naudojimas Bitcoin kainų prognozavimui
- 💹 **Strategijų testavimas**: Prekybos strategijų testavimas istoriniais duomenimis be realios rizikos
- 📊 **Rezultatų analizė**: Išsamios simuliacijų analizės ir veiklos rezultatų vertinimas
- 📝 **Sandorių apskaita**: Automatinė prekybos sandorių registracija ir jų analizė

## Kaip pradėti

1. Įdiekite reikalingas bibliotekas:
   ```bash
   pip install -r requirements.txt
   ```
2. Paruoškite duomenis:
   - Atsisiųskite istorinius Bitcoin kainų duomenis iš patikimo šaltinio
   - Įkelkite duomenis į sistemą naudodami `data_loader.py` skriptą
3. Pasirinkite prekybos strategiją:
   - Peržiūrėkite ir redaguokite strategijų nustatymus faile `config/strategy_config.json`
4. Paleiskite simuliaciją:
   ```bash
   python run_simulation.py
   ```
5. Peržiūrėkite rezultatus:
   - Analizuokite simuliacijos rezultatus faile `results/simulation_results.csv`
   - Naudokite `results_analyzer.py` skriptą, kad gautumėte išsamesnę analizę

## Dokumentacija

Išsamesnė projekto dokumentacija yra prieinama šiuose failuose:

- [Duomenų bazės schema](db_schema.md): Detalus duomenų bazės struktūros aprašymas
- [Servisų metodų dokumentacija](service_docs.md): Informacija apie projekto servisų metodus
- [Naudojimo pavyzdžiai](usage_examples.md): Praktiniai pavyzdžiai, kaip naudoti sistemą
- [Testų rezultatai](test_results.md): Sistemos testavimo rezultatai ir išvados

## Indeksas

- [Projekto struktūra](#projekto-struktura)
- [Priklausomybės](#priklausomybes)
- [Diegimas](#diegiant)
- [Naudojimas](#naudojimas)
- [Testavimas](#testavimas)
- [Problemos ir sprendimai](#problemos-ir-sprendimai)
- [Ateities plėtros kryptys](#ateities-pletros-kryptys)
- [Autoriai](#autoriai)
- [Licencija](#licencija)

## Projekto struktūra

```
/bitcoin_trading_simulator
|-- /data
|   |-- raw_data.csv
|   |-- processed_data.csv
|-- /results
|   |-- simulation_results.csv
|   |-- performance_metrics.json
|-- /src
|   |-- main.py
|   |-- data_loader.py
|   |-- model_trainer.py
|   |-- strategy_tester.py
|   |-- results_analyzer.py
|-- /tests
|   |-- test_data_loader.py
|   |-- test_model_trainer.py
|   |-- test_strategy_tester.py
|-- requirements.txt
|-- README.md
|-- LICENSE
```

## Priklausomybės

Projekto sėkmingam veikimui reikalingos šios Python bibliotekos:

- `numpy`: Mokslo skaičiavimams
- `pandas`: Duomenų analizei ir manipuliavimui
- `matplotlib`: Duomenų vizualizavimui
- `scikit-learn`: Mašininio mokymosi modelių kūrimui ir vertinimui
- `tensorflow` arba `pytorch`: Giliam mokymuisi (priklauso nuo pasirinkto modelio)
- `statsmodels`: Statistinei analizei

## Diegimas

Norėdami įdiegti projektą, atlikite šiuos veiksmus:

1. Klonuokite saugyklą į savo kompiuterį:
   ```bash
   git clone https://github.com/vartotojas/bitcoin_trading_simulator.git
   ```
2. Eikite į projekto katalogą:
   ```bash
   cd bitcoin_trading_simulator
   ```
3. Įdiekite priklausomybes:
   ```bash
   pip install -r requirements.txt
   ```
4. (Pasirinktinai) Sukurkite virtualią aplinką, kad izoliuotumėte projekto priklausomybes:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate  # Windows
   ```

## Naudojimas

Norėdami naudoti Bitcoin Prekybos Simuliatorių, atlikite šiuos veiksmus:

1. Paruoškite duomenis, kaip aprašyta skyriuje "Kaip pradėti"
2. Pasirinkite ir sukonfigūruokite prekybos strategiją
3. Paleiskite simuliaciją
4. Analizuokite gautus rezultatus ir, prireikus, tobulinkite strategiją

## Testavimas

Projekte yra įtraukti automatizuoti testai, skirti patikrinti pagrindinėms funkcijoms:

- Duomenų įkėlimo testai
- Modelių mokymo ir prognozavimo testai
- Prekybos strategijų testai
- Rezultatų analizės testai

Norėdami paleisti testus, vykdykite šią komandą:

```bash
pytest
```

## Problemos ir sprendimai

Dažniausiai pasitaikančios problemos ir jų sprendimai:

- **Problema**: Nepavyksta įkelti duomenų iš CSV failo
  - **Sprendimas**: Patikrinkite, ar teisingai nurodytas failo kelias ir ar failas nėra užrakintas kitų programų
- **Problema**: Modelio mokymas nepavyksta dėl duomenų trūkumo
  - **Sprendimas**: Įsitikinkite, kad turite pakankamai duomenų mokymui, ir, jei reikia, pridėkite daugiau duomenų
- **Problema**: Simuliacijos rezultatai atrodo netikslūs
  - **Sprendimas**: Patikrinkite strategijos nustatymus ir įsitikinkite, kad jie atitinka jūsų lūkesčius

## Ateities plėtros kryptys

Galimos projekto plėtros kryptys:

- Naujų mašininio mokymosi modelių pridėjimas
- Išplėstinė prekybos strategijų analizė ir optimizavimas
- Naudotojo sąsajos kūrimas, kad sistema būtų prieinamesnė
- Integracija su realių laikų duomenų šaltiniais, kad būtų galima atlikti gyvų prekybos simuliacijų

## Autoriai

Projekto autoriai ir prisidėję asmenys:

- Vardas Pavardė ([@github_vardas](https://github.com/github_vardas)) - Pagrindinis kūrėjas
- Vardas Pavardė ([@github_vardas2](https://github.com/github_vardas2)) - Duomenų analizės specialistas
- Vardas Pavardė ([@github_vardas3](https://github.com/github_vardas3)) - Mašininio mokymosi inžinierius

## Licencija

Šis projektas yra licencijuotas pagal MIT licenciją - skaitykite [LICENSE](LICENSE) failą daugiau informacijos.
