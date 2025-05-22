// Bitcoin kainų prognozių grafiko funkcijos

/**
 * Atvaizduoja Bitcoin kainos grafiką
 * @param {Object} priceHistory - Kainos istorijos duomenys
 * @param {Object} predictions - Prognozių duomenys
 */
function renderPriceChart(priceHistory, predictions) {
    console.log("Piešiamas grafikas su duomenimis:", { priceHistory, predictions });
    
    // Gauname kontekstą
    const ctx = document.getElementById('price-chart').getContext('2d');
    
    // Jei jau yra sukurtas grafikas, jį sunaikiname
    if (window.priceChart) {
        window.priceChart.destroy();
    }
    
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
            label: 'LSTM Prognozė',
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
                    text: 'Bitcoin kainos istorija ir LSTM prognozė'
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

/**
 * Atnaujina realaus laiko BTC kainą
 */
function updateLivePrice() {
    fetch('/api/btc_price/current')
        .then(response => {
            if (!response.ok) {
                throw new Error('API atsakymas ne OK');
            }
            return response.json();
        })
        .then(data => {
            if (data.price) {
                // Formatuojame kainą su dviem skaičiais po kablelio
                const formattedPrice = parseFloat(data.price).toFixed(2);
                
                // Atnaujiname kainą ir atnaujinimo laiką
                document.getElementById('btc-price').textContent = '$' + formattedPrice;
                document.getElementById('price-update-time').textContent = new Date().toLocaleString();
            }
        })
        .catch(error => console.error('Klaida gaunant realaus laiko kainą:', error));
}

// Inicializuojame puslapį, kai jis pilnai užkrautas
document.addEventListener('DOMContentLoaded', function() {
    console.log('Puslapis užkrautas, pradedame inicializaciją');
    
    // Išsaugome pradinius duomenis globaliai
    window.priceHistory = priceHistory;
    window.predictions = predictions;
    
    console.log("Pradiniai duomenys:", { priceHistory, predictions });
    
    // Atvaizduojame grafiką
    renderPriceChart(priceHistory, predictions);
    
    // Iškart atnaujiname kainą
    updateLivePrice();
    
    // Nustatome periodinį atnaujinimą
    setInterval(updateLivePrice, 60000);
    
    // Pastaba: JavaScript event listener mygtukui nebenaudojamas, nes dabar naudojame HTML formą
});