// Kontekstinės pagalbos sistema - rodo pagalbos tekstus virš UI elementų
// Šis failas apima kontekstinės pagalbos funkcionalumą

// Pagalbos tekstų objektas - saugomi pagal elementų ID arba klases
const helpTexts = {
    // Modelių valdymo pagalba
    'create-model-btn': 'Sukurti naują prognozavimo modelį su pasirinktais parametrais',
    'import-model-btn': 'Importuoti anksčiau eksportuotą modelį iš failo',
    'model-list': 'Čia rodomi visi jūsų sukurti modeliai',
    'model-type-select': 'Pasirinkite modelio tipą - LSTM modeliai tinka ilgalaikėms prognozėms, GRU - trumpalaikėms',
    
    // Treniravimo užduočių pagalba
    'create-task-btn': 'Sukurti naują modelio treniravimo užduotį',
    'tasks-list': 'Čia rodomos visos suplanuotos ir vykdomos treniravimo užduotys',
    'task-calendar': 'Kalendoriaus vaizdas padeda planuoti užduotis laike',
    'epochs-input': 'Kiek kartų modelis apmokomas su visais duomenimis. Daugiau epochų gali duoti geresnį rezultatą, bet ilgiau trunka.',
    'batch-size-input': 'Duomenų kiekis, apdorojamas vienos iteracijos metu. Didesnis dydis gali paspartinti treniravimą, bet reikalauja daugiau atminties.',
    'learning-rate-input': 'Mokymosi žingsnio dydis. Mažesnė reikšmė reiškia lėtesnį, bet stabilesnį apmokymą.',
    
    // Validacijos ir testavimo pagalba
    'evaluate-model-btn': 'Įvertinti modelio tikslumą lyginant su testiniais duomenimis',
    'metrics-container': 'Čia rodomi modelio tikslumo metrikos ir grafikai',
    'confusion-matrix': 'Šis grafikas parodo, kaip dažnai modelis teisingai/neteisingai klasifikuoja duomenis',
    
    // Prognozių sudarymo pagalba
    'prediction-form': 'Formoje nurodykite parametrus naujai prognozei',
    'prediction-period': 'Laikotarpis, kuriam norite sudaryti prognozę',
    'prediction-interval': 'Intervalas tarp prognozuojamų taškų (valandos, dienos ir t.t.)',
    'prediction-result': 'Čia bus rodomi prognozės rezultatai',
    
    // Bendroji pagalba
    'sidebar': 'Pagrindinis navigacijos meniu - čia rasite visas pagrindines funkcijas',
    'user-dropdown': 'Vartotojo nustatymai ir atsijungimas',
    'notification-center': 'Pranešimų centras - čia rasite visus sistemos pranešimus'
};

// Inicializuojame kontekstinę pagalbą
document.addEventListener('DOMContentLoaded', function() {
    // Žymė, ar pagalba įjungta
    let helpEnabled = localStorage.getItem('contextualHelpEnabled') === 'true';
    
    // Sukuriame pagalbos jungiklį
    createHelpToggle(helpEnabled);
    
    // Inicializuojame pagalbos rodymą
    initializeContextualHelp(helpEnabled);
    
    // Pridedame pagalbos mygtuką į kiekvieną puslapį
    addHelpButton();
});

// Sukuria pagalbos jungiklį
function createHelpToggle(initialState) {
    // Ieškome vietos, kur įdėti jungiklį (dažniausiai navigacijos juostoje)
    const navbarRight = document.querySelector('.navbar-nav.ml-auto, .navbar-nav.ms-auto');
    
    if (navbarRight) {
        // Sukuriame jungiklio HTML
        const toggleHtml = `
            <li class="nav-item">
                <div class="form-check form-switch mt-2">
                    <input class="form-check-input" type="checkbox" id="help-toggle" ${initialState ? 'checked' : ''}>
                    <label class="form-check-label text-light" for="help-toggle">Pagalba</label>
                </div>
            </li>
        `;
        
        // Įterpiame prieš paskutinį elementą (dažniausiai prieš vartotojo meniu)
        navbarRight.insertAdjacentHTML('afterbegin', toggleHtml);
        
        // Pridedame įvykio klausymą
        const toggle = document.getElementById('help-toggle');
        if (toggle) {
            toggle.addEventListener('change', function() {
                const helpEnabled = this.checked;
                localStorage.setItem('contextualHelpEnabled', helpEnabled);
                
                // Atnaujiname pagalbos rodymą
                initializeContextualHelp(helpEnabled);
                
                // Rodome pranešimą
                if (helpEnabled) {
                    showNotification('Kontekstinė pagalba įjungta', 'Užveskite pelę ant elementų, kad pamatytumėte pagalbos tekstus.');
                } else {
                    showNotification('Kontekstinė pagalba išjungta', 'Pagalba nebus rodoma.');
                }
            });
        }
    }
}

