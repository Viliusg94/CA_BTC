// Duomenų išvalymo funkcija, kad išvengti klaidų
function safeJsonParse(jsonStr) {
    try {
        return JSON.parse(jsonStr);
    } catch (e) {
        console.error("Klaida apdorojant JSON:", e);
        return null;
    }
}

// Grafikų atvaizdavimas
document.addEventListener('DOMContentLoaded', function() {
    // Naudojame duomenis iš window.appData
    const priceData = window.appData.priceChart;
    const comparisonData = window.appData.comparisonChart;
    const periodData = window.appData.periodCharts;
    
    // Pagrindinis kainos grafikas
    if (priceData) {
        Plotly.newPlot('price-chart', priceData.data, priceData.layout);
    } else {
        console.warn("Nėra pagrindinių kainos duomenų grafikui");
    }
    
    // Modelių palyginimo grafikas
    if (comparisonData) {
        Plotly.newPlot('comparison-chart', comparisonData.data, comparisonData.layout);
    } else {
        console.warn("Nėra modelių palyginimo duomenų");
    }
    
    // Periodų grafikai
    if (periodData['7d']) {
        Plotly.newPlot('priceChart7d', periodData['7d'].data, periodData['7d'].layout);
    }
    
    if (periodData['30d']) {
        Plotly.newPlot('priceChart30d', periodData['30d'].data, periodData['30d'].layout);
    }
    
    if (periodData['90d']) {
        Plotly.newPlot('priceChart90d', periodData['90d'].data, periodData['90d'].layout);
    }
    
    // Aktyvių mokymų atnaujinimas
    updateActiveTrainings();
});

// Atnaujina aktyvių mokymų informaciją kas 5 sekundes
function updateActiveTrainings() {
    setInterval(function() {
        fetch('/api/training_status')
            .then(response => response.json())
            .then(data => {
                const container = document.getElementById('active-training-container');
                if (!container) return;
                
                if (Object.keys(data).length === 0) {
                    container.innerHTML = '<div class="text-center p-3"><p class="text-muted mb-0">Šiuo metu nėra aktyvių mokymų.</p></div>';
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
}