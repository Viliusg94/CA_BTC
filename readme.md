🔁 9. Hiperparametrų optimizavimas
Užduotis:
Optimizuoti modelių parametrus
9.1 Bazinis hiperparametrų paieškos framework
Sukurti parametrų paieškos infrastruktūrą
Implementuoti GridSearch ir RandomSearch metodus
Sukurti rezultatų saugojimo ir analizės mechanizmą
Implementuoti parallel processing testavimui pagreitinti
✅
Checkpoint 9.1:
Veikia bazinis hiperparametrų paieškos framework
9.2 ML modelių optimizavimas
Atlikti paprastų modelių hiperparametrų optimizavimą
Išbandyti bent 10 skirtingų parametrų kombinacijų
Išsaugoti rezultatus ir išrinkti geriausius parametrus
Sukurti konfigūracijos failą optimaliems parametrams
✅
Checkpoint 9.2:
ML modelių hiperparametrai optimizuoti
9.3 Neuroninių tinklų optimizavimas
Optimizuoti:
Learning rate
Batch size
Epochs
Hidden layers skaičius ir dydis
Dropout rate
Activation functions
Išbandyti bent 15 skirtingų kombinacijų
✅
Checkpoint 9.3:
Neuroninių tinklų hiperparametrai optimizuoti
9.4 Prekybos strategijų parametrų optimizavimas
Optimizuoti prekybos parametrus:
Stop-loss/Take-profit santykį
Pozicijos dydį
Įėjimo/išėjimo slenkščius
Trailing stop parametrus
Signalų filtravimo slenkščius
Išbandyti bent 10 skirtingų kombinacijų
✅
Checkpoint 9.4:
Prekybos strategijų parametrai optimizuoti
9.5 Pažangesni optimizavimo metodai
Implementuoti Bayesian Optimization
Išbandyti genetinius algoritmus parametrų paieškai
Implementuoti Optuna ar kitas pažangias bibliotekas
Palyginti su baziniais metodais
✅
Checkpoint 9.5:
Pažangesni optimizavimo metodai įgyvendinti
9.6 Testavimo rezultatų apibendrinimas
Sukurti bent 30+ skirtingų bandymų rezultatų lentelę
Atlikti statistinę rezultatų analizę
Identifikuoti geriausius parametrų rinkinius
Parengti apibendrinimo ataskaitą
✅
Checkpoint 9.6:
Visų testavimų rezultatai apibendrinti# 🧠 Tavo Projektas: BTC valiutos kursoprognozė su ML ir prekybos simuliatorius
🎯 Projekto tikslas
Sukurti sistemą, kuri ne tik prognozuoja Bitcoin (BTC) kurso pokyčius, bet ir simuliuoja prekybossprendimus pagal mašininio mokymosi modelių prognozes.
🧱 1. Duomenų bazė su MySQL ir SQLAlchemy
Užduotis:
Sukurti MySQL duomenų bazę Bitcoin duomenims
1.1 Duomenų bazės sukūrimas
Sukonfigūruoti MySQL serverį projekte
Sukurti duomenų bazės schemą
Parengti prisijungimo konfigūraciją su slaptažodžiais (.env faile)
✅
Checkpoint 1.1:
MySQL duomenų bazė sukurta ir pasiekiama programiškai
1.2 SQLAlchemy ORM modeliai
Sukurti pagrindinius duomenų modelius:
BTC kainų istoriniai duomenys
Techninių indikatorių lentelė
Prognozių lentelė
Naudotojų lentelė
Prekybos operacijų lentelė
Portfelio būsenos lentelė
✅
Checkpoint 1.2:
SQLAlchemy ORM modeliai sukurti ir veikia migracija
1.3 Duomenų importavimas
Sukurti API klientus duomenims gauti (CoinGecko, Binance)
Sukurti duomenų importavimo skriptus iš CSV failų
Realizuoti duomenų importavimo logiką į MySQL
Sukurti validavimo mechanizmą duomenims tikrinti
✅
Checkpoint 1.3:
Duomenys sėkmingai importuojami į MySQL duomenų bazę
1.4 Duomenų užklausų realizavimas
Sukurti pagrindinius repozitorijos metodus duomenims gauti
Optimizuoti užklausas naudojant indeksus
Sukurti testus užklausų veikimui patikrinti
✅
Checkpoint 1.4:
Veikia efektyvios užklausos per SQLAlchemy su MySQL duomenų baze
🔄 2. Duomenų transformacijos ir inžinerija
Užduotis:
Apdoroti duomenis ir sukurti reikalingus indikatorius
2.1 Duomenų valymas
Anomalijų pašalinimas
Trūkstamų reikšmių tvarkymas
Duomenų formavimas pagal laiko intervalus (1h, 4h, 1d)
✅
Checkpoint 2.1:
Duomenys išvalyti ir standartizuoti
2.2 Techninio analizės indikatorių skaičiavimas
Moving Average (SMA, EMA) - slankieji vidurkiai
RSI (Relative Strength Index) - santykinis stiprumo indeksas
MACD (Moving Average Convergence Divergence)
Bollinger Bands - Bolingerio juostos
Volume indikatoriai (OBV, Volume MA)
✅
Checkpoint 2.2:
Techniniai indikatoriai suskaičiuoti ir patalpinti MySQL lentelėse
2.3 Pažangesnių ypatybių inžinerija
Lag features (praėjusių dienų kainos, n=1,3,7,14,30)
Trend features (krypties indikatoriai)
Sezoniniai požymiai (savaitės diena, mėnuo)
Kintamumo (volatility) indikatoriai
Koreliacija su kitais finansiniais instrumentais (jei įmanoma)
✅
Checkpoint 2.3:
Pažangesnės ypatybės sukurtos
2.4 Duomenų transformavimas modeliams
Normalizavimas/standartizavimas
One-hot encoding (kategoriniams kintamiesiems)
Target label generavimas:
Krypties prognozės (1-kils, 0-kris)
% kainos pokyčio prognozės
Train/test/validation padalinimas
✅
Checkpoint 2.4:
Duomenys paruošti modelių mokymui
🔗 3. SQLAlchemy komunikacija ir repozitorijos šablonas
Užduotis:
Užtikrinti vieningą priėjimą prie duomenų
3.1 Bazinė repozitorija
Sukurti bazinę Repository klasę su pagrindiniais CRUD metodais
Implementuoti universalų išimčių apdorojimą
Realizuoti transakciją palaikančius metodus
✅
Checkpoint 3.1:
Sukurta bazinė Repository klasė, kuri veikia su bet kokiu modeliu
3.2 Specializuotos repozitorijos
BtcPriceRepository - kainų duomenims valdyti
IndicatorRepository - techniniams indikatoriams
TradingRepository - prekybos operacijoms
PredictionRepository - prognozių rezultatams
PortfolioRepository - portfelio būsenoms
✅
Checkpoint 3.2:
Specializuotos repozitorijos su specifinėmis užklausomis veikia
3.3 Duomenų UnitOfWork šablonas
Implementuoti UnitOfWork šabloną
Sukurti transakciją palaikančius metodus
Realizuoti Dependency Injection konteinerį
✅
Checkpoint 3.3:
UnitOfWork šablonas leidžia atlikti kompleksines operacijas
3.4 Duomenų servisai
Sukurti aukštesnio lygio Data Service komponentus
Implementuoti versijų valdymą (data versioning) duomenims
Sukurti duomenų agregavimo metodus
✅
Checkpoint 3.4:
Duomenų servisai veikia ir užtikrina duomenų vientisumą
💹 4. Prekybos simuliatorius
Užduotis:
Sukurti prekybos logikos mechanizmą
4.1 Bazinė simuliatoriaus infrastruktūra
Sukurti simuliatoriaus variklio klasę
Realizuoti laiko juostos valdymą (timestamping)
Sukurti virtualaus balanso ir portfelio valdymo komponentes
Įgyvendinti įvykių registravimo (logging) sistemą
✅
Checkpoint 4.1:
Bazinė simuliatoriaus infrastruktūra veikia
4.2 Prekybos signalų generatoriai
Sukurti bazinę SignalGenerator klasę
Implementuoti konkrečius generatorius:
ModelPredictionSignalGenerator (pagal ML prognozes)
TechnicalIndicatorSignalGenerator (pagal techninius indikatorius)
HybridSignalGenerator (kombinuotas metodas)
Sukurti signalų filtravimo mechanizmą
✅
Checkpoint 4.2:
Signalų generatoriai sugeneruoja prekybos signalus
4.3 Prekybos strategijos
Sukurti bazinę TradingStrategy klasę
Implementuoti populiarias strategijas:
TrendFollowingStrategy
MeanReversionStrategy
BreakoutStrategy
MachineLearningStrategy (pagal ML modelio prognozes)
Sukurti strategijų kompoziciją
✅
Checkpoint 4.3:
Prekybos strategijos priima signalus ir generuoja sprendimus
4.4 Rizikos valdymas
Sukurti pozicijos dydžio skaičiavimo algoritmus
Implementuoti stop-loss ir take-profit logiką
Sukurti dinaminio stop-loss keitimo mechanizmą
Realizuoti trailing stop funkcionalumą
Portfelio rizikos valdymas (diversifikacija, jei simuliuojami keli instrumentai)
✅
Checkpoint 4.4:
Rizikos valdymo mechanizmai veikia simuliatoriuje
4.5 Prekybos vykdymas ir rezultatų fiksavimas
Realizuoti OrderExecutor komponentą
Sukurti komisinius mokesčius (fees) simuliuojantį mechanizmą
Implementuoti slippage (kainos praslydimai) simuliaciją
Fiksuoti visus prekybos įvykius MySQL duomenų bazėje
Skaičiuoti ir saugoti prekybos statistiką (pelnas/nuostolis, sandorio dydis, ir t.t.)
✅
Checkpoint 4.5:
Visas prekybos ciklas veikia nuo signalo iki įvykdymo ir rezultatų fiksavimo
🧑‍💻 5. Naudotojo sąsaja (UI) su Flask
Užduotis:
Sukurti patogią naudotojo sąsają
5.1 Bazinė Flask aplinka
Sukurti Flask projekto struktūrą (blueprints)
Implementuoti autentifikaciją
Sukurti pagrindinį šabloną (layout)
Realizuoti klaidų apdorojimą
Sukurti duomenų filtravimo ir validavimo mechanizmus
✅
Checkpoint 5.1:
Veikianti Flask aplikacija su autentifikacija
5.2 Duomenų vizualizacijos
Realizuoti interaktyvius kainų grafikus su Plotly/Chart.js
Sukurti techninių indikatorių vizualizacijas
Implementuoti prekybos signalų atvaizdavimą grafikuose
Sukurti portfelio vertės pokyčio vizualizacijas
Realizuoti realaus laiko duomenų atnaujinimą
✅
Checkpoint 5.2:
Interaktyvūs grafikai ir vizualizacijos veikia UI
5.3 Modelio treniravimo UI
Sukurti modelio parametrų formas
Implementuoti hiperparametrų keitimo funkcionalumą
Realizuoti modelio treniravimo proceso atvaizdavimą (progress bar)
Sukurti modelio metrikų atvaizdavimą
Treniravimo rezultatų saugojimo mechanizmas
✅
Checkpoint 5.3:
Per UI galima treniruoti modelius su skirtingais parametrais
5.4 Prognozių ir simuliacijų UI
Sukurti prognozių generavimo sąsają
Implementuoti prekybos simuliatoriaus paleidimo ir parametrų nustatymo UI
Realizuoti simuliacijos rezultatų peržiūrą
Sukurti realaus laiko prognozių ir simuliacijų stebėjimo puslapį
Įgyvendinti simuliacijų palyginimo sąsają
✅
Checkpoint 5.4:
UI leidžia paleisti prognozes ir simuliacijas, peržiūrėti rezultatus
5.5 Ataskaitų ir insights UI
Sukurti ataskaitų generavimo puslapį
Implementuoti prekybos strategijų rezultatų palyginimo lenteles
Realizuoti modelių efektyvumo palyginimo grafinius elementus
Sukurti pasirinkto laikotarpio analizės puslapį
Implementuoti user-specific ataskaitų formavimą
✅
Checkpoint 5.5:
Ataskaitų ir įžvalgų puslapiai veikia UI
📊 6. Saugojimas ir naudotojų testai
Užduotis:
Išsaugoti ir analizuoti rezultatus
6.1 Rezultatų saugojimo schema
Sukurti išplėstinę duomenų schemą rezultatams
Implementuoti skirtingas lenteles prognozėms, simuliacijoms, metrikoms
Sukurti ryšius tarp lentelių ir realizuoti užklausas pagal relationships
Optimizuoti saugojimo schemas dideliam duomenų kiekiui
✅
Checkpoint 6.1:
Duomenų bazės schema rezultatams optimizuota ir įdiegta
6.2 Naudotojų sesijų valdymas
Sukurti naudotojų sesijų lentelę MySQL
Implementuoti unikalius identifikatorius kiekvienai treniravimo/testavimo sesijai
Realizuoti metrikas pagal naudotojo profilį
Sukurti naudotojų rezultatų apsaugą (privatūs/vieši rezultatai)
✅
Checkpoint 6.2:
Naudotojų sesijos saugomos ir valdomos
6.3 Eksperimentų registravimas
Sukurti eksperimentų registro (experiment registry) sistemą
Implementuoti parametrų ir hiperparametrų sekimą
Realizuoti eksperimentų versijų kontrolę
Sukurti eksperimentų palyginimo funkcionalumą
✅
Checkpoint 6.3:
Eksperimentų registravimo sistema veikia
6.4 Rezultatų eksportavimas ir importavimas
Sukurti rezultatų eksportavimo į CSV/Excel/JSON mechanizmą
Implementuoti prognozių ir simuliacijų rezultatų importavimo logiką
Realizuoti ataskaitų generavimą į PDF formatą
Sukurti backup sistemą duomenų bazei
✅
Checkpoint 6.4:
Rezultatų eksportavimo ir importavimo funkcijos veikia
🔢 7. Paprasti ML modeliai
Užduotis:
Sukurti bazinius mašininio mokymosi modelius
7.1 Logistinė regresija
Sukurti LogisticRegression modelį krypties prognozavimui (1-kils, 0-kris)
Atlikti ypatybių (feature) atranką
Optimizuoti modelio hiperparametrus (C, solver, penalty)
Išmatuoti modelio tikslumą ir kitas metrikas
✅
Checkpoint 7.1:
Logistinės regresijos modelis treniruotas ir testuotas
7.2 Random Forest modelis
Sukurti RandomForest modelį krypties prognozavimui
Atlikti feature importance analizę
Optimizuoti hiperparametrus (n_estimators, max_depth, min_samples_split)
Palyginti su logistine regresija
✅
Checkpoint 7.2:
Random Forest modelis sukurtas ir palygintas
7.3 ARIMA/SARIMA laiko eilučių modeliai
Sukurti ARIMA/SARIMA modelį kainos prognozavimui
Atlikti stacionarumo testus ir transformacijas
Optimizuoti p, d, q parametrus
Įvertinti modelio prognozavimo tikslumą
✅
Checkpoint 7.3:
ARIMA/SARIMA modelis įgyvendintas
7.4 Gradient Boosting modeliai
Sukurti XGBoost arba LightGBM modelį
Optimizuoti hiperparametrus boosting modeliams
Palyginti su ankstesniais modeliais
Integruoti su prekybos simuliatoriumi
✅
Checkpoint 7.4:
Gradient Boosting modelis sukonfigūruotas
7.5 Modelių vertinimas prekybos simuliatoriuje
Įvertinti visų paprastų modelių efektyvumą prekybos simuliatoriuje
Sukurti benchmark sistemą modeliams lyginti
Identifikuoti geriausią paprastą modelį pagal prekybos rezultatus
Parengti detalią ataskaitą apie paprastų modelių efektyvumą
✅
Checkpoint 7.5:
Paprastų modelių prekybos rezultatai išanalizuoti ir palyginti
🧠 8. Neuroninis tinklas + palyginimas
Užduotis:
Sukurti ir palyginti pažangesnius modelius
8.1 Duomenų paruošimas neuroniniams tinklams
Sukurti specialius duomenų apdorojimo metodus NN
Implementuoti sliding window metodą sekų formavimui
Sukurti duomenų generatorius batch mokymui
Implementuoti duomenų normalizavimą/standartizavimą
✅
Checkpoint 8.1:
Duomenys paruošti specialiai neuroniniams tinklams
8.2 RNN/LSTM modelis
Sukurti bazinį RNN ar LSTM modelį su Keras/TensorFlow/PyTorch
Optimizuoti tinklo architektūrą (sluoksniai, neuronai)
Implementuoti early stopping, callback funkcijas
Išbandyti bidirectional LSTM variantus
✅
Checkpoint 8.2:
RNN/LSTM modelis sukurtas ir apmokytas
8.3 CNN modelis laiko eilutėms
Sukurti 1D-CNN modelį laiko eilučių duomenims
Optimizuoti filtrų dydžius ir skaičių
Išbandyti skirtingas pooling strategijas
Palyginti su LSTM rezultatais
✅
Checkpoint 8.3:
CNN modelis laiko eilutėms sukurtas
8.4 Transformer modelis
Sukurti Transformer architektūros modelį (Attention mechanizmas)
Implementuoti positional encoding laiko eilutėms
Optimizuoti attention heads parametrus
Palyginti su tradicinėmis RNN/LSTM architektūromis
✅
Checkpoint 8.4:
Transformer modelis įgyvendintas
8.5 Modelių ansamblis
Sukurti modelių ansamblį iš sukurtų sprendimų
Implementuoti balsavimo (voting) arba svertinius metodus
Patikrinti ansamblio efektyvumą
Palyginti su atskirais modeliais
✅
Checkpoint 8.5:
Modelių ansamblis sukurtas ir išbandytas
8.6 Modelių palyginimas pagal prekybos rezultatus
Palyginti visus modelius pagal tradicines ML metrikas (accuracy, RMSE)
Išanalizuoti modelių efektyvumą prekybos simuliatoriuje
Įvertinti rizikos/grąžos santykį kiekvienam modeliui
Sukurti detalią palyginimo ataskaitą
✅
Checkpoint 8.6:
Visų modelių prekybos rezultatai išanalizuoti ir palyginti
🔁 9. Hiperparametrų optimizavimas
Užduotis:
Optimizuoti modelių parametrus
Modelių parametrų testavimas (20-30 variantų):
Epochs, batch size, learning rate, hidden layers, dropout, optimizer ir kt.
Prekybos strategijų parametrų testavimas:
Stop-loss lygiai, take-profit ribos, pozicijos dydžio nustatymai
Visi rezultatai įrašyti į ataskaitos lentelę
✅
Checkpoint 9:
Parengta testavimo lentelė su 30+ bandymų rezultatais
📏 10. Metrikos + Grafikai
Užduotis:
Vizualizuoti ir analizuoti rezultatus
Prognozavimo metrikos: RMSE, MAE, Accuracy, Precision, Recall, F1 Score
Prekybos metrikos: ROI, Sharpe ratio, Max Drawdown, Win/Loss ratio
Grafikai:
BTC prognozė vs reali kaina
Klaidų pasiskirstymas
Prekybos simuliacijos portfelio vertės kitimas
Modelių palyginimas pagal investavimo grąžą
Vartotojo prognozių ir prekybos istorija
✅
Checkpoint 10:
Sugeneruoti prasmingi 6+ grafikai, dinamiškai naudojant matplotlib/plotly
🔍 11. Backtesting ir validacija
Užduotis:
Patikrinti modelių efektyvumą skirtingomis rinkos sąlygomis
Modelio testavimas skirtingais laikotarpiais (augimas, kritimas, šoninė rinka)
Walk-forward validacija (pastovus pertreniravimas su naujausiais duomenimis)
Prekybos rezultatų statistinė analizė
✅
Checkpoint 11:
Atliktas išsamus backtesting ir walk-forward validacija
📁 Projekto struktūra (pavyzdinė)
✅ Github reikalavimai
Būtinos šakos:
main — stabilus projektas
btc_trader/
│
├── app/ # Flask aplikacija
│ ├── routes.py # Flask maršrutai
│ ├── forms.py # Naudotojo sąsajos formos
│ └── templates/
│
├── database/ # Duomenų bazės logika
│ ├── models.py # SQLAlchemy modeliai
│ ├── db_init.py # Duomenų įkėlimas
│
├── ml_models/ # ML modeliai
│ ├── logistic.py # Paprastas modelis
│ ├── rnn_lstm.py # LSTM
│ ├── cnn.py # CNN modelis
│ └── transformer.py # Transformeris (bonusas)
│
├── trading/ # Prekybos simuliatoriaus moduliai
│ ├── simulator.py # Prekybos logika
│ ├── strategies.py # Prekybos strategijos
│ └── portfolio.py # Portfelio valdymas
│
├── preprocessing/
│ └── feature_engineering.py
│
├── notebooks/ # Jupyter eksperimentams
│
├── results/
│ ├── evaluation.csv # 30+ bandymų lentelė
│ └── trading_results.csv # Prekybos rezultatai
│
├── static/
│ └── plots/ # Sugeneruoti grafikai
│
├── config.py
├── requirements.txt
└── main.py
ml-dev — modelių kūrimas
frontend-ui — Flask UI kūrimas
trading-sim — prekybos simuliatoriaus kūrimas
Bent 7 commitai per visas šakas
✅
Checkpoint 12:
Projektas Github'e, šakos ir commitai tvarkingi
📝 Ataskaitos santrauka (trumpai)
1.
Aprašytas uždavinys: BTC kainos spėjimas ir automatinė prekyba
2.
Github nuoroda
3.
Savęs įvertinimas
4.
Darbo įspūdžiai
5.
Duomenų šaltiniai: pvz., Binance API
6.
Tikslai: sukurti 3 modelius, įvertinti, palyginti, simuliuoti prekybą
7.
Testų lentelė (30+)
8.
Prekybos simuliacijos rezultatai
9.
Pastebėjimai (kas veikė / neveikė)
10.
Išvados ir rekomendacijos



