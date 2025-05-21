
# Bitcoin Kainų Prognozavimo Modelių Prekybos Rezultatų Ataskaita

## Įvadas

Šioje ataskaitoje pateikiami įvairių mašininio mokymosi modelių, naudojamų Bitcoin kainų prognozavimui, 
prekybos simuliacijos rezultatai ir analizė. Buvo analizuojami šie modeliai:

1. Logistinė regresija
2. Random Forest
3. XGBoost
4. Buy and Hold strategija (bazinis modelis, visada spėja "kils")
5. Atsitiktinis spėjimas

## Testavimo sąlygos

- Pradinis kapitalas: $10,000
- Testavimo laikotarpis: 2024-08-22 - 2025-05-20 (272 dienos)
- Komisinis mokestis: 0.1% nuo kiekvieno sandorio vertės
- Prekybos strategija: Pirkimas, kai signalas keičiasi į "kils", pardavimas, kai signalas keičiasi į "kris"

## Pagrindiniai rezultatai

Geriausią prekybos rezultatą parodė **Atsitiktinis spėjimas** modelis:
- Galutinė portfelio vertė: $12451.13
- Bendras pelnas: $2451.13 (24.51%)
- Metinė grąža: 34.38%
- Sharpe rodiklis: 0.92

## Modelių palyginimas

| Modelis | Galutinė vertė ($) | Grąža (%) | Metinė grąža (%) | Sandorių skaičius | Sėkmingų sandorių (%) | Max drawdown (%) | Sharpe rodiklis |
|---------|-------------------|----------|-----------------|-------------------|----------------------|-----------------|----------------|
              Modelis  Galutinė vertė ($)  Grąža (%)  Metinė grąža (%)  Sandorių skaičius  Sėkmingų sandorių (%)  Max drawdown (%)  Sharpe rodiklis
Atsitiktinis spėjimas        12451.129077  24.511291         34.375780                126              52.380952         26.092565         0.915519
        Random Forest        12177.793338  21.777933         30.415184                 34              70.588235          9.300426         1.118605
  Logistinė regresija        11829.284887  18.292849         25.410076                 72              55.555556         13.376062         0.841381
              XGBoost        10563.085226   5.630852          7.662605                 24              75.000000         11.402937         0.419558
         Buy and Hold        10000.000000   0.000000          0.000000                  0               0.000000          0.000000         0.000000

## Išvados

1. **Efektyviausi modeliai:** Atsitiktinis spėjimas, Random Forest parodė geriausius rezultatus prekyboje.

2. **Tikslumas vs. Pelningumas:** Nors modelio tikslumas yra svarbus, jis ne visada tiesiogiai koreliuoja su 
   prekybos pelningumu. Atsitiktinis spėjimas modelis, kurio tikslumas buvo 0.5000, 
   generavo didžiausią grąžą.

3. **Sandorių dažnumas:** Modeliai atliko skirtingą kiekį sandorių: mažiausiai - 0, 
   daugiausiai - 126. Optimalus sandorių skaičius priklauso nuo modelio gebėjimo 
   tiksliai prognozuoti kainų pokyčius.

4. **Rizikos valdymas:** Modeliai pasižymėjo skirtingais maksimalaus nuosmukio (drawdown) rodikliais. Mažiausias drawdown
   buvo 0.00%, didžiausias - 26.09%.

5. **Palyginimas su HODL:** Mašininio mokymosi modeliai parodė geresnius rezultatus nei paprasta Buy and Hold strategija.

## Rekomendacijos

1. Tolesniam darbui rekomenduojama naudoti Atsitiktinis spėjimas modelį, kuris parodė geriausius rezultatus.
2. Verta ištirti modelių derinimo galimybes, pvz., ansamblinio mokymosi metodus.
3. Tobulinti prekybos strategiją, įvedant rizikos valdymo priemones, pvz., stop-loss ir take-profit.
4. Įtraukti daugiau išorinių kintamųjų (rinkos sentimentas, ekonominiai rodikliai), kurie galėtų pagerinti prognozes.

