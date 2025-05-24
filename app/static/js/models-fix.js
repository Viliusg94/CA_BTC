/**
 * Fixed Models page JavaScript with proper error handling
 */

// Global variables
let modelsData = {};
let refreshInterval = null;
let isRefreshing = false;

// Initialize the models page
document.addEventListener('DOMContentLoaded', function() {
    console.log('Models page loaded - initializing...');
    
    // Small delay to ensure DOM is fully ready
    setTimeout(() => {
        initializeModelsPage();
    }, 100);
});

// Main initialization function
function initializeModelsPage() {
    console.log('Initializing models page...');
    
    // Start auto-refresh
    startAutoRefresh();
    
    // Initial load
    setTimeout(() => {
        refreshModelsList();
    }, 500);
    
    // Add event listeners
    setupEventListeners();
}

// Utility functions for error handling
function showError(message, containerId = 'error-container') {
    console.error('Error:', message);
    
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = `
            <div class="alert alert-danger alert-dismissible fade show" role="alert">
                <i class="fas fa-exclamation-triangle me-2"></i>
                <strong>Klaida:</strong> ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        `;
        container.style.display = 'block';
    }
    
    // Auto-hide after 10 seconds
    setTimeout(() => hideError(containerId), 10000);
}

function hideError(containerId = 'error-container') {
    const container = document.getElementById(containerId);
    if (container) {
        container.style.display = 'none';
        container.innerHTML = '';
    }
}

function showSuccess(message, containerId = 'success-container') {
    console.log('Success:', message);
    
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = `
            <div class="alert alert-success alert-dismissible fade show" role="alert">
                <i class="fas fa-check-circle me-2"></i>
                <strong>Sėkmingai:</strong> ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        `;
        container.style.display = 'block';
    }
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        if (container) {
            container.style.display = 'none';
            container.innerHTML = '';
        }
    }, 5000);
}

// Main function to refresh models list
window.refreshModelsList = function() {
    if (isRefreshing) {
        console.log('Already refreshing, skipping...');
        return Promise.resolve();
    }
    
    isRefreshing = true;
    console.log('Refreshing models list...');
    
    // Show loading state
    showLoadingState();
    
    return fetch('/api/model_history_db')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Models data received:', data);
            
            if (data.success && data.models) {
                modelsData = data.models;
                renderModelsTable(data.models);
                updateSummaryStats(data.models);
                hideError(); // Hide any previous errors
                console.log('Models list updated successfully');
            } else {
                throw new Error(data.error || 'Invalid response format');
            }
        })
        .catch(error => {
            console.error('Error fetching models:', error);
            console.error('Error type:', error.constructor.name);
            console.error('Error stack:', error.stack);
            
            handleRefreshError(error);
        })
        .finally(() => {
            isRefreshing = false;
            hideLoadingState();
        });
};

// Error handling for refresh
function handleRefreshError(error) {
    console.log('Refresh error details:', error);
    console.log('Original error:', error);
    
    let errorMessage = 'Nepavyko užkrauti modelių duomenų';
    
    if (error.message.includes('404')) {
        errorMessage = 'API endpoint nerastas - patikrinkite serverio konfigūraciją';
    } else if (error.message.includes('500')) {
        errorMessage = 'Serverio klaida - patikrinkite serverio logus';
    } else if (error.message.includes('Failed to fetch')) {
        errorMessage = 'Nepavyko prisijungti prie serverio - patikrinkite internetą';
    } else if (error.message) {
        errorMessage = error.message;
    }
    
    showError(errorMessage);
    
    // Show fallback message in models container
    const modelsContainer = document.getElementById('models-container');
    if (modelsContainer) {
        modelsContainer.innerHTML = `
            <div class="text-center py-5">
                <i class="fas fa-exclamation-triangle fa-3x text-warning mb-3"></i>
                <h5 class="text-muted">Nepavyko užkrauti modelių</h5>
                <p class="text-muted">${errorMessage}</p>
                <button class="btn btn-primary" onclick="refreshModelsList()">
                    <i class="fas fa-sync-alt me-2"></i>Bandyti dar kartą
                </button>
            </div>
        `;
    }
}

