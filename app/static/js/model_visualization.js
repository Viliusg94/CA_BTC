// Šis skriptas sukuria interaktyvų modelio architektūros vizualizavimo įrankį

// Globalūs kintamieji
let modelLayers = []; // Modelio sluoksnių informacija
let selectedLayerIndex = -1; // Pažymėto sluoksnio indeksas

/**
 * Inicializuoja modelio vizualizacijos įrankį
 * @param {Array} layers - Modelio sluoksnių masyvas
 */
function initModelVisualizer(layers) {
    // Išsaugome sluoksnių informaciją
    modelLayers = layers;
    
    // Sukuriame vizualinę diagramą
    createLayersVisualization();
    
    // Pridedame įvykių klausytojus
    addEventListeners();
    
    console.log("Modelio vizualizacijos įrankis inicializuotas");
}

/**
 * Sukuria vizualinę sluoksnių diagramą
 */
function createLayersVisualization() {
    const container = document.getElementById('layers-visualization');
    if (!container) return;
    
    // Išvalome konteinerį
    container.innerHTML = '';
    
    // Sukuriame kiekvieną sluoksnį
    modelLayers.forEach((layer, index) => {
        // Sukuriame sluoksnio elementą
        const layerElement = document.createElement('div');
        layerElement.className = 'layer-box';
        layerElement.id = `layer-${index}`;
        layerElement.dataset.index = index;
        
        // Jei tai pažymėtas sluoksnis, pridedame klasę
        if (index === selectedLayerIndex) {
            layerElement.classList.add('selected-layer');
        }
        
        // Nustatome skirtingą spalvą pagal sluoksnio tipą
        let layerColor = '#3498db'; // Numatytoji spalva
        
        // Skirtinga spalva pagal sluoksnio tipą
        if (layer.type.includes('Dense')) {
            layerColor = '#2ecc71'; // Žalia spalva
        } else if (layer.type.includes('Conv')) {
            layerColor = '#e74c3c'; // Raudona spalva
        } else if (layer.type.includes('LSTM') || layer.type.includes('GRU')) {
            layerColor = '#9b59b6'; // Violetinė spalva
        } else if (layer.type.includes('Dropout')) {
            layerColor = '#95a5a6'; // Pilka spalva
        }
        
        layerElement.style.backgroundColor = layerColor;
        
        // Sluoksnio pavadinimas
        const nameElement = document.createElement('div');
        nameElement.className = 'layer-name';
        nameElement.textContent = layer.name;
        layerElement.appendChild(nameElement);
        
        // Sluoksnio tipas
        const typeElement = document.createElement('div');
        typeElement.className = 'layer-type';
        typeElement.textContent = layer.type;
        layerElement.appendChild(typeElement);
        
        // Parametrų skaičius
        const paramsElement = document.createElement('div');
        paramsElement.className = 'layer-params';
        paramsElement.textContent = `Parametrai: ${layer.params.toLocaleString()}`;
        layerElement.appendChild(paramsElement);
        
        // Įdedame sluoksnį į konteinerį
        container.appendChild(layerElement);
        
        // Pridedame jungiamąją liniją tarp sluoksnių, išskyrus pirmą
        if (index > 0) {
            const connector = document.createElement('div');
            connector.className = 'layer-connector';
            container.appendChild(connector);
        }
    });
}

/**
 * Prideda įvykių klausytojus interaktyvumui
 */
function addEventListeners() {
    // Pasirenkame visus sluoksnius
    const layerElements = document.querySelectorAll('.layer-box');
    
    // Pridedame paspaudimo įvykį kiekvienam sluoksniui
    layerElements.forEach(element => {
        element.addEventListener('click', function() {
            // Gauname sluoksnio indeksą
            const index = parseInt(this.dataset.index);
            
            // Pažymime pasirinktą sluoksnį
            selectLayer(index);
            
            // Rodome detalią informaciją apie sluoksnį
            showLayerDetails(index);
        });
    });
}

/**
 * Pažymi pasirinktą sluoksnį
 * @param {number} index - Sluoksnio indeksas
 */
function selectLayer(index) {
    // Nuimame pažymėjimą nuo visų sluoksnių
    document.querySelectorAll('.layer-box').forEach(el => {
        el.classList.remove('selected-layer');
    });
    
    // Pažymime pasirinktą sluoksnį
    const selectedElement = document.getElementById(`layer-${index}`);
    if (selectedElement) {
        selectedElement.classList.add('selected-layer');
    }
    
    // Atnaujiname globalinį kintamąjį
    selectedLayerIndex = index;
}

/**
 * Rodo detalią informaciją apie pasirinktą sluoksnį
 * @param {number} index - Sluoksnio indeksas
 */
