// Grafikų inicializavimo ir valdymo JavaScript failas

// Grafikų objektai
let priceChart = null;
let volumeChart = null;
let macdChart = null;
let portfolioChart = null;

// Periodinis atnaujinimas
let updateInterval = null;

// Grafikų spalvos
const chartColors = {
    price: 'rgb(54, 162, 235)',
    volume: 'rgb(75, 192, 192)',
    sma20: 'rgb(255, 159, 64)',
    sma50: 'rgb(153, 102, 255)',
    macd: 'rgb(54, 162, 235)',
    signal: 'rgb(255, 99, 132)',
    portfolio: 'rgb(75, 192, 192)',
    btc: 'rgb(255, 159, 64)',
    cash: 'rgb(153, 102, 255)',
    buySignal: 'rgb(75, 192, 192)',
    sellSignal: 'rgb(255, 99, 132)'
};

// Inicializuoja grafikų atvaizdavimą
function initCharts() {
    // Inicializuojame kainos grafiką
    initPriceChart();
    
    // Inicializuojame apyvartų grafiką
    initVolumeChart();
    
    // Inicializuojame MACD grafiką
    initMacdChart();
    
    // Inicializuojame portfelio grafiką
    initPortfolioChart();
    
    // Pradedame periodinį atnaujinimą (kas 30 sekundžių)
    startAutoUpdate();
}

// Inicializuoja kainos grafiką
function initPriceChart() {
    const ctx = document.getElementById('priceChart').getContext('2d');
    
    // Sukuriame grafiką
    priceChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'BTC kaina',
                    data: [],
                    borderColor: chartColors.price,
                    backgroundColor: 'rgba(54, 162, 235, 0.1)',
                    borderWidth: 2,
                    tension: 0.1,
                    pointRadius: 1,
                    fill: true
                },
                {
                    label: 'SMA 20',
                    data: [],
                    borderColor: chartColors.sma20,
                    borderWidth: 1.5,
                    tension: 0.1,
                    pointRadius: 0,
                    fill: false
                },
                {
                    label: 'SMA 50',
                    data: [],
                    borderColor: chartColors.sma50,
                    borderWidth: 1.5,
                    tension: 0.1,
                    pointRadius: 0,
                    fill: false
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Laikas'
                    }
                },
                y: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Kaina (EUR)'
                    }
                }
            },
            plugins: {
                tooltip: {
                    mode: 'index',
                    intersect: false
                },
                legend: {
                    position: 'top',
                },
                title: {
                    display: true,
                    text: 'BTC kaina ir slenkantys vidurkiai'
                }
            }
        }
    });
}

// Inicializuoja apyvartų grafiką
function initVolumeChart() {
    const ctx = document.getElementById('volumeChart').getContext('2d');
    
    // Sukuriame grafiką
    volumeChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Apyvarta',
                    data: [],
                    backgroundColor: chartColors.volume,
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Laikas'
                    }
                },
                y: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Apyvarta'
                    }
                }
            },
            plugins: {
                tooltip: {
                    mode: 'index',
                    intersect: false
                },
                legend: {
                    position: 'top',
                },
                title: {
                    display: true,
                    text: 'Prekybos apyvarta'
                }
            }
        }
    });
}

// Inicializuoja MACD grafiką
function initMacdChart() {
    const ctx = document.getElementById('macdChart').getContext('2d');
    
    // Sukuriame grafiką
    macdChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'MACD',
                    data: [],
                    borderColor: chartColors.macd,
                    backgroundColor: 'rgba(54, 162, 235, 0.1)',
                    borderWidth: 2,
                    tension: 0.1,
                    pointRadius: 0,
                    fill: false
                },
                {
                    label: 'Signalo linija',
                    data: [],
                    borderColor: chartColors.signal,
                    borderWidth: 1.5,
                    tension: 0.1,
                    pointRadius: 0,
                    fill: false
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Laikas'
                    }
                },
                y: {
                    display: true,
                    title: {
                        display: true,
                        text: 'MACD'
                    }
                }
            },
            plugins: {
                tooltip: {
                    mode: 'index',
                    intersect: false
                },
                legend: {
                    position: 'top',
                },
                title: {
                    display: true,
                    text: 'MACD indikatorius'
                }
            }
        }
    });
}

