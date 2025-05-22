// Grafikos atvaizdavimo funkcijos
document.addEventListener('DOMContentLoaded', function() {
    // Pagrindiniai grafikų atvaizdavimai
    try {
        // Atvaizdavimas pagrindinio kainos grafiko
        if (window.priceChartData) {
            Plotly.newPlot('price-chart', window.priceChartData.data, window.priceChartData.layout);
        }
        
        // Atvaizdavimas modelių palyginimo grafiko
        if (window.comparisonChartData) {
            Plotly.newPlot('comparison-chart', window.comparisonChartData.data, window.comparisonChartData.layout);
        }
    } catch (error) {
        console.error("Klaida apdorojant pagrindinius grafikus:", error);
    }
    
    // Laiko periodų grafikų atvaizdavimas
    try {
        if (window.timePeriodCharts) {
            // 7 dienų grafikas
            if (window.timePeriodCharts['7d']) {
                Plotly.newPlot('priceChart7d', window.timePeriodCharts['7d'].data, window.timePeriodCharts['7d'].layout);
            }
            
            // 30 dienų grafikas
            if (window.timePeriodCharts['30d']) {
                Plotly.newPlot('priceChart30d', window.timePeriodCharts['30d'].data, window.timePeriodCharts['30d'].layout);
            }
            
            // 90 dienų grafikas
            if (window.timePeriodCharts['90d']) {
                Plotly.newPlot('priceChart90d', window.timePeriodCharts['90d'].data, window.timePeriodCharts['90d'].layout);
            }
        }
    } catch (error) {
        console.error("Klaida apdorojant laiko periodų grafikus:", error);
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