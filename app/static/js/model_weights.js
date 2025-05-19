// filepath: d:\CA_BTC\app\static\js\model_weights.js
/**
 * Modelio svorių vizualizacijos modulis
 * 
 * Šis modulis teikia funkcionalumą modelio svorių, 
 * histogramų ir aktyvacijų vizualizacijai
 */

class ModelWeightsVisualizer {
    constructor(modelName) {
        this.modelName = modelName;
        this.chartInstances = {};
    }
    
    // Inicializuoja visas vizualizacijas
    initialize() {
        this.initializeHistograms();
        this.bindEventListeners();
    }
    
    // Inicializuoja histogramų atvaizdavimą
    initializeHistograms() {
        const histogramCanvases = document.querySelectorAll('.weight-histogram');
        
        histogramCanvases.forEach((canvas) => {
            const layerIndex = canvas.id.split('-')[1];
            this.loadHistogramData(canvas, layerIndex);
        });
    }
    
    // Gauna histogramos duomenis iš serverio
    loadHistogramData(canvas, layerIndex) {
        fetch(`/api/model_weights/histogram?model_name=${this.modelName}&layer_index=${layerIndex}`)
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    console.error('Klaida:', data.error);
                    return;
                }
                
                this.renderHistogram(canvas, data.histogram);
                this.loadLayerAnalysis(layerIndex);
            })
            .catch(error => {
                console.error('Klaida gaunant histogramą:', error);
            });
    }
    
    // Vizualizuoja histogramą
    renderHistogram(canvas, histogramData) {
        const ctx = canvas.getContext('2d');
        
        const chartConfig = {
            type: 'bar',
            data: {
                labels: histogramData.bins,
                datasets: [{
                    label: 'Svorių pasiskirstymas',
                    data: histogramData.values,
                    backgroundColor: 'rgba(54, 162, 235, 0.5)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        };
        
        if (this.chartInstances[canvas.id]) {
            this.chartInstances[canvas.id].destroy();
        }
        
        this.chartInstances[canvas.id] = new Chart(ctx, chartConfig);
    }
    
    // Gauna ir atvaizduoja sluoksnio statistinę analizę
    loadLayerAnalysis(layerIndex) {
        fetch(`/api/model_weights/analysis?model_name=${this.modelName}&layer_index=${layerIndex}`)
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    console.error('Klaida:', data.error);
                    return;
                }
                
                this.updateLayerAnalysisUI(layerIndex, data);
            })
            .catch(error => {
                console.error('Klaida gaunant analizę:', error);
            });
    }
    
    // Atnaujina statistinės analizės UI
    updateLayerAnalysisUI(layerIndex, data) {
        const layerCard = document.querySelector(`.layer-card[data-layer-index="${layerIndex}"]`);
        layerCard.querySelector('.min-value').textContent = data.min.toFixed(6);
        layerCard.querySelector('.max-value').textContent = data.max.toFixed(6);
        layerCard.querySelector('.mean-value').textContent = data.mean.toFixed(6);
        layerCard.querySelector('.std-value').textContent = data.std.toFixed(6);
    }
    
    // Registruoja įvykių klausytojus
    bindEventListeners() {
        document.querySelectorAll('.show-activations').forEach(button => {
            button.addEventListener('click', (event) => {
                const layerIndex = event.target.dataset.layerIndex;
                this.showActivations(layerIndex);
            });
        });
        
        document.querySelectorAll('.show-details').forEach(button => {
            button.addEventListener('click', (event) => {
                const layerIndex = event.target.dataset.layerIndex;
                this.showDetailedAnalysis(layerIndex);
            });
        });
        
        // Filtravimo įvykiai
        document.getElementById('apply-filters').addEventListener('click', () => this.applyFilters());
        document.getElementById('reset-filters').addEventListener('click', () => this.resetFilters());
    }
    
    // Atvaizduoja aktyvacijas
    showActivations(layerIndex) {
        fetch(`/api/model_weights/activations?model_name=${this.modelName}&layer_index=${layerIndex}`)
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    console.error('Klaida:', data.error);
                    return;
                }
                
                this.renderActivationsHeatmap(data.heatmap);
                
                const modal = new bootstrap.Modal(document.getElementById('activationsModal'));
                modal.show();
            })
            .catch(error => {
                console.error('Klaida gaunant aktyvacijąs:', error);
            });
    }
    
    // Vizualizuoja aktyvacijų šilumos žemėlapį
    renderActivationsHeatmap(heatmapData) {
        const canvas = document.getElementById('activations-heatmap');
        const ctx = canvas.getContext('2d');
        
        // Pašaliname seną grafiką, jei toks jau buvo
        if (this.chartInstances['activations-heatmap']) {
            this.chartInstances['activations-heatmap'].destroy();
        }
        
        // Nustatome paveiksliuką kaip fono paveikslėlį, jei duomenys yra base64 formatu
        if (typeof heatmapData === 'string' && heatmapData.length > 0) {
            // Sukuriame paveikslėlį ir nustatome jo šaltinį
            const img = new Image();
            img.onload = function() {
                // Išvalome canvas
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                
                // Pritaikome canvas dydį prie paveiksliuko
                canvas.width = img.width;
                canvas.height = img.height;
                
                // Piešiame paveikslėlį
                ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
            };
            
            // Nustatome paveiksliuko šaltinį
            img.src = `data:image/png;base64,${heatmapData}`;
        } else {
            // Jei duomenys nėra base64 formatu, rodome klaidos pranešimą
            ctx.font = '16px Arial';
            ctx.fillStyle = 'red';
            ctx.textAlign = 'center';
            ctx.fillText('Nepavyko atvaizduoti aktyvacijų: neteisingas duomenų formatas', canvas.width/2, canvas.height/2);
        }
    }
    
    // Atvaizduoja detalią analizę
    showDetailedAnalysis(layerIndex) {
        fetch(`/api/model_weights/analysis?model_name=${this.modelName}&layer_index=${layerIndex}`)
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    console.error('Klaida:', data.error);
                    return;
                }
                
                this.renderDetailedAnalysis(data);
                
                const modal = new bootstrap.Modal(document.getElementById('detailsModal'));
                modal.show();
            })
            .catch(error => {
                console.error('Klaida gaunant analizę:', error);
            });
    }
    
    // Vizualizuoja detalią analizę
    renderDetailedAnalysis(data) {
        const container = document.querySelector('.detailed-analysis-container');
        
        // Sukuriame HTML turinį detaliai analizei
        let html = `
            <div class="row mb-4">
                <div class="col-md-12">
                    <h5 class="border-bottom pb-2">Pagrindinė statistika</h5>
                </div>
            </div>
            
            <div class="row mb-4">
                <!-- Pagrindinė statistika kortelėse -->
                <div class="col-md-3">
                    <div class="card bg-light">
                        <div class="card-body text-center">
                            <h6 class="card-title text-muted">Minimumas</h6>
                            <p class="h3 text-primary">${data.min.toFixed(6)}</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card bg-light">
                        <div class="card-body text-center">
                            <h6 class="card-title text-muted">Maksimumas</h6>
                            <p class="h3 text-primary">${data.max.toFixed(6)}</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card bg-light">
                        <div class="card-body text-center">
                            <h6 class="card-title text-muted">Vidurkis</h6>
                            <p class="h3 text-primary">${data.mean.toFixed(6)}</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card bg-light">
                        <div class="card-body text-center">
                            <h6 class="card-title text-muted">Stand. nuokrypis</h6>
                            <p class="h3 text-primary">${data.std.toFixed(6)}</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row mb-4">
                <div class="col-md-12">
                    <h5 class="border-bottom pb-2">Pasiskirstymo statistika</h5>
                </div>
            </div>
            
            <div class="row mb-4">
                <!-- Pasiskirstymo statistika kortelėse -->
                <div class="col-md-4">
                    <div class="card bg-light">
                        <div class="card-body text-center">
                            <h6 class="card-title text-muted">Mediana</h6>
                            <p class="h3 text-success">${data.median.toFixed(6)}</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card bg-light">
                        <div class="card-body text-center">
                            <h6 class="card-title text-muted">Retumas (sparsity)</h6>
                            <p class="h3 text-success">${(data.sparsity * 100).toFixed(2)}%</p>
                            <small>Nulių procentas visame tinkle</small>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card bg-light">
                        <div class="card-body text-center">
                            <h6 class="card-title text-muted">Elementų skaičius</h6>
                            <p class="h3 text-success">${data.total_elements.toLocaleString()}</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row mb-4">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header bg-light">
                            <h6 class="mb-0">Reikšmių pasiskirstymas</h6>
                        </div>
                        <div class="card-body">
                            <table class="table table-sm">
                                <tr>
                                    <td>Teigiamos reikšmės:</td>
                                    <td class="text-end">${(data.positive_ratio * 100).toFixed(2)}%</td>
                                    <td>
                                        <div class="progress">
                                            <div class="progress-bar bg-success" role="progressbar" 
                                                 style="width: ${data.positive_ratio * 100}%"></div>
                                        </div>
                                    </td>
                                </tr>
                                <tr>
                                    <td>Neigiamos reikšmės:</td>
                                    <td class="text-end">${(data.negative_ratio * 100).toFixed(2)}%</td>
                                    <td>
                                        <div class="progress">
                                            <div class="progress-bar bg-danger" role="progressbar" 
                                                 style="width: ${data.negative_ratio * 100}%"></div>
                                        </div>
                                    </td>
                                </tr>
                                <tr>
                                    <td>Nulinės reikšmės:</td>
                                    <td class="text-end">${(data.sparsity * 100).toFixed(2)}%</td>
                                    <td>
                                        <div class="progress">
                                            <div class="progress-bar bg-secondary" role="progressbar" 
                                                 style="width: ${data.sparsity * 100}%"></div>
                                        </div>
                                    </td>
                                </tr>
                            </table>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header bg-light">
                            <h6 class="mb-0">Procentilės</h6>
                        </div>
                        <div class="card-body">
                            <table class="table table-sm">
                                <tr>
                                    <td>1%:</td>
                                    <td class="text-end">${data.percentiles['1'].toFixed(6)}</td>
                                </tr>
                                <tr>
                                    <td>25%:</td>
                                    <td class="text-end">${data.percentiles['25'].toFixed(6)}</td>
                                </tr>
                                <tr>
                                    <td>50% (mediana):</td>
                                    <td class="text-end">${data.percentiles['50'].toFixed(6)}</td>
                                </tr>
                                <tr>
                                    <td>75%:</td>
                                    <td class="text-end">${data.percentiles['75'].toFixed(6)}</td>
                                </tr>
                                <tr>
                                    <td>99%:</td>
                                    <td class="text-end">${data.percentiles['99'].toFixed(6)}</td>
                                </tr>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Įterpiame HTML turinį į konteinerį
        container.innerHTML = html;
    }
    
    // Taiko filtrus sluoksniams
    applyFilters() {
        // Gauname filtro reikšmes
        const typeFilter = document.getElementById('layer-type-filter').value.toLowerCase();
        const minParams = parseInt(document.getElementById('layer-params-filter').value) || 0;
        const sortBy = document.getElementById('sort-by').value;
        
        // Gauname visas sluoksnių korteles
        const layerCards = document.querySelectorAll('.layer-card');
        const container = document.getElementById('layers-container');
        
        // Masyvas matomų kortelių saugojimui
        const visibleCards = [];
        
        // Filtruojame korteles
        layerCards.forEach(card => {
            // Gauname korteles atributus
            const layerType = card.dataset.layerType.toLowerCase();
            const paramsElement = card.querySelector('.params-count');
            
            // Jei elementas egzistuoja, gauname parametrų skaičių
            let params = 0;
            if (paramsElement) {
                // Ištraukiame skaičių iš teksto
                const match = paramsElement.textContent.match(/\d+/);
                if (match) {
                    params = parseInt(match[0]);
                }
            }
            
            // Tikriname ar sluoksnis atitinka filtrus
            const typeMatch = !typeFilter || typeFilter === 'all' || layerType.includes(typeFilter);
            const paramsMatch = params >= minParams;
            
            // Rodome arba slepiame sluoksnį
            if (typeMatch && paramsMatch) {
                card.style.display = 'block';  // arba 'flex' priklausomai nuo CSS
                visibleCards.push(card);
            } else {
                card.style.display = 'none';
            }
        });
        
        // Rikiuojame matomus sluoksnius
        visibleCards.sort((a, b) => {
            if (sortBy === 'name') {
                // Rikiuojame pagal pavadinimą
                const nameA = a.querySelector('h5').textContent.trim();
                const nameB = b.querySelector('h5').textContent.trim();
                return nameA.localeCompare(nameB);
            } else if (sortBy === 'params') {
                // Rikiuojame pagal parametrų skaičių
                const paramsA = parseInt(a.querySelector('.params-count')?.textContent.match(/\d+/) || 0);
                const paramsB = parseInt(b.querySelector('.params-count')?.textContent.match(/\d+/) || 0);
                return paramsB - paramsA;  // Didžiausi skaičiai pirmi
            } else {
                // Rikiuojame pagal originalų indeksą
                const indexA = parseInt(a.dataset.layerIndex || 0);
                const indexB = parseInt(b.dataset.layerIndex || 0);
                return indexA - indexB;
            }
        });
        
        // Pertvarkome sluoksnių korteles dokumente pagal rikiavimą
        visibleCards.forEach(card => {
            container.appendChild(card);
        });
        
        // Atnaujinkime rezultatų skaičių, jei toks elementas egzistuoja
        const resultsCount = document.getElementById('results-count');
        if (resultsCount) {
            resultsCount.textContent = `Rodoma sluoksnių: ${visibleCards.length} iš ${layerCards.length}`;
        }
    }
    
    // Atstato filtrus į pradinę būseną
    resetFilters() {
        // Nustatome pradinius filtro reikšmes
        document.getElementById('layer-type-filter').value = 'all';
        document.getElementById('layer-params-filter').value = '0';
        document.getElementById('sort-by').value = 'index';
        
        // Rodome visas korteles
        const layerCards = document.querySelectorAll('.layer-card');
        layerCards.forEach(card => {
            card.style.display = 'block';  // arba 'flex' priklausomai nuo CSS
        });
        
        // Atstatome pradinę sluoksnių tvarką
        this.applyFilters();
        
        // Parodome pranešimą vartotojui
        const message = document.getElementById('filter-message');
        if (message) {
            message.textContent = 'Filtrai atstatyti į pradinę būseną';
            message.style.display = 'block';
            
            // Paslepiame pranešimą po 3 sekundžių
            setTimeout(() => {
                message.style.display = 'none';
            }, 3000);
        }
    }
}

// Inicializuojame, kai puslapis užkraunamas
document.addEventListener('DOMContentLoaded', function() {
    // Gauname modelio pavadinimą iš URL
    const path = window.location.pathname;
    const modelName = path.substring(path.lastIndexOf('/') + 1);
    
    // Inicializuojame vizualizatorių
    const visualizer = new ModelWeightsVisualizer(modelName);
    visualizer.initialize();
});