// Inicializuoja portfelio grafiką
function initPortfolioChart() {
    const ctx = document.getElementById('portfolioChart').getContext('2d');
    
    // Sukuriame grafiką
    portfolioChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Portfelio vertė',
                    data: [],
                    borderColor: chartColors.portfolio,
                    backgroundColor: 'rgba(75, 192, 192, 0.1)',
                    borderWidth: 2,
                    tension: 0.1,
                    pointRadius: 1,
                    fill: true
                },
                {
                    label: 'BTC vertė',
                    data: [],
                    borderColor: chartColors.btc,
                    borderWidth: 1.5,
                    tension: 0.1,
                    pointRadius: 0,
                    fill: false
                },
                {
                    label: 'Grynieji pinigai',
                    data: [],
                    borderColor: chartColors.cash,
                    borderWidth: 1.5,
                    tension: 0.1,
                    pointRadius: 0,
                    fill: false
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Data'
                    }
                },
                y: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Vertė (EUR)'
                    }
                }
            },
            plugins: {
                tooltip: {
                    mode: 'index',
                    intersect: false
                },
                legend: {
                    position: 'top',
                },
                title: {
                    display: true,
                    text: 'Portfelio vertės istorija'
                }
            }
        }
    });
}

// Gauna duomenis ir atnaujina grafikų
function updateCharts() {
    // Gauname kainos duomenis
    fetch('/trading/api/price-data?interval=1h&limit=100')
        .then(response => response.json())
        .then(data => {
            // Atnaujiname kainų grafiką
            updatePriceChart(data);
            
            // Atnaujiname apyvartų grafiką
            updateVolumeChart(data);
            
            // Atnaujiname MACD grafiką
            updateMacdChart(data);
            
            // Atnaujiname prekybos signalus
            drawTradingSignals(data);
        })
        .catch(error => console.error('Klaida gaunant kainos duomenis:', error));
    
    // Gauname portfelio duomenis
    fetch('/trading/api/portfolio-history?days=30')
        .then(response => response.json())
        .then(data => {
            // Atnaujiname portfelio grafiką
            updatePortfolioChart(data);
        })
        .catch(error => console.error('Klaida gaunant portfelio duomenis:', error));
}

// Atnaujina kainos grafiką
function updatePriceChart(data) {
    if (!priceChart) return;
    
    // Atnaujiname duomenis
    priceChart.data.labels = data.labels;
    priceChart.data.datasets[0].data = data.prices;
    priceChart.data.datasets[1].data = data.sma20;
    priceChart.data.datasets[2].data = data.sma50;
    
    // Atnaujiname grafiką
    priceChart.update();
}

// Atnaujina apyvartų grafiką
function updateVolumeChart(data) {
    if (!volumeChart) return;
    
    // Atnaujiname duomenis
    volumeChart.data.labels = data.labels;
    volumeChart.data.datasets[0].data = data.volumes;
    
    // Atnaujiname grafiką
    volumeChart.update();
}

// Atnaujina MACD grafiką
function updateMacdChart(data) {
    if (!macdChart) return;
    
    // Atnaujiname duomenis
    macdChart.data.labels = data.labels;
    macdChart.data.datasets[0].data = data.macd;
    macdChart.data.datasets[1].data = data.signal;
    
    // Atnaujiname grafiką
    macdChart.update();
}

// Atnaujina portfelio grafiką
function updatePortfolioChart(data) {
    if (!portfolioChart) return;
    
    // Atnaujiname duomenis
    portfolioChart.data.labels = data.labels;
    portfolioChart.data.datasets[0].data = data.portfolio;
    
    // Konvertuojame BTC į EUR (pavyzdinis kursas 50000)
    const btcInEur = data.btc.map(amount => amount * 50000);
    portfolioChart.data.datasets[1].data = btcInEur;
    
    portfolioChart.data.datasets[2].data = data.cash;
    
    // Atnaujiname grafiką
    portfolioChart.update();
}

