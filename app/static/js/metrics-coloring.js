// Metrikų reikšmių spalvinis kodavimas
document.addEventListener('DOMContentLoaded', function() {
    // Inicializuojame spalvinį kodavimą metrikoms
    applyMetricsColoring();
    
    // Funkcija, kuri pritaiko spalvinį kodavimą
    function applyMetricsColoring() {
        // Tikslumo (accuracy) metrikų spalvinis kodavimas
        colorAccuracyMetrics();
        
        // Klaidos (loss) metrikų spalvinis kodavimas
        colorLossMetrics();
        
        // Progreso juostų spalvinis kodavimas
        colorProgressBars();
    }
    
    // Tikslumo metrikų spalvinis kodavimas
    function colorAccuracyMetrics() {
        // Randame visus elementus su accuracy reikšmėmis
        const accuracyElements = document.querySelectorAll('.accuracy-metric');
        
        accuracyElements.forEach(function(element) {
            // Gauname reikšmę (gali būti tekste kaip "85%" arba data-value atribute)
            let value = parseFloat(element.dataset.value);
            if (isNaN(value)) {
                // Bandome gauti reikšmę iš teksto (pvz., "85%")
                const text = element.textContent.trim();
                value = parseFloat(text.replace('%', '')) / 100;
            }
            
            if (isNaN(value)) return; // Jeigu vis tiek nėra skaičius, grįžtame
            
            // Pritaikome spalvos klasę pagal reikšmę
            if (value >= 0.9) {
                element.classList.add('metric-excellent');
            } else if (value >= 0.8) {
                element.classList.add('metric-good');
            } else if (value >= 0.6) {
                element.classList.add('metric-average');
            } else {
                element.classList.add('metric-poor');
            }
        });
    }
    
    // Klaidos metrikų spalvinis kodavimas (mažesnė reikšmė = geriau)
    function colorLossMetrics() {
        // Randame visus elementus su loss reikšmėmis
        const lossElements = document.querySelectorAll('.loss-metric');
        
        lossElements.forEach(function(element) {
            // Gauname reikšmę
            let value = parseFloat(element.dataset.value);
            if (isNaN(value)) {
                // Bandome gauti reikšmę iš teksto
                const text = element.textContent.trim();
                value = parseFloat(text);
            }
            
            if (isNaN(value)) return; // Jeigu vis tiek nėra skaičius, grįžtame
            
            // Pritaikome spalvos klasę pagal reikšmę (loss atveju - mažesnė reikšmė geriau)
            if (value < 0.1) {
                element.classList.add('error-metric-excellent');
            } else if (value < 0.3) {
                element.classList.add('error-metric-good');
            } else if (value < 0.5) {
                element.classList.add('error-metric-average');
            } else {
                element.classList.add('error-metric-poor');
            }
        });
    }
    
    // Progreso juostų spalvinis kodavimas
    function colorProgressBars() {
        // Randame visas progreso juostas su data-value atributu
        const progressBars = document.querySelectorAll('.progress[data-value]');
        
        progressBars.forEach(function(progressElement) {
            const value = parseFloat(progressElement.dataset.value);
            if (isNaN(value)) return;
            
            // Triname seniau pridėtas klases
            progressElement.classList.remove('progress-excellent', 'progress-good', 'progress-average', 'progress-poor');
            
            // Pritaikome tinkamą klasę pagal reikšmę
            if (value >= 0.9) {
                progressElement.classList.add('progress-excellent');
            } else if (value >= 0.8) {
                progressElement.classList.add('progress-good');
            } else if (value >= 0.6) {
                progressElement.classList.add('progress-average');
            } else {
                progressElement.classList.add('progress-poor');
            }
        });
    }
    
    // Globalus metodas, kurį galima iškviesti iš kitų skriptų
    window.applyMetricsColoring = applyMetricsColoring;
});