// Show loading state
function showLoadingState() {
    const modelsContainer = document.getElementById('models-container');
    if (modelsContainer) {
        modelsContainer.innerHTML = `
            <div class="text-center py-5">
                <div class="spinner-border text-primary mb-3" role="status">
                    <span class="visually-hidden">Kraunama...</span>
                </div>
                <h5 class="text-muted">Kraunami modeliai...</h5>
            </div>
        `;
    }
    
    // Disable refresh button
    const refreshBtn = document.getElementById('refresh-models-btn');
    if (refreshBtn) {
        refreshBtn.disabled = true;
        refreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Kraunama...';
    }
}

// Hide loading state
function hideLoadingState() {
    const refreshBtn = document.getElementById('refresh-models-btn');
    if (refreshBtn) {
        refreshBtn.disabled = false;
        refreshBtn.innerHTML = '<i class="fas fa-sync-alt me-2"></i>Atnaujinti';
    }
}

// Render models table
function renderModelsTable(models) {
    const container = document.getElementById('models-container');
    if (!container) {
        console.error('Models container not found');
        return;
    }
    
    if (!models || models.length === 0) {
        container.innerHTML = `
            <div class="text-center py-5">
                <i class="fas fa-database fa-3x text-muted mb-3"></i>
                <h5 class="text-muted">Modelių nerasta</h5>
                <p class="text-muted">Pradėkite modelio mokymą, kad pamatytumėte rezultatus čia</p>
                <a href="/real_training" class="btn btn-primary">
                    <i class="fas fa-plus me-2"></i>Pradėti mokymą
                </a>
            </div>
        `;
        return;
    }
    
    // Sort models by timestamp (newest first)
    const sortedModels = models.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
    
    let tableHtml = `
        <div class="table-responsive">
            <table class="table table-dark table-hover">
                <thead>
                    <tr>
                        <th><i class="fas fa-robot me-2"></i>Modelio tipas</th>
                        <th><i class="fas fa-chart-line me-2"></i>R² Score</th>
                        <th><i class="fas fa-ruler me-2"></i>MAE</th>
                        <th><i class="fas fa-square-root-alt me-2"></i>RMSE</th>
                        <th><i class="fas fa-clock me-2"></i>Sukurta</th>
                        <th><i class="fas fa-cog me-2"></i>Epochos</th>
                        <th><i class="fas fa-toggle-on me-2"></i>Būsena</th>
                        <th><i class="fas fa-tools me-2"></i>Veiksmai</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    sortedModels.forEach((model, index) => {
        const isActive = model.is_active;
        const statusBadge = isActive ? 
            '<span class="badge bg-success"><i class="fas fa-check me-1"></i>Aktyvus</span>' : 
            '<span class="badge bg-secondary"><i class="fas fa-pause me-1"></i>Neaktyvus</span>';
        
        const r2Score = model.r2 !== null ? model.r2.toFixed(4) : 'N/A';
        const mae = model.mae !== null ? model.mae.toFixed(2) : 'N/A';
        const rmse = model.rmse !== null ? model.rmse.toFixed(2) : 'N/A';
        const epochs = model.epochs || 'N/A';
        
        const timestamp = model.timestamp ? new Date(model.timestamp).toLocaleString('lt-LT') : 'N/A';
        
        // Performance indicator
        let performanceClass = 'text-muted';
        let performanceIcon = 'fas fa-question';
        
        if (model.r2 !== null) {
            if (model.r2 >= 0.8) {
                performanceClass = 'text-success';
                performanceIcon = 'fas fa-star';
            } else if (model.r2 >= 0.6) {
                performanceClass = 'text-warning';
                performanceIcon = 'fas fa-star-half-alt';
            } else {
                performanceClass = 'text-danger';
                performanceIcon = 'fas fa-exclamation-triangle';
            }
        }
        
        tableHtml += `
            <tr class="${isActive ? 'table-success' : ''}" data-model-id="${model.id}">
                <td>
                    <strong class="text-primary">${model.model_type}</strong>
                    <br>
                    <small class="text-muted">ID: ${model.id}</small>
                </td>
                <td>
                    <span class="${performanceClass}">
                        <i class="${performanceIcon} me-1"></i>${r2Score}
                    </span>
                </td>
                <td><span class="text-info">${mae}</span></td>
                <td><span class="text-warning">${rmse}</span></td>
                <td>
                    <small>${timestamp}</small>
                </td>
                <td><span class="badge bg-info">${epochs}</span></td>
                <td>${statusBadge}</td>
                <td>
                    <div class="btn-group btn-group-sm">
                        ${!isActive ? `
                            <button class="btn btn-outline-success btn-sm" onclick="activateModel(${model.id})" title="Aktyvuoti modelį">
                                <i class="fas fa-play"></i>
                            </button>
                        ` : `
                            <button class="btn btn-outline-warning btn-sm" onclick="deactivateModel(${model.id})" title="Deaktyvuoti modelį">
                                <i class="fas fa-pause"></i>
                            </button>
                        `}
                        <button class="btn btn-outline-info btn-sm" onclick="viewModelDetails(${model.id})" title="Peržiūrėti detales">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button class="btn btn-outline-danger btn-sm" onclick="deleteModel(${model.id})" title="Ištrinti modelį">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    });
    
    tableHtml += `
                </tbody>
            </table>
        </div>
    `;
    
    container.innerHTML = tableHtml;
}

