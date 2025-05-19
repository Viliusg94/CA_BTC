// filepath: d:\CA_BTC\app\static\js\model_comparison.js
// Modelių palyginimo JavaScript kodas

// Grafikų objektai
let accuracyChart = null;
let lossChart = null;

// Modelių duomenys
let modelsData = [];

// Spalvų masyvas skirtingiems modeliams
const chartColors = [
    'rgb(54, 162, 235)',
    'rgb(255, 99, 132)',
    'rgb(75, 192, 192)',
    'rgb(255, 159, 64)',
    'rgb(153, 102, 255)',
    'rgb(255, 205, 86)',
    'rgb(201, 203, 207)',
    'rgb(60, 179, 113)',
    'rgb(106, 90, 205)',
    'rgb(220, 20, 60)'
];

// Inicializuojame puslapį kai jis užkraunamas
document.addEventListener('DOMContentLoaded', function() {
    // Modelių palyginimo mygtukas
    const compareBtn = document.getElementById('compare-btn');
    compareBtn.addEventListener('click', compareModels);
});

// Palygina pasirinktus modelius
function compareModels() {
    // Gauname visus pažymėtus modelius
    const selectedModels = document.querySelectorAll('.model-checkbox:checked');
    
    // Tikriname ar bent 2 modeliai pasirinkti
    if (selectedModels.length < 2) {
        document.getElementById('no-models-selected').style.display = 'block';
        document.getElementById('comparison-results').style.display = 'none';
        return;
    }
    
    // Pašaliname įspėjimą
    document.getElementById('no-models-selected').style.display = 'none';
    
    // Rodome krovimo indikatorių
    document.getElementById('loading-indicator').style.display = 'block';
    document.getElementById('comparison-results').style.display = 'none';
    
    // Konstruojame URL su pasirinktais modeliais
    const modelIds = Array.from(selectedModels).map(checkbox => checkbox.value);
    
    // Išvalome esamus duomenis
    modelsData = [];
    
    // Gauname kiekvieno modelio metrikas
    Promise.all(modelIds.map(modelId => 
        fetch(`/models/api/models/${modelId}/metrics`)
            .then(response => response.json())
            .then(metrics => {
                // Gauname modelio struktūrą, kad gautume papildomą informaciją
                return fetch(`/models/api/models/${modelId}/structure`)
                    .then(response => response.json())
                    .then(structure => {
                        return {
                            id: modelId,
                            metrics: metrics,
                            structure: structure
                        };
                    });
            })
            .catch(error => {
                console.error(`Klaida gaunant duomenis modeliui ${modelId}:`, error);
                return null;
            })
    ))
    .then(results => {
        // Išmetame null reikšmes (jei buvo klaidų)
        modelsData = results.filter(result => result !== null);
        
        // Paslepiame krovimo indikatorių
        document.getElementById('loading-indicator').style.display = 'none';
        
        // Jei yra bent 2 modeliai, rodome palyginimą
        if (modelsData.length >= 2) {
            // Atvaizduojame palyginimo rezultatus
            displayComparisonResults(modelsData);
        } else {
            // Rodome klaidą
            document.getElementById('no-models-selected').textContent = 'Nepavyko gauti modelių duomenų palyginimui.';
            document.getElementById('no-models-selected').style.display = 'block';
        }
    })
    .catch(error => {
        console.error('Klaida lyginant modelius:', error);
        document.getElementById('loading-indicator').style.display = 'none';
        document.getElementById('no-models-selected').textContent = 'Klaida lyginant modelius.';
        document.getElementById('no-models-selected').style.display = 'block';
    });
}

// Atvaizduoja palyginimo rezultatus
function displayComparisonResults(modelsData) {
    // Rodome rezultatų konteinerį
    document.getElementById('comparison-results').style.display = 'block';
    
    // Atvaizduojame metrikų korteles
    displayMetricCards(modelsData);
    
    // Atvaizduojame tikslumo grafiką
    displayAccuracyChart(modelsData);
    
    // Atvaizduojame nuostolių grafiką
    displayLossChart(modelsData);
    
    // Užpildome parametrų lentelę
    displayParamsTable(modelsData);
}