// Piešia prekybos signalus
function drawTradingSignals(data) {
    if (!priceChart) return;
    
    // Pašaliname ankstesnius signalus
    removeTradingSignalsFromChart();
    
    // Pridedame pirkimo signalus
    const buySignals = data.buySignals;
    for (const date in buySignals) {
        const index = data.labels.indexOf(date);
        if (index !== -1) {
            addBuySignalToChart(index, buySignals[date]);
        }
    }
    
    // Pridedame pardavimo signalus
    const sellSignals = data.sellSignals;
    for (const date in sellSignals) {
        const index = data.labels.indexOf(date);
        if (index !== -1) {
            addSellSignalToChart(index, sellSignals[date]);
        }
    }
    
    // Atnaujiname grafiką
    priceChart.update();
}

// Pašalina prekybos signalus iš grafiko
function removeTradingSignalsFromChart() {
    if (!priceChart) return;
    
    // Pašaliname signalų datasets
    priceChart.data.datasets = priceChart.data.datasets.filter(dataset => 
        dataset.label !== 'Pirkimo signalai' && dataset.label !== 'Pardavimo signalai'
    );
}

// Prideda pirkimo signalus į grafiką
function addBuySignalToChart(index, price) {
    if (!priceChart) return;
    
    // Ieškome ar jau yra pirkimo signalų dataset
    let buySignalDataset = priceChart.data.datasets.find(dataset => dataset.label === 'Pirkimo signalai');
    
    // Jei nėra, sukuriame
    if (!buySignalDataset) {
        buySignalDataset = {
            label: 'Pirkimo signalai',
            data: Array(priceChart.data.labels.length).fill(null),
            backgroundColor: chartColors.buySignal,
            pointRadius: 5,
            pointStyle: 'triangle',
            showLine: false
        };
        priceChart.data.datasets.push(buySignalDataset);
    }
    
    // Pridedame signalą
    buySignalDataset.data[index] = price;
}

// Prideda pardavimo signalus į grafiką
function addSellSignalToChart(index, price) {
    if (!priceChart) return;
    
    // Ieškome ar jau yra pardavimo signalų dataset
    let sellSignalDataset = priceChart.data.datasets.find(dataset => dataset.label === 'Pardavimo signalai');
    
    // Jei nėra, sukuriame
    if (!sellSignalDataset) {
        sellSignalDataset = {
            label: 'Pardavimo signalai',
            data: Array(priceChart.data.labels.length).fill(null),
            backgroundColor: chartColors.sellSignal,
            pointRadius: 5,
            pointStyle: 'triangle',
            rotation: 180,
            showLine: false
        };
        priceChart.data.datasets.push(sellSignalDataset);
    }
    
    // Pridedame signalą
    sellSignalDataset.data[index] = price;
}

// Pradeda periodinį grafikų atnaujinimą
function startAutoUpdate() {
    // Sustabdome ankstesnį jei buvo
    stopAutoUpdate();
    
    // Iš karto atnaujiname
    updateCharts();
    
    // Nustatome periodinį atnaujinimą
    updateInterval = setInterval(updateCharts, 30000); // kas 30 sekundžių
}

// Sustabdo periodinį grafikų atnaujinimą
function stopAutoUpdate() {
    if (updateInterval) {
        clearInterval(updateInterval);
        updateInterval = null;
    }
}

// Užregistruokite anotacijų įskiepį, jei jis egzistuoja
if (typeof ChartAnnotation !== 'undefined') {
    Chart.register(ChartAnnotation);
} else {
    console.warn('ChartAnnotation nerastas! Anotacijos grafikuose nebus rodomos.');
}

/**
 * Atvaizduoja Bitcoin kainos grafiką
 * @param {Object} priceHistory - Kainos istorijos duomenys
 * @param {Object} predictions - Prognozių duomenys
 */