// Update summary statistics
function updateSummaryStats(models) {
    if (!models || models.length === 0) {
        document.getElementById('total-models').textContent = '0';
        document.getElementById('active-models').textContent = '0';
        document.getElementById('best-r2').textContent = 'N/A';
        document.getElementById('avg-mae').textContent = 'N/A';
        return;
    }
    
    const totalModels = models.length;
    const activeModels = models.filter(m => m.is_active).length;
    
    // Calculate best R² score
    const validR2Models = models.filter(m => m.r2 !== null && m.r2 !== undefined);
    const bestR2 = validR2Models.length > 0 ? Math.max(...validR2Models.map(m => m.r2)) : null;
    
    // Calculate average MAE
    const validMAEModels = models.filter(m => m.mae !== null && m.mae !== undefined);
    const avgMAE = validMAEModels.length > 0 ? 
        validMAEModels.reduce((sum, m) => sum + m.mae, 0) / validMAEModels.length : null;
    
    // Update DOM elements
    document.getElementById('total-models').textContent = totalModels;
    document.getElementById('active-models').textContent = activeModels;
    document.getElementById('best-r2').textContent = bestR2 !== null ? bestR2.toFixed(4) : 'N/A';
    document.getElementById('avg-mae').textContent = avgMAE !== null ? avgMAE.toFixed(2) : 'N/A';
}

// Model action functions
window.activateModel = function(modelId) {
    if (confirm('Ar tikrai norite aktyvuoti šį modelį? Kiti modeliai bus deaktyvuoti.')) {
        fetch(`/api/activate_model/${modelId}`, {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showSuccess('Modelis sėkmingai aktyvuotas');
                refreshModelsList();
            } else {
                showError(data.error || 'Nepavyko aktyvuoti modelio');
            }
        })
        .catch(error => {
            showError('Klaida aktyvuojant modelį: ' + error.message);
        });
    }
};

window.deactivateModel = function(modelId) {
    if (confirm('Ar tikrai norite deaktyvuoti šį modelį?')) {
        fetch(`/api/deactivate_model/${modelId}`, {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showSuccess('Modelis sėkmingai deaktyvuotas');
                refreshModelsList();
            } else {
                showError(data.error || 'Nepavyko deaktyvuoti modelio');
            }
        })
        .catch(error => {
            showError('Klaida deaktyvuojant modelį: ' + error.message);
        });
    }
};