// Atvaizduoja metrikų korteles
function displayMetricCards(modelsData) {
    const metricsContainer = document.getElementById('metrics-cards');
    metricsContainer.innerHTML = '';
    
    // Tikslumo kortelė
    const bestAccuracy = Math.max(...modelsData.map(model => 
        model.metrics.accuracy?.slice(-1)[0] || 0
    ));
    
    const bestAccuracyModel = modelsData.find(model => 
        (model.metrics.accuracy?.slice(-1)[0] || 0) === bestAccuracy
    );
    
    // Tik jei yra reikšmė ir ji ne nulis
    if (bestAccuracy > 0) {
        const accuracyCard = document.createElement('div');
        accuracyCard.className = 'col-md-3';
        accuracyCard.innerHTML = `
            <div class="card metric-card bg-success text-white">
                <div class="card-body text-center">
                    <h5 class="card-title">Geriausias tikslumas</h5>
                    <h3 class="display-4">${(bestAccuracy * 100).toFixed(2)}%</h3>
                    <p class="card-text">${bestAccuracyModel.structure.name}</p>
                </div>
            </div>
        `;
        metricsContainer.appendChild(accuracyCard);
    }
    
    // Nuostolių kortelė
    const bestLoss = Math.min(...modelsData.map(model => 
        model.metrics.loss?.slice(-1)[0] || Infinity
    ));
    
    const bestLossModel = modelsData.find(model => 
        (model.metrics.loss?.slice(-1)[0] || Infinity) === bestLoss
    );
    
    // Tik jei yra reikšmė ir ji ne begalybė
    if (bestLoss < Infinity) {
        const lossCard = document.createElement('div');
        lossCard.className = 'col-md-3';
        lossCard.innerHTML = `
            <div class="card metric-card bg-info text-white">
                <div class="card-body text-center">
                    <h5 class="card-title">Mažiausi nuostoliai</h5>
                    <h3 class="display-4">${bestLoss.toFixed(4)}</h3>
                    <p class="card-text">${bestLossModel.structure.name}</p>
                </div>
            </div>
        `;
        metricsContainer.appendChild(lossCard);
    }
    
    // Sluoksnių skaičius
    const maxLayersCount = Math.max(...modelsData.map(model => 
        model.structure.layers.length
    ));
    
    const maxLayersModel = modelsData.find(model => 
        model.structure.layers.length === maxLayersCount
    );
    
    const layersCard = document.createElement('div');
    layersCard.className = 'col-md-3';
    layersCard.innerHTML = `
        <div class="card metric-card bg-warning">
            <div class="card-body text-center">
                <h5 class="card-title">Daugiausiai sluoksnių</h5>
                <h3 class="display-4">${maxLayersCount}</h3>
                <p class="card-text">${maxLayersModel.structure.name}</p>
            </div>
        </div>
    `;
    metricsContainer.appendChild(layersCard);
    
    // Parametrų skaičius
    const modelsParams = modelsData.map(model => {
        const totalParams = model.structure.layers.reduce((sum, layer) => sum + parseInt(layer.params || 0), 0);
        return { model: model, params: totalParams };
    });
    
    const maxParamsModel = modelsParams.reduce((prev, current) => 
        (prev.params > current.params) ? prev : current
    );
    
    const paramsCard = document.createElement('div');
    paramsCard.className = 'col-md-3';
    paramsCard.innerHTML = `
        <div class="card metric-card bg-primary text-white">
            <div class="card-body text-center">
                <h5 class="card-title">Daugiausiai parametrų</h5>
                <h3 class="display-4">${maxParamsModel.params.toLocaleString()}</h3>
                <p class="card-text">${maxParamsModel.model.structure.name}</p>
            </div>
        </div>
    `;
    metricsContainer.appendChild(paramsCard);
}

// Atvaizduoja tikslumo grafiką
function displayAccuracyChart(modelsData) {
    const ctx = document.getElementById('accuracy-chart').getContext('2d');
    
    // Sunaikinti esamą grafiką, jei jis yra
    if (accuracyChart) {
        accuracyChart.destroy();
    }
    
    // Paruošiame duomenis grafikui
    const datasets = modelsData.map((model, index) => {
        const color = chartColors[index % chartColors.length];
        return {
            label: model.structure.name,
            data: model.metrics.accuracy || [],
            backgroundColor: color,
            borderColor: color,
            fill: false,
            tension: 0.1
        };
    });
    
    // Sukuriame grafiką
    accuracyChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: Array.from({ length: Math.max(...modelsData.map(m => m.metrics.accuracy?.length || 0)) }, (_, i) => i+1),
            datasets: datasets
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                },
                title: {
                    display: true,
                    text: 'Modelių tikslumo palyginimas'
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                }
            },
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Epochos'
                    }
                },
                y: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Tikslumas'
                    },
                    min: 0,
                    max: 1
                }
            }
        }
    });
}

// Atvaizduoja nuostolių grafiką
function displayLossChart(modelsData) {
    const ctx = document.getElementById('loss-chart').getContext('2d');
    
    // Sunaikinti esamą grafiką, jei jis yra
    if (lossChart) {
        lossChart.destroy();
    }
    
    // Paruošiame duomenis grafikui
    const datasets = modelsData.map((model, index) => {
        const color = chartColors[index % chartColors.length];
        return {
            label: model.structure.name,
            data: model.metrics.loss || [],
            backgroundColor: color,
            borderColor: color,
            fill: false,
            tension: 0.1
        };
    });
    
    // Sukuriame grafiką
    lossChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: Array.from({ length: Math.max(...modelsData.map(m => m.metrics.loss?.length || 0)) }, (_, i) => i+1),
            datasets: datasets
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                },
                title: {
                    display: true,
                    text: 'Modelių nuostolių palyginimas'
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                }
            },
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Epochos'
                    }
                },
                y: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Nuostoliai'
                    }
                }
            }
        }
    });
}

// Užpildo parametrų lentelę
function displayParamsTable(modelsData) {
    const tableBody = document.getElementById('params-table-body');
    tableBody.innerHTML = '';
    
    modelsData.forEach(model => {
        const totalParams = model.structure.layers.reduce((sum, layer) => sum + parseInt(layer.params || 0), 0);
        
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${model.structure.name}</td>
            <td>${model.structure.layers.length}</td>
            <td>${totalParams.toLocaleString()}</td>
            <td>${model.metrics.training_time || 'N/A'}</td>
            <td>${model.metrics.accuracy ? (model.metrics.accuracy.slice(-1)[0] * 100).toFixed(2) + '%' : 'N/A'}</td>
            <td>${model.metrics.loss ? model.metrics.loss.slice(-1)[0].toFixed(4) : 'N/A'}</td>
            <td>
                <a href="/models/visualization?model=${model.id}" class="btn btn-sm btn-info">
                    <i class="fas fa-eye"></i> Peržiūrėti
                </a>
            </td>
        `;
        tableBody.appendChild(row);
    });
}