// Inicializuoja kontekstinę pagalbą
function initializeContextualHelp(enabled) {
    if (!enabled) {
        // Pašaliname visus esamus pagalbos tekstus
        document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => {
            if (el._tippy) {
                el._tippy.destroy();
            } else if (window.bootstrap && bootstrap.Tooltip) {
                const tooltip = bootstrap.Tooltip.getInstance(el);
                if (tooltip) {
                    tooltip.dispose();
                }
            }
        });
        return;
    }
    
    // Pridedame pagalbos tekstus elementams pagal ID arba klasę
    for (const selector in helpTexts) {
        const elements = document.querySelectorAll(`#${selector}, .${selector}`);
        
        elements.forEach(element => {
            // Pridedame tooltip atributus
            element.setAttribute('data-bs-toggle', 'tooltip');
            element.setAttribute('data-bs-placement', 'top');
            element.setAttribute('title', helpTexts[selector]);
            
            // Inicializuojame tooltip (jei naudojame Bootstrap)
            if (window.bootstrap && bootstrap.Tooltip) {
                new bootstrap.Tooltip(element);
            } 
            // Arba inicializuojame paprastą title atributą
        });
    }
}

// Rodo pranešimą vartotojui
function showNotification(title, message) {
    // Jei yra BTCNotifications objektas, naudojame jį
    if (window.BTCNotifications) {
        BTCNotifications.showNotification(title, message, 'info');
        return;
    }
    
    // Kitaip rodome paprastą laikinąjį pranešimą
    const notification = document.createElement('div');
    notification.className = 'alert alert-info alert-dismissible fade show';
    notification.style.position = 'fixed';
    notification.style.top = '20px';
    notification.style.right = '20px';
    notification.style.zIndex = '9999';
    notification.innerHTML = `
        <strong>${title}</strong><br>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Automatiškai uždarome po 5 sekundžių
    setTimeout(() => {
        notification.remove();
    }, 5000);
}

// Prideda pagalbos mygtuką į puslapį
function addHelpButton() {
    // Sukuriame mygtuką
    const helpButton = document.createElement('div');
    helpButton.className = 'help-button';
    helpButton.innerHTML = '<i class="fas fa-question-circle"></i>';
    helpButton.style.position = 'fixed';
    helpButton.style.bottom = '20px';
    helpButton.style.right = '20px';
    helpButton.style.backgroundColor = '#007bff';
    helpButton.style.color = '#fff';
    helpButton.style.width = '50px';
    helpButton.style.height = '50px';
    helpButton.style.borderRadius = '50%';
    helpButton.style.display = 'flex';
    helpButton.style.justifyContent = 'center';
    helpButton.style.alignItems = 'center';
    helpButton.style.cursor = 'pointer';
    helpButton.style.fontSize = '24px';
    helpButton.style.boxShadow = '0 2px 5px rgba(0,0,0,0.3)';
    helpButton.style.zIndex = '999';
    
    // Pridedame įvykių klausymą
    helpButton.addEventListener('click', function() {
        // Atidarome pagalbos puslapį
        window.open('/docs', '_blank');
    });
    
    // Pridedame tooltip
    helpButton.setAttribute('data-bs-toggle', 'tooltip');
    helpButton.setAttribute('data-bs-placement', 'left');
    helpButton.setAttribute('title', 'Pagalbos centras');
    
    // Įdedame į dokumentą
    document.body.appendChild(helpButton);
    
    // Inicializuojame tooltip, jei galima
    if (window.bootstrap && bootstrap.Tooltip) {
        new bootstrap.Tooltip(helpButton);
    }
}