window.deleteModel = function(modelId) {
    if (confirm('Ar tikrai norite ištrinti šį modelį? Šis veiksmas negrįžtamas!')) {
        fetch(`/api/delete_model/${modelId}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showSuccess('Modelis sėkmingai ištrintas');
                refreshModelsList();
            } else {
                showError(data.error || 'Nepavyko ištrinti modelio');
            }
        })
        .catch(error => {
            showError('Klaida trinant modelį: ' + error.message);
        });
    }
};

window.viewModelDetails = function(modelId) {
    const model = modelsData.find(m => m.id === modelId);
    if (!model) {
        showError('Modelio duomenys nerasti');
        return;
    }
    
    // Create and show modal with model details
    const modalHtml = `
        <div class="modal fade" id="modelDetailsModal" tabindex="-1" aria-hidden="true">
            <div class="modal-dialog modal-lg">
                <div class="modal-content bg-dark">
                    <div class="modal-header border-secondary">
                        <h5 class="modal-title text-primary">
                            <i class="fas fa-robot me-2"></i>Modelio Detalės: ${model.model_type}
                        </h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="row">
                            <div class="col-md-6">
                                <h6 class="text-warning"><i class="fas fa-chart-line me-2"></i>Našumo Metrikų</h6>
                                <ul class="list-group list-group-flush">
                                    <li class="list-group-item bg-transparent border-secondary text-light">
                                        <strong>R² Score:</strong> ${model.r2 !== null ? model.r2.toFixed(6) : 'N/A'}
                                    </li>
                                    <li class="list-group-item bg-transparent border-secondary text-light">
                                        <strong>MAE:</strong> ${model.mae !== null ? model.mae.toFixed(4) : 'N/A'}
                                    </li>
                                    <li class="list-group-item bg-transparent border-secondary text-light">
                                        <strong>MSE:</strong> ${model.mse !== null ? model.mse.toFixed(4) : 'N/A'}
                                    </li>
                                    <li class="list-group-item bg-transparent border-secondary text-light">
                                        <strong>RMSE:</strong> ${model.rmse !== null ? model.rmse.toFixed(4) : 'N/A'}
                                    </li>
                                    <li class="list-group-item bg-transparent border-secondary text-light">
                                        <strong>Training Loss:</strong> ${model.training_loss !== null ? model.training_loss.toFixed(6) : 'N/A'}
                                    </li>
                                    <li class="list-group-item bg-transparent border-secondary text-light">
                                        <strong>Validation Loss:</strong> ${model.validation_loss !== null ? model.validation_loss.toFixed(6) : 'N/A'}
                                    </li>
                                </ul>
                            </div>
                            <div class="col-md-6">
                                <h6 class="text-info"><i class="fas fa-cogs me-2"></i>Mokymo Parametrai</h6>
                                <ul class="list-group list-group-flush">
                                    <li class="list-group-item bg-transparent border-secondary text-light">
                                        <strong>Epochos:</strong> ${model.epochs || 'N/A'}
                                    </li>
                                    <li class="list-group-item bg-transparent border-secondary text-light">
                                        <strong>Batch Size:</strong> ${model.batch_size || 'N/A'}
                                    </li>
                                    <li class="list-group-item bg-transparent border-secondary text-light">
                                        <strong>Learning Rate:</strong> ${model.learning_rate || 'N/A'}
                                    </li>
                                    <li class="list-group-item bg-transparent border-secondary text-light">
                                        <strong>Lookback:</strong> ${model.lookback || 'N/A'}
                                    </li>
                                    <li class="list-group-item bg-transparent border-secondary text-light">
                                        <strong>Dropout:</strong> ${model.dropout || 'N/A'}
                                    </li>
                                    <li class="list-group-item bg-transparent border-secondary text-light">
                                        <strong>Validation Split:</strong> ${model.validation_split || 'N/A'}
                                    </li>
                                </ul>
                            </div>
                        </div>
                        
                        <div class="mt-4">
                            <h6 class="text-success"><i class="fas fa-info-circle me-2"></i>Papildoma Informacija</h6>
                            <ul class="list-group list-group-flush">
                                <li class="list-group-item bg-transparent border-secondary text-light">
                                    <strong>ID:</strong> ${model.id}
                                </li>
                                <li class="list-group-item bg-transparent border-secondary text-light">
                                    <strong>Sukurta:</strong> ${model.timestamp ? new Date(model.timestamp).toLocaleString('lt-LT') : 'N/A'}
                                </li>
                                <li class="list-group-item bg-transparent border-secondary text-light">
                                    <strong>Mokymo Laikas:</strong> ${model.training_time ? model.training_time.toFixed(2) + 's' : 'N/A'}
                                </li>
                                <li class="list-group-item bg-transparent border-secondary text-light">
                                    <strong>Aktyvus:</strong> ${model.is_active ? 
                                        '<span class="badge bg-success">Taip</span>' : 
                                        '<span class="badge bg-secondary">Ne</span>'}
                                </li>
                                ${model.notes ? `
                                <li class="list-group-item bg-transparent border-secondary text-light">
                                    <strong>Pastabos:</strong> ${model.notes}
                                </li>
                                ` : ''}
                            </ul>
                        </div>
                        
                        ${model.model_params ? `
                        <div class="mt-4">
                            <h6 class="text-primary"><i class="fas fa-code me-2"></i>Modelio Parametrai</h6>
                            <pre class="bg-secondary p-3 rounded"><code>${model.model_params}</code></pre>
                        </div>
                        ` : ''}
                    </div>
                    <div class="modal-footer border-secondary">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Uždaryti</button>
                        ${!model.is_active ? `
                            <button type="button" class="btn btn-success" onclick="activateModel(${model.id}); bootstrap.Modal.getInstance(document.getElementById('modelDetailsModal')).hide();">
                                <i class="fas fa-play me-2"></i>Aktyvuoti
                            </button>
                        ` : `
                            <button type="button" class="btn btn-warning" onclick="deactivateModel(${model.id}); bootstrap.Modal.getInstance(document.getElementById('modelDetailsModal')).hide();">
                                <i class="fas fa-pause me-2"></i>Deaktyvuoti
                            </button>
                        `}
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Remove existing modal if any
    const existingModal = document.getElementById('modelDetailsModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Add modal to body
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('modelDetailsModal'));
    modal.show();
    
    // Clean up modal when hidden
    document.getElementById('modelDetailsModal').addEventListener('hidden.bs.modal', function() {
        this.remove();
    });
};

// Setup event listeners
function setupEventListeners() {
    // Refresh button
    const refreshBtn = document.getElementById('refresh-models-btn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            refreshModelsList();
        });
    }
    
    // Auto-refresh checkbox
    const autoRefreshCheckbox = document.getElementById('auto-refresh');
    if (autoRefreshCheckbox) {
        autoRefreshCheckbox.addEventListener('change', function() {
            if (this.checked) {
                startAutoRefresh();
            } else {
                stopAutoRefresh();
            }
        });
    }
    
    // Filter buttons
    const filterBtns = document.querySelectorAll('.filter-btn');
    filterBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const filter = this.dataset.filter;
            applyFilter(filter);
            
            // Update active button
            filterBtns.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
        });
    });
}

