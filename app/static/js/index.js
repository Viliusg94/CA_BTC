// static/js/index.js

// Kintamieji bus perduodami per window objektą
var priceChartData = null; 
var comparisonChartData = null;

// Kainos grafiko rodymas
document.addEventListener('DOMContentLoaded', function() {
    try {
        // Naudojame window objektą kintamiesiems pasiekti
        if (window.priceChartData && document.getElementById('price-chart')) {
            Plotly.newPlot('price-chart', window.priceChartData.data, window.priceChartData.layout);
        }
        
        if (window.comparisonChartData && document.getElementById('comparison-chart')) {
            Plotly.newPlot('comparison-chart', window.comparisonChartData.data, window.comparisonChartData.layout);
        }
        
        // Iškart atnaujinti aktyvių mokymų sąrašą
        updateActiveTrainingJobs();
        
        // Periodiškai atnaujiname aktyvių mokymų sąrašą
        setInterval(updateActiveTrainingJobs, 5000);
    } catch (error) {
        console.error('Klaida inicializuojant grafikų duomenis:', error);
    }
});

// Funkcija kainos grafiko atnaujinimui pagal pasirinktą intervalą
function updateChart(days, buttonElement) {
    if (!buttonElement || !days) return;
    
    fetch('/api/price_chart?days=' + days)
        .then(function(response) {
            if (!response.ok) {
                throw new Error('Serverio klaida: ' + response.status);
            }
            return response.json();
        })
        .then(function(chartData) {
            if (chartData && document.getElementById('price-chart')) {
                Plotly.newPlot('price-chart', chartData.data, chartData.layout);
            }
        })
        .catch(function(error) {
            console.error('Klaida gaunant kainų duomenis:', error);
            alert('Nepavyko gauti kainų duomenų. Bandykite vėliau.');
        });
            
    // Atnaujinti aktyvius mygtukus
    var buttons = document.querySelectorAll('.btn-group .btn');
    if (buttons && buttons.length) {
        for (var i = 0; i < buttons.length; i++) {
            buttons[i].classList.remove('active');
        }
        buttonElement.classList.add('active');
    }
}

// Funkcija aktyvių mokymų atnaujinimui
function updateActiveTrainingJobs() {
    var container = document.getElementById('active-training-container');
    if (!container) return;
    
    fetch('/api/active_training_jobs')
        .then(function(response) {
            if (!response.ok) {
                throw new Error('Serverio klaida: ' + response.status);
            }
            return response.json();
        })
        .then(function(data) {
            if (!Array.isArray(data)) {
                throw new Error('Gautas neteisingas duomenų formatas');
            }
            
            if (data.length === 0) {
                container.innerHTML = '<div class="text-center p-3"><p class="text-muted mb-0">Šiuo metu nėra aktyvių mokymų.</p></div>';
                return;
            }
            
            var fragment = document.createDocumentFragment();
            var ul = document.createElement('ul');
            ul.className = 'list-group list-group-flush';
            
            for (var i = 0; i < data.length; i++) {
                var job = data[i];
                var progress = job.progress || 0;
                
                var li = document.createElement('li');
                li.className = 'list-group-item';
                
                var upperDiv = document.createElement('div');
                upperDiv.className = 'd-flex justify-content-between';
                
                var modelSpan = document.createElement('span');
                modelSpan.textContent = job.model_type.toUpperCase();
                
                var statusSpan = document.createElement('small');
                statusSpan.textContent = job.status;
                
                upperDiv.appendChild(modelSpan);
                upperDiv.appendChild(statusSpan);
                
                var progressDiv = document.createElement('div');
                progressDiv.className = 'progress mt-2';
                progressDiv.style.height = '5px';
                
                var progressBar = document.createElement('div');
                progressBar.className = 'progress-bar bg-info';
                progressBar.setAttribute('role', 'progressbar');
                progressBar.style.width = progress + '%';
                progressBar.setAttribute('aria-valuenow', progress);
                progressBar.setAttribute('aria-valuemin', '0');
                progressBar.setAttribute('aria-valuemax', '100');
                
                progressDiv.appendChild(progressBar);
                li.appendChild(upperDiv);
                li.appendChild(progressDiv);
                ul.appendChild(li);
            }
            
            fragment.appendChild(ul);
            container.innerHTML = '';
            container.appendChild(fragment);
        })
        .catch(function(error) {
            console.error('Klaida atnaujinant aktyvių mokymų sąrašą:', error);
            container.innerHTML = '<div class="alert alert-warning text-center"><i class="fas fa-exclamation-triangle me-2"></i> Nepavyko atnaujinti mokymų sąrašo.</div>';
        });
}