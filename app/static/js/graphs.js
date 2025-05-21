

// Grafiko klasė
class ChartManager {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        this.chartInstance = null;
    }
    
    // Grafikų piešimo metodai
    drawPriceChart(data) {
        this.destroyExisting();
        
        this.chartInstance = new Chart(this.ctx, {
            type: 'line',
            data: {
                labels: data.dates,
                datasets: [{
                    label: 'Bitcoin kaina (USD)',
                    data: data.prices,
                    borderColor: 'rgb(54, 162, 235)',
                    backgroundColor: 'rgba(54, 162, 235, 0.1)',
                    borderWidth: 2,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Data'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Kaina (USD)'
                        }
                    }
                }
            }
        });
    }
    
    drawPredictionChart(data) {
        this.destroyExisting();
        
        this.chartInstance = new Chart(this.ctx, {
            type: 'line',
            data: {
                labels: data.dates,
                datasets: [
                    {
                        label: 'Faktinė kaina',
                        data: data.actual,
                        borderColor: 'rgb(54, 162, 235)',
                        backgroundColor: 'rgba(54, 162, 235, 0.1)',
                        borderWidth: 2,
                        yAxisID: 'y'
                    },
                    {
                        label: 'Prognozės (1=kils, 0=kris)',
                        data: data.predicted,
                        borderColor: 'rgb(255, 99, 132)',
                        backgroundColor: 'rgba(255, 99, 132, 0.1)',
                        borderWidth: 2,
                        type: 'line',
                        stepped: true,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: 'Kaina (USD)'
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        min: -0.1,
                        max: 1.1,
                        title: {
                            display: true,
                            text: 'Prognozė'
                        },
                        grid: {
                            drawOnChartArea: false
                        }
                    }
                }
            }
        });
    }
    
    drawPerformanceChart(data) {
        this.destroyExisting();
        
        this.chartInstance = new Chart(this.ctx, {
            type: 'line',
            data: {
                labels: data.dates,
                datasets: [{
                    label: 'Balansas (USD)',
                    data: data.balances,
                    borderColor: 'rgb(75, 192, 192)',
                    backgroundColor: 'rgba(75, 192, 192, 0.1)',
                    borderWidth: 2,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Data'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Balansas (USD)'
                        }
                    }
                }
            }
        });
    }
    
    // Sunaikina egzistuojantį grafiką
    destroyExisting() {
        if (this.chartInstance) {
            this.chartInstance.destroy();
            this.chartInstance = null;
        }
    }
}

// Inicializacija dokumento užkrovimo metu
document.addEventListener('DOMContentLoaded', function() {
    // Elementai
    const graphTypeSelect = document.getElementById('graph-type');
    const timeframeSelect = document.getElementById('timeframe');
    const modelSelectContainer = document.getElementById('model-select-container');
    const modelSelect = document.getElementById('model-select');
    const updateGraphBtn = document.getElementById('update-graph');
    
    // Grafiko valdiklis
    const chartManager = new ChartManager('main-chart');
    
    // Kontrolės elementų elgsena
    graphTypeSelect.addEventListener('change', function() {
        if (this.value === 'price') {
            modelSelectContainer.style.display = 'none';
        } else {
            modelSelectContainer.style.display = 'block';
        }
    });
    
    // Grafiko atnaujinimo funkcija
    function updateGraph() {
        const graphType = graphTypeSelect.value;
        const timeframe = timeframeSelect.value;
        const modelId = modelSelect.value;
        
        // URL parametrai
        let url = `/analysis/api/graph-data?type=${graphType}&timeframe=${timeframe}`;
        if (graphType !== 'price') {
            url += `&model_id=${modelId}`;
        }
        
        // Gaunami duomenys iš API
        fetch(url)
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    console.error('Klaida gaunant duomenis:', data.error);
                    return;
                }
                
                // Piešiame grafiką su gautais duomenimis
                if (graphType === 'price') {
                    chartManager.drawPriceChart(data);
                } else if (graphType === 'prediction') {
                    chartManager.drawPredictionChart(data);
                } else if (graphType === 'performance') {
                    chartManager.drawPerformanceChart(data);
                }
            })
            .catch(error => {
                console.error('Klaida vykdant užklausą:', error);
            });
    }
    
    // Mygtuko paspaudimo įvykis
    updateGraphBtn.addEventListener('click', updateGraph);
    
    // Pirmas grafiko užkrovimas
    updateGraph();
});