// Auto-refresh functionality
function startAutoRefresh() {
    stopAutoRefresh(); // Stop any existing interval
    
    refreshInterval = setInterval(() => {
        if (!isRefreshing) {
            console.log('Auto-refreshing models...');
            refreshModelsList();
        }
    }, 30000); // Refresh every 30 seconds
    
    console.log('Auto-refresh started');
}

function stopAutoRefresh() {
    if (refreshInterval) {
        clearInterval(refreshInterval);
        refreshInterval = null;
        console.log('Auto-refresh stopped');
    }
}

// Filter functionality
function applyFilter(filter) {
    const rows = document.querySelectorAll('#models-container tbody tr');
    
    rows.forEach(row => {
        const modelType = row.querySelector('td:first-child strong').textContent.toLowerCase();
        const isActive = row.classList.contains('table-success');
        
        let show = true;
        
        switch(filter) {
            case 'active':
                show = isActive;
                break;
            case 'inactive':
                show = !isActive;
                break;
            case 'lstm':
                show = modelType === 'lstm';
                break;
            case 'gru':
                show = modelType === 'gru';
                break;
            case 'cnn':
                show = modelType === 'cnn';
                break;
            case 'transformer':
                show = modelType === 'transformer';
                break;
            case 'all':
            default:
                show = true;
                break;
        }
        
        row.style.display = show ? '' : 'none';
    });
}