function renderPriceChart(priceHistory, predictions) {
    console.log("Piešiamas Bitcoin kainos grafikas");
    
    // Gauname kontekstą
    const ctx = document.getElementById('price-chart').getContext('2d');
    
    // Tikriname, ar turime duomenis
    if (!priceHistory || !priceHistory.dates || !priceHistory.close || 
        priceHistory.dates.length === 0 || priceHistory.close.length === 0) {
        console.error('Trūksta kainos istorijos duomenų');
        return;
    }
    
    // Sukuriame datasets
    const datasets = [
        {
            label: 'Bitcoin kaina (USD)',
            data: priceHistory.close,
            borderColor: 'rgb(75, 192, 192)',
            tension: 0.1,
            fill: false
        }
    ];
    
    // Jei yra prognozių, pridedame jas prie grafiko
    if (predictions && predictions.values && predictions.values.length > 0) {
        // Paskutinė reali kaina
        const lastRealPrice = priceHistory.close[priceHistory.close.length - 1];
        
        // Visos reikšmės prognozės grafikui (paskutinė reali + prognozuojamos)
        const predictionData = [lastRealPrice, ...predictions.values];
        
        // Datos prognozių grafikui (paskutinė reali data + prognozių datos)
        const predictionDates = [
            priceHistory.dates[priceHistory.dates.length - 1], 
            ...predictions.dates
        ];
        
        // Pridedame prognozių dataset
        datasets.push({
            label: 'Prognozė',
            data: predictionData,
            borderColor: 'rgb(255, 99, 132)',
            borderDash: [5, 5],
            tension: 0.1,
            fill: false
        });
    }
    
    // Sukuriame grafiką
    window.priceChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: priceHistory.dates,
            datasets: datasets
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Bitcoin kainos istorija ir prognozė'
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                }
            },
            scales: {
                y: {
                    title: {
                        display: true,
                        text: 'Kaina (USD)'
                    },
                    beginAtZero: false
                }
            }
        }
    });
}

// Inicializuojame, kai dokumentas užkrautas
document.addEventListener('DOMContentLoaded', function() {
    // Tikriname ar yra grafikų elementai
    if (document.getElementById('priceChart') &&
        document.getElementById('volumeChart') &&
        document.getElementById('macdChart') &&
        document.getElementById('portfolioChart')) {
        // Inicializuojame grafikus
        initCharts();
    }
    
    console.log('Puslapis užkrautas, piešiamas grafikas');
    
    // Atvaizduojame grafiką
    renderPriceChart(priceHistory, predictions);
});

// Patikrinkite, ar duomenys turi reikiamus laukus
if (trainingData.length > 0 && !trainingData[0].hasOwnProperty('loss')) {
    console.error('Neteisingas duomenų formatas - trūksta metrikų laukų!');
    return;
}

/**
 * Siunčia užklausą modelio apmokymui ir prognozavimui
 */
function trainModel() {
    // Rodome pranešimą apie apmokymo pradžią
    document.getElementById('training-status').textContent = 'Vyksta apmokymas...';
    
    console.log("Siunčiama POST užklausa į /predict");
    
    // Siunčiame užklausą
    fetch('/predict', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({})  // Tuščias JSON objektas
    })
    .then(response => {
        console.log("Gautas atsakymas:", response.status);
        if (!response.ok) {
            throw new Error('API atsakymas ne OK: ' + response.status);
        }
        return response.json();
    })
    .then(data => {
        console.log("Gauti duomenys:", data);
        if (data.status === 'success') {
            document.getElementById('training-status').textContent = 'Apmokymas baigtas sėkmingai!';
            
            // Atnaujiname grafiką su naujomis prognozėmis
            if (data.predictions) {
                // Jei turime globalią priceHistory ir window.priceChart
                if (window.priceHistory && window.priceChart) {
                    // Naujos prognozės
                    const newPredictions = data.predictions;
                    
                    // Sunaikinti esamą grafiką
                    window.priceChart.destroy();
                    
                    // Atvaizduojame naują grafiką su naujomis prognozėmis
                    renderPriceChart(window.priceHistory, newPredictions);
                }
            }
        } else {
            document.getElementById('training-status').textContent = 'Klaida: ' + data.message;
        }
    })
    .catch(error => {
        console.error('Klaida apmokant modelį:', error);
        document.getElementById('training-status').textContent = 'Klaida siunčiant užklausą.';
    });
}

// Kitos funkcijos lieka tos pačios