function showLayerDetails(index) {
    // Gauname sluoksnio informaciją
    const layer = modelLayers[index];
    if (!layer) return;
    
    // Gauname detalios informacijos elementą
    const detailsContainer = document.getElementById('layer-details');
    if (!detailsContainer) return;
    
    // Formuojame HTML turinį
    let detailsHtml = `
        <div class="card mt-4">
            <div class="card-header bg-primary text-white">
                <h5 class="mb-0">Sluoksnio "${layer.name}" detalės</h5>
            </div>
            <div class="card-body">
                <table class="table table-bordered">
                    <tr>
                        <th>Savybė</th>
                        <th>Reikšmė</th>
                    </tr>
                    <tr>
                        <td>Tipas</td>
                        <td>${layer.type}</td>
                    </tr>
                    <tr>
                        <td>Parametrų skaičius</td>
                        <td>${layer.params.toLocaleString()}</td>
                    </tr>
                    <tr>
                        <td>Išvesties forma</td>
                        <td>${layer.output_shape}</td>
                    </tr>
    `;
    
    // Pridedame aktyvaciją, jei ji yra
    if (layer.activation) {
        detailsHtml += `
                    <tr>
                        <td>Aktyvacijos funkcija</td>
                        <td>${layer.activation}</td>
                    </tr>
        `;
    }
    
    // Pridedame treniruojamas/ne informaciją
    detailsHtml += `
                    <tr>
                        <td>Treniruojamas</td>
                        <td>${layer.trainable ? 'Taip' : 'Ne'}</td>
                    </tr>
                </table>
            </div>
        </div>
    `;
    
    // Įrašome HTML į detalios informacijos konteinerį
    detailsContainer.innerHTML = detailsHtml;
    
    // Slenkame prie detalios informacijos
    detailsContainer.scrollIntoView({ behavior: 'smooth' });
}

/**
 * Išplečia visus sluoksnius
 */
function expandAllLayers() {
    // Einame per visus sluoksnius
    modelLayers.forEach((layer, index) => {
        // Randame sluoksnio elementą
        const layerElement = document.getElementById(`layer-${index}`);
        if (layerElement) {
            // Nustatome didesnį dydį
            layerElement.style.height = 'auto';
            layerElement.style.width = '250px';
            
            // Rodome visą informaciją
            layerElement.classList.add('expanded');
        }
    });
    
    // Atnaujiname jungiamąsias linijas
    updateConnectors();
}

/**
 * Sutraukia visus sluoksnius
 */
function collapseAllLayers() {
    // Einame per visus sluoksnius
    modelLayers.forEach((layer, index) => {
        // Randame sluoksnio elementą
        const layerElement = document.getElementById(`layer-${index}`);
        if (layerElement) {
            // Nustatome originalų dydį
            layerElement.style.height = '';
            layerElement.style.width = '';
            
            // Paslepiame papildomą informaciją
            layerElement.classList.remove('expanded');
        }
    });
    
    // Atnaujiname jungiamąsias linijas
    updateConnectors();
}

/**
 * Atnaujiname jungiamąsias linijas
 */
function updateConnectors() {
    // Šią funkciją būtų galima naudoti, jei būtų sudėtingesnės linijos
    console.log('Jungiamosios linijos atnaujintos');
}

/**
 * Išsaugo dabartinį vaizdą kaip HTML5 Canvas paveikslėlį
 */
function saveAsImage() {
    // Gauname vizualizacijos konteinerį
    const container = document.getElementById('layers-visualization');
    if (!container) return;
    
    // HTML į PNG konversiją būtų galima atlikti su html2canvas biblioteka
    alert('Funkcionalumas dar kuriamas. Naudokite eksporto mygtuką statiniame režime.');
}

/**
 * Ieško sluoksnių pagal raktažodį
 * @param {string} keyword - Paieškos raktažodis
 */
function searchLayers(keyword) {
    // Jei raktažodis tuščias, rodome visus sluoksnius
    if (!keyword) {
        document.querySelectorAll('.layer-box').forEach(el => {
            el.style.display = 'block';
        });
        return;
    }
    
    // Konvertuojame į mažąsias raides
    keyword = keyword.toLowerCase();
    
    // Einame per visus sluoksnius
    modelLayers.forEach((layer, index) => {
        // Randame sluoksnio elementą
        const layerElement = document.getElementById(`layer-${index}`);
        if (layerElement) {
            // Tikriname ar sluoksnio pavadinimas arba tipas atitinka paiešką
            const nameMatch = layer.name.toLowerCase().includes(keyword);
            const typeMatch = layer.type.toLowerCase().includes(keyword);
            
            // Rodome arba slepiame sluoksnį
            layerElement.style.display = (nameMatch || typeMatch) ? 'block' : 'none';
        }
    });
}