// Cleanup when page is unloaded
window.addEventListener('beforeunload', function() {
    stopAutoRefresh();
});

// Export functions for testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        refreshModelsList,
        activateModel,
        deactivateModel,
        deleteModel,
        viewModelDetails,
        showError,
        hideError,
        showSuccess
    };
}

// Fix model training status refresh issues

document.addEventListener('DOMContentLoaded', function() {
    console.log('models-fix.js loaded');
    loadModelsList();
    
    // Form submission for training
    const trainingForm = document.getElementById('training-form');
    if (trainingForm) {
        trainingForm.addEventListener('submit', function(event) {
            event.preventDefault();
            console.log('Training form submitted');
            
            // Disable the button and show loading state
            const submitBtn = document.querySelector('#train-btn');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Pradedamas apmokymas...';
            }
            
            // Get form data
            const formData = new FormData(trainingForm);
            
            // Log the form data being sent
            console.log('Sending form data:');
            for (let [key, value] of formData.entries()) {
                console.log(`${key}: ${value}`);
            }
            
            // Send form data to API
            fetch('/api/train_model', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                console.log('Training response:', data);
                
                if (data.success) {
                    // Show success message
                    showAlert('success', `Modelio ${formData.get('model_type').toUpperCase()} apmokymas pradėtas sėkmingai!`);
                    
                    // Re-enable button
                    if (submitBtn) {
                        submitBtn.disabled = false;
                        submitBtn.innerHTML = '<i class="fas fa-play-circle"></i> Pradėti Apmokymą';
                    }
                    
                    // Redirect to training status page
                    setTimeout(() => {
                        window.location.href = '/training_status';
                    }, 1000);
                } else {
                    // Show error message
                    showAlert('danger', `Klaida: ${data.error || 'Nepavyko pradėti apmokymo'}`);
                    
                    // Re-enable button
                    if (submitBtn) {
                        submitBtn.disabled = false;
                        submitBtn.innerHTML = '<i class="fas fa-play-circle"></i> Pradėti Apmokymą';
                    }
                }
            })
            .catch(error => {
                console.error('Error starting training:', error);
                showAlert('danger', 'Klaida siunčiant užklausą');
                
                // Re-enable button
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = '<i class="fas fa-play-circle"></i> Pradėti Apmokymą';
                }
            });
        });
    }
    
    // Add refresh models button handler
    const refreshBtn = document.getElementById('refresh-models-btn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            loadModelsList();
        });
    }
});

