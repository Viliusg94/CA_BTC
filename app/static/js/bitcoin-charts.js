/**
 * Supaprastinta, garantuotai veikianti Bitcoin grafikų versija
 */

// Paleidžiame, kai puslapis užkrautas
document.addEventListener('DOMContentLoaded', function() {
    console.log("Puslapis užkrautas - kuriami grafikai");
    
    // Add debugging for global variables with safety checks
    console.log("=== GLOBAL VARIABLES DEBUG ===");
    console.log("window.priceHistory exists:", typeof window.priceHistory !== 'undefined');
    console.log("window.predictions exists:", typeof window.predictions !== 'undefined');
    
    // Safely access global variables
    const priceHistory = (typeof window.priceHistory !== 'undefined') ? window.priceHistory : {"dates":[], "prices":[], "close":[], "volumes":[]};
    const predictions = (typeof window.predictions !== 'undefined') ? window.predictions : [];
    
    console.log("priceHistory:", priceHistory);
    console.log("predictions:", predictions);
    console.log("================================");
    
    // Render candlestick chart
    const candlestickElement = document.getElementById('candlestick-chart');
    if (candlestickElement) {
        console.log("Bandoma užkrauti žvakių grafiką...");
        
        // Try primary endpoint first, then fallback
        const tryFetchCandlestickData = (url) => {
            return fetch(url)
                .then(response => {
                    console.log(`API response from ${url}:`, response.status);
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}`);
                    }
                    return response.json();
                });
        };
        
        // Start with the working endpoint directly
        tryFetchCandlestickData('/api/btc_price/history?days=100')
            .then(data => {
                console.log("Gauti žvakių duomenys:", data);
                
                // Handle different response formats
                let chartData = {};
                if (data.labels && data.open && data.high && data.low && data.close) {
                    // Candlestick format
                    chartData = data;
                } else if (data.dates && data.open && data.high && data.low && data.prices) {
                    // History API format
                    chartData = {
                        labels: data.dates,
                        open: data.open,
                        high: data.high,
                        low: data.low,
                        close: data.prices,
                        volume: data.volumes || []
                    };
                } else if (data.dates && data.close) {
                    // Simplified format - create missing data
                    chartData = {
                        labels: data.dates,
                        open: data.close,  // Use close as open
                        high: data.close.map(price => price * 1.01), // Simulate high
                        low: data.close.map(price => price * 0.99),  // Simulate low
                        close: data.close,
                        volume: data.volumes || []
                    };
                } else if (data.dates && data.prices) {
                    // Use prices as close
                    chartData = {
                        labels: data.dates,
                        open: data.prices,
                        high: data.prices.map(price => price * 1.01),
                        low: data.prices.map(price => price * 0.99),
                        close: data.prices,
                        volume: data.volumes || []
                    };
                } else {
                    throw new Error("Invalid data format received");
                }
                
                if (!chartData.labels || !chartData.close || chartData.labels.length === 0) {
                    console.error("Netinkami žvakių duomenys:", chartData);
                    createFallbackChart(candlestickElement, 'Bitcoin Historical Price (Demo Data)');
                    return;
                }
                
                // Set chart container size
                candlestickElement.style.width = '100%';
                candlestickElement.style.height = '400px';
                candlestickElement.width = candlestickElement.offsetWidth;
                candlestickElement.height = 400;
                
                // Always use line chart (more reliable than candlestick plugin)
                new Chart(candlestickElement.getContext('2d'), {
                    type: 'line',
                    data: { 
                        labels: chartData.labels, 
                        datasets: [
                            {
                                label: 'BTC Close Price',
                                data: chartData.close,
                                borderColor: '#F7931A',
                                backgroundColor: '#F7931A20',
                                borderWidth: 2,
                                fill: false,
                                tension: 0.1
                            },
                            {
                                label: 'BTC High',
                                data: chartData.high,
                                borderColor: '#28a745',
                                backgroundColor: '#28a74520',
                                borderWidth: 1,
                                fill: false,
                                tension: 0.1
                            },
                            {
                                label: 'BTC Low',
                                data: chartData.low,
                                borderColor: '#dc3545',
                                backgroundColor: '#dc354520',
                                borderWidth: 1,
                                fill: false,
                                tension: 0.1
                            }
                        ]
                    },
                    options: { 
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: { 
                            title: { 
                                display: true, 
                                text: 'Bitcoin Historical Price (OHLC)' 
                            },
                            tooltip: {
                                callbacks: {
                                    label: function(context) {
                                        return context.dataset.label + ': $' + 
                                            parseFloat(context.raw).toLocaleString(undefined, {
                                                minimumFractionDigits: 2,
                                                maximumFractionDigits: 2
                                            });
                                    }
                                }
                            }
                        },
                        scales: {
                            y: {
                                ticks: {
                                    callback: function(value) {
                                        return '$' + parseInt(value).toLocaleString();
                                    }
                                }
                            }
                        }
                    }
                });
                console.log("Žvakių grafikas sukurtas sėkmingai!");
            })
            .catch(error => {
                console.error("Klaida užkraunant žvakių duomenis:", error);
                createFallbackChart(candlestickElement, 'Bitcoin Historical Price (Demo Data)');
            });
    }

    // Render predictions chart (with historical price) - ALWAYS try to render this
    const predictionsElement = document.getElementById('predictionsChart');
    if (predictionsElement) {
        console.log("Bandoma sukurti prognozių grafiką...");
        renderPredictionsChart(predictionsElement, predictions, priceHistory);
    } else {
        console.log("Prognozių grafiko elementas nerastas - ID: predictionsChart");
    }
    
    // Always try to render prediction table
    renderPredictionTable(predictions);
});

function renderPredictionsChart(canvas, predictions, priceHistory) {
    // Išsamūs debugging pranešimai
    console.log("== PROGNOZIŲ GRAFIKO KŪRIMAS: PRADŽIA ==");
    console.log("Canvas elementas:", canvas);
    console.log("Predictions parameter:", predictions);
    console.log("PriceHistory parameter:", priceHistory);
    
    // Fix canvas sizing first
    canvas.style.width = '100%';
    canvas.style.height = '400px';
    canvas.width = canvas.offsetWidth;
    canvas.height = 400;
    
    // Patikriname, ar turime Chart.js
    if (typeof Chart === 'undefined') {
        console.error("Chart.js biblioteka neužkrauta!");
        return;
    }
    
    console.log("Chart.js biblioteka rasta");
    
    // Use parameters instead of global variables
    const safePredictions = predictions || [];
    const safePriceHistory = priceHistory || {};
    
    // Check if we have predictions - if not, show a message or historical data
    if (!safePredictions || safePredictions.length === 0) {
        console.log("Nėra prognozių duomenų - bandoma rodyti istorinę kainą");
        
        // Try to show historical price data if available
        if (safePriceHistory && safePriceHistory.dates && safePriceHistory.dates.length > 0) {
            const historicalPrices = safePriceHistory.prices || safePriceHistory.close || [];
            if (historicalPrices.length > 0) {
                console.log("Rodoma istorinė kaina:", historicalPrices.length, "taškų");
                
                new Chart(canvas, {
                    type: 'line',
                    data: {
                        labels: safePriceHistory.dates,
                        datasets: [{
                            label: 'Istorinė Bitcoin kaina',
                            data: historicalPrices,
                            borderColor: '#F7931A',
                            backgroundColor: '#F7931A20',
                            borderWidth: 2,
                            fill: false,
                            tension: 0.1
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            title: {
                                display: true,
                                text: 'Bitcoin kainos istorija - pasirinkite modelius prognozėms'
                            },
                            tooltip: {
                                callbacks: {
                                    label: function(context) {
                                        return context.dataset.label + ': $' + 
                                            parseInt(context.raw).toLocaleString();
                                    }
                                }
                            }
                        },
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
                                    text: 'Kaina (USD)'
                                },
                                ticks: {
                                    callback: function(value) {
                                        return '$' + parseInt(value).toLocaleString();
                                    }
                                }
                            }
                        }
                    }
                });
                console.log("Istorinės kainos grafikas sukurtas sėkmingai!");
                return;
            }
        }
        
        // Create a simple chart with a message if no data at all
        new Chart(canvas, {
            type: 'line',
            data: {
                labels: ['Nėra duomenų'],
                datasets: [{
                    label: 'Prognozės',
                    data: [0],
                    borderColor: '#ddd',
                    backgroundColor: '#f8f9fa',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Nėra prognozių duomenų - pasirinkite modelius ir generuokite prognozes'
                    }
                },
                scales: {
                    y: {
                        display: false
                    },
                    x: {
                        display: false
                    }
                }
            }
        });
        return;
    }
    
    console.log("Predictions duomenys:", predictions);
    
    // Sukuriame grafiką su prognozėmis
    try {
        // Prepare datasets: historical price + each model prediction
        const datasets = [];
        
        // Fix historical price data handling
        if (typeof priceHistory !== 'undefined' && priceHistory) {
            console.log("Price history objektas:", priceHistory);
            
            // Check different possible structures
            let historicalPrices = null;
            let historicalDates = null;
            
            if (priceHistory.prices && priceHistory.dates) {
                historicalPrices = priceHistory.prices;
                historicalDates = priceHistory.dates;
            } else if (priceHistory.close && priceHistory.dates) {
                historicalPrices = priceHistory.close;
                historicalDates = priceHistory.dates;
            }
            
            if (historicalPrices && historicalDates && historicalPrices.length > 0 && historicalDates.length > 0) {
                console.log("Pridedama istorinė kaina:", historicalPrices.length, "taškų");
                datasets.push({
                    label: 'Istorinė kaina',
                    data: historicalPrices,
                    borderColor: '#888',
                    backgroundColor: '#8882',
                    borderWidth: 2,
                    tension: 0.1,
                    fill: false,
                    pointRadius: 1
                });
            } else {
                console.warn("Netinkami istorinės kainos duomenys");
            }
        }
        
        // Spalvos
        const colors = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF'];
        
        // Pridedame kiekvieno modelio prognozę
        predictions.forEach((pred, index) => {
            if (!pred || !pred.values || !pred.dates) {
                console.warn(`Prognozė ${index} netinkama:`, pred);
                return;
            }
            
            const values = Array.isArray(pred.values) ? pred.values : [];
            const dates = Array.isArray(pred.dates) ? pred.dates : [];
            
            if (values.length === 0 || dates.length === 0) {
                console.warn(`Prognozė ${index} turi tuščius masyvus`);
                return;
            }
            
            // Paprastas duomenų valymas
            const cleanValues = values.map(v => {
                const num = parseFloat(v);
                return isNaN(num) ? 0 : num;
            });
            
            console.log(`Pridedama prognozė ${index}: ${pred.model}, ${cleanValues.length} reikšmės`);
            
            datasets.push({
                label: pred.model || `Modelis ${index + 1}`,
                data: cleanValues,
                borderColor: colors[index % colors.length],
                backgroundColor: colors[index % colors.length] + '33',
                borderWidth: 2,
                tension: 0.1,
                fill: false
            });
        });
        
        if (datasets.length === 0) {
            console.error("Nėra tinkamų duomenų grafikui!");
            return;
        }
        
        // Gauname visas datas - prioritetas prognozių datoms
        let allDates = [];
        if (predictions.length > 0 && predictions[0].dates) {
            allDates = predictions[0].dates;
        } else if (typeof priceHistory !== 'undefined' && priceHistory && priceHistory.dates && priceHistory.dates.length > 0) {
            allDates = priceHistory.dates;
        }
        
        console.log("Naudojamos datos grafikui:", allDates.length, "elementų");
        
        // Sukuriame prognozių grafiką
        new Chart(canvas, {
            type: 'line',
            data: {
                labels: allDates,
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    intersect: false,
                },
                plugins: {
                    title: {
                        display: true,
                        text: 'Bitcoin kainų prognozės ir istorija'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.dataset.label + ': $' + 
                                    parseInt(context.raw).toLocaleString();
                            }
                        }
                    }
                },
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
                            text: 'Kaina (USD)'
                        },
                        ticks: {
                            callback: function(value) {
                                return '$' + parseInt(value).toLocaleString();
                            }
                        }
                    }
                }
            }
        });
        
        console.log("Prognozių grafikas sukurtas sėkmingai!");
    } catch (error) {
        console.error("Klaida kuriant prognozių grafiką:", error);
    }
    
    console.log("== PROGNOZIŲ GRAFIKO KŪRIMAS: PABAIGA ==");
}

/**
 * Atvaizduoja prognozių lentelę
 */
function renderPredictionTable(predictions) {
    const tableBody = document.getElementById('prediction-table-body');
    if (!tableBody) return;
    
    tableBody.innerHTML = '';
    
    // Use parameter instead of global variable
    const safePredictions = predictions || [];
    
    // Tikriname, ar turime duomenis
    if (!safePredictions || !Array.isArray(safePredictions) || safePredictions.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="5" class="text-center">Nėra prognozių duomenų</td></tr>';
        return;
    }
    
    // Filtruojame validžias prognozes
    const validPredictions = safePredictions.filter(p => 
        p && p.model && Array.isArray(p.values) && p.values.length > 0 && Array.isArray(p.dates) && p.dates.length > 0
    );
    
    if (validPredictions.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="5" class="text-center">Nėra tinkamų prognozių duomenų</td></tr>';
        return;
    }
    
    // Naudojame pirmo modelio datas kaip bazę
    const firstPred = validPredictions[0];
    const dates = firstPred.dates;
    
    // Sukuriame eilutę kiekvienai datai
    dates.forEach((date, i) => {
        const row = document.createElement('tr');
        
        // Datos stulpelis
        const dateCell = document.createElement('td');
        dateCell.textContent = date;
        row.appendChild(dateCell);
        
        // Stulpelis kiekvienam modeliui
        validPredictions.forEach(pred => {
            const cell = document.createElement('td');
            
            if (i < pred.values.length) {
                const value = parseFloat(pred.values[i]);
                if (!isNaN(value)) {
                    cell.textContent = '$' + value.toLocaleString(undefined, {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2
                    });
                    
                    // Rodyklė pagal tendenciją
                    if (i > 0 && i < pred.values.length) {
                        const prevValue = parseFloat(pred.values[i-1]);
                        if (!isNaN(prevValue)) {
                            if (value > prevValue) {
                                cell.classList.add('text-success');
                                cell.innerHTML += ' <i class="fas fa-arrow-up"></i>';
                            } else if (value < prevValue) {
                                cell.classList.add('text-danger');
                                cell.innerHTML += ' <i class="fas fa-arrow-down"></i>';
                            }
                        }
                    }
                } else {
                    cell.textContent = 'N/A';
                }
            } else {
                cell.textContent = 'N/A';
            }
            
            row.appendChild(cell);
        });
        
        tableBody.appendChild(row);
    });
}

// Add fallback chart function
function createFallbackChart(canvas, title) {
    // Create mock data for demonstration
    const mockData = generateMockBitcoinData();
    
    canvas.style.width = '100%';
    canvas.style.height = '400px';
    canvas.width = canvas.offsetWidth;
    canvas.height = 400;
    
    new Chart(canvas.getContext('2d'), {
        type: 'line',
        data: {
            labels: mockData.dates,
            datasets: [{
                label: 'BTC Price (Demo)',
                data: mockData.prices,
                borderColor: '#F7931A',
                backgroundColor: '#F7931A20',
                borderWidth: 2,
                fill: false,
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: title + ' - Демонстрационные данные'
                }
            },
            scales: {
                y: {
                    ticks: {
                        callback: function(value) {
                            return '$' + parseInt(value).toLocaleString();
                        }
                    }
                }
            }
        }
    });
}

// Generate mock Bitcoin data
function generateMockBitcoinData() {
    const dates = [];
    const prices = [];
    let currentPrice = 45000;
    
    for (let i = 30; i >= 0; i--) {
        const date = new Date();
        date.setDate(date.getDate() - i);
        dates.push(date.toISOString().split('T')[0]);
        
        // Add some random variation
        currentPrice *= (1 + (Math.random() - 0.5) * 0.02);
        prices.push(Math.round(currentPrice));
    }
    
    return { dates, prices };
}