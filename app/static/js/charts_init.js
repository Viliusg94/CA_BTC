// Grafikos duomenų ir atvaizdavimo valdymo failas

// Globalūs kintamieji grafikų duomenims
var priceChartData = null;
var comparisonChartData = null;
var timePeriodCharts = {};

// Duomenų inicializavimo funkcija - iškviečiama iš index.html
function initializeChartData(priceData, comparisonData, periodData) {
    // Pagrindinis kainos grafikas
    if (priceData) {
        priceChartData = priceData;
        Plotly.newPlot('price-chart', priceChartData.data, priceChartData.layout);
    } else {
        console.warn("Nėra pagrindinių kainos duomenų grafikui");
        showNoDataMessage('price-chart', 'Kainos istorijos duomenys nepasiekiami');
    }
    
    // Modelių palyginimo grafikas
    if (comparisonData) {
        comparisonChartData = comparisonData;
        Plotly.newPlot('comparison-chart', comparisonChartData.data, comparisonChartData.layout);
    } else {
        console.warn("Nėra modelių palyginimo duomenų");
        showNoDataMessage('comparison-chart', 'Modelių palyginimo duomenys nepasiekiami');
    }
    
    // Laiko periodų grafikai
    if (periodData) {
        timePeriodCharts = periodData;
        renderTimePeriodCharts();
    }
    
    // Pradedame aktyvių mokymų atnaujinimą
    updateActiveTrainings();
}

// Funkcija atvaizduojanti laiko periodų grafikus
function renderTimePeriodCharts() {
    // 7 dienų grafikas
    if (timePeriodCharts['7d']) {
        Plotly.newPlot('priceChart7d', timePeriodCharts['7d'].data, timePeriodCharts['7d'].layout);
    } else {
        showNoDataMessage('priceChart7d', '7 dienų istorijos duomenys nepasiekiami');
    }
    
    // 30 dienų grafikas
    if (timePeriodCharts['30d']) {
        Plotly.newPlot('priceChart30d', timePeriodCharts['30d'].data, timePeriodCharts['30d'].layout);
    } else {
        showNoDataMessage('priceChart30d', '30 dienų istorijos duomenys nepasiekiami');
    }
    
    // 90 dienų grafikas
    if (timePeriodCharts['90d']) {
        Plotly.newPlot('priceChart90d', timePeriodCharts['90d'].data, timePeriodCharts['90d'].layout);
    } else {
        showNoDataMessage('priceChart90d', '90 dienų istorijos duomenys nepasiekiami');
    }
}

// Funkcija atnaujinanti aktyvių mokymų informaciją
function updateActiveTrainings() {
    setInterval(function() {
        fetch('/api/training_status')
            .then(response => response.json())
            .then(data => {
                const container = document.getElementById('active-training-container');
                if (!container) return;
                
                if (Object.keys(data).length === 0) {
                    container.innerHTML = `
                        <div class="text-center p-3">
                            <p class="text-muted mb-0">Šiuo metu nėra aktyvių mokymų.</p>
                        </div>
                    `;
                } else {
                    let html = '<ul class="list-group list-group-flush">';
                    
                    for (const [jobId, job] of Object.entries(data)) {
                        html += `
                            <li class="list-group-item">
                                <div class="d-flex justify-content-between">
                                    <span>${job.model_type.toUpperCase()}</span>
                                    <small>${job.status}</small>
                                </div>
                                <div class="progress mt-2" style="height: 5px;">
                                    <div class="progress-bar bg-info" role="progressbar" 
                                         style="width: ${job.progress}%"
                                         aria-valuenow="${job.progress}" 
                                         aria-valuemin="0" 
                                         aria-valuemax="100">
                                    </div>
                                </div>
                            </li>
                        `;
                    }
                    
                    html += '</ul>';
                    container.innerHTML = html;
                }
            })
            .catch(error => console.error('Klaida gaunant mokymų statusą:', error));
    }, 5000);
}

// Funkcija perjungianti kainos grafiką pagal laiko intervalą
function updateChart(days, buttonElement) {
    // Pažymime aktyvų mygtuką
    const buttons = buttonElement.parentElement.querySelectorAll('.btn');
    buttons.forEach(btn => btn.classList.remove('active'));
    buttonElement.classList.add('active');
    
    // Čia ateityje galima įdėti logiką, kuri atnaujintų grafiką pagal pasirinktą intervalą
}

// Funkcija rodanti pranešimą, kad nėra duomenų
function showNoDataMessage(elementId, message) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = `
            <div class="alert alert-warning text-center">
                <i class="fas fa-exclamation-triangle me-2"></i>
                ${message}
            </div>
        `;
    }
}

// Grafikų inicializavimas, kai dokumentas užkrautas
document.addEventListener('DOMContentLoaded', function() {
    try {
        // Gauname duomenis iš window objekto, kurie buvo perduoti iš serverio
        const priceData = window.chartData.price;
        const comparisonData = window.chartData.comparison;
        const periodData = window.chartData.periods;
        
        // Inicializuojame grafikus su gautais duomenimis
        initializeChartData(priceData, comparisonData, periodData);
    } catch(e) {
        console.error("Klaida inicializuojant grafikų duomenis:", e);
    }
});