// Function to load models list
function loadModelsList() {
    console.log('Loading models list...');
    
    const modelsContainer = document.getElementById('models-container');
    if (!modelsContainer) {
        console.error('Models container not found');
        return;
    }
    
    // Show loading spinner
    modelsContainer.innerHTML = `
        <div class="text-center py-5">
            <div class="spinner-border text-primary mb-3" role="status">
                <span class="visually-hidden">Kraunama...</span>
            </div>
            <h5 class="text-muted">Kraunami modeliai...</h5>
        </div>
    `;
    
    // Fetch models from API
    fetch('/api/model_history_db')
        .then(response => {
            console.log('Model history response status:', response.status);
            return response.json();
        })
        .then(data => {
            console.log('Model history response data:', data);
            
            if (data.success && data.models) {
                // Process and display models
                displayModels(data.models);
            } else {
                // Show error
                modelsContainer.innerHTML = `
                    <div class="alert alert-warning">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        Nepavyko gauti modelių sąrašo. ${data.error || ''}
                    </div>
                `;
            }
        })
        .catch(error => {
            console.error('Error loading models:', error);
            modelsContainer.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-circle me-2"></i>
                    Klaida kraunant modelius: ${error.message}
                </div>
            `;
        });
}

// Display models in a table
function displayModels(models) {
    console.log(`Displaying ${models.length} models`);
    
    const modelsContainer = document.getElementById('models-container');
    if (!modelsContainer) return;
    
    // Group models by type
    const modelsByType = {};
    models.forEach(model => {
        if (!modelsByType[model.model_type]) {
            modelsByType[model.model_type] = [];
        }
        modelsByType[model.model_type].push(model);
    });
    
    // Update stats
    document.getElementById('total-models').textContent = models.length;
    document.getElementById('active-models').textContent = models.filter(m => m.is_active).length;
    
    // Find best R2 score
    const bestR2 = Math.max(...models.filter(m => m.r2 !== null).map(m => m.r2), 0);
    document.getElementById('best-r2').textContent = bestR2 > 0 ? bestR2.toFixed(4) : 'N/A';
    
    // Calculate average MAE
    const validMaeValues = models.filter(m => m.mae !== null).map(m => m.mae);
    const avgMae = validMaeValues.length > 0 ? validMaeValues.reduce((a, b) => a + b, 0) / validMaeValues.length : 0;
    document.getElementById('avg-mae').textContent = avgMae > 0 ? avgMae.toFixed(2) : 'N/A';
    
    // Create HTML for each model type
    let html = '';
    
    // Store models globally for other functions to access
    window.modelsData = models;
    
    Object.keys(modelsByType).forEach(modelType => {
        const typeModels = modelsByType[modelType].sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
        
        html += `
            <div class="card mb-4">
                <div class="card-header bg-primary text-white">
                    <h5 class="mb-0">${modelType} Modeliai (${typeModels.length})</h5>
                </div>
                <div class="card-body p-0">
                    <div class="table-responsive">
                        <table class="table table-hover table-striped mb-0">
                            <thead>
                                <tr>
                                    <th>ID</th>
                                    <th>Data</th>
                                    <th>R²</th>
                                    <th>MAE</th>
                                    <th>Epochos</th>
                                    <th>Būsena</th>
                                    <th>Veiksmai</th>
                                </tr>
                            </thead>
                            <tbody>
        `;
        
        typeModels.forEach(model => {
            const date = new Date(model.timestamp).toLocaleString('lt-LT');
            const isActive = model.is_active;
            
            html += `
                <tr>
                    <td>${model.id}</td>
                    <td>${date}</td>
                    <td>${model.r2 !== null ? model.r2.toFixed(4) : 'N/A'}</td>
                    <td>${model.mae !== null ? model.mae.toFixed(2) : 'N/A'}</td>
                    <td>${model.epochs || 'N/A'}</td>
                    <td>
                        ${isActive ? 
                            '<span class="badge bg-success">Aktyvus</span>' : 
                            '<span class="badge bg-secondary">Neaktyvus</span>'
                        }
                    </td>
                    <td>
                        <div class="btn-group btn-group-sm">
                            <button class="btn btn-outline-info" onclick="viewModelDetails(${model.id})">
                                <i class="fas fa-info-circle"></i>
                            </button>
                            ${isActive ? 
                                `<button class="btn btn-outline-secondary" disabled>
                                    <i class="fas fa-check-circle"></i>
                                </button>` : 
                                `<button class="btn btn-outline-success" onclick="activateModel(${model.id})">
                                    <i class="fas fa-check-circle"></i>
                                </button>`
                            }
                            <button class="btn btn-outline-danger" onclick="deleteModel(${model.id})">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        });
        
        html += `
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        `;
    });
    
    if (html === '') {
        html = `
            <div class="alert alert-info">
                <i class="fas fa-info-circle me-2"></i>
                Nėra apmokytų modelių. Pradėkite apmokymą naudodami formą viršuje.
            </div>
        `;
    }
    
    modelsContainer.innerHTML = html;
}

// Show alert messages
function showAlert(type, message) {
    const alertsContainer = document.getElementById('alerts-container');
    if (!alertsContainer) return;
    
    const alertId = 'alert-' + Date.now();
    const alertHtml = `
        <div id="${alertId}" class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;
    
    alertsContainer.innerHTML += alertHtml;
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        const alertElement = document.getElementById(alertId);
        if (alertElement) {
            alertElement.classList.remove('show');
            setTimeout(() => alertElement.remove(), 300);
        }
    }, 5000);
}

console.log('Models-fix.js loaded successfully');
