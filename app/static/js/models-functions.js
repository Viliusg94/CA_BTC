// Model action functions for models.html

// Activate model
window.activateModel = function(modelId) {
    console.log(`Activating model ${modelId}`);
    
    const modelType = getModelTypeById(modelId);
    if (!modelType) {
        showError('Modelio tipas nerastas');
        return;
    }
    
    fetch(`/api/use_model/${modelType}/${modelId}`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showSuccess(`Modelis #${modelId} sėkmingai aktyvuotas`);
            refreshModelsList();
        } else {
            throw new Error(data.error || 'Nepavyko aktyvuoti modelio');
        }
    })
    .catch(error => {
        console.error('Error activating model:', error);
        showError(`Klaida aktyvuojant modelį: ${error.message}`);
    });
};

// Deactivate model
window.deactivateModel = function(modelId) {
    console.log(`Deactivating model ${modelId}`);
    
    const modelType = getModelTypeById(modelId);
    if (!modelType) {
        showError('Modelio tipas nerastas');
        return;
    }
    
    // Since we don't have a specific deactivate endpoint, we'll use another model of same type
    // Or create a custom solution
    const modelsOfSameType = modelsData.filter(m => m.model_type === modelType && m.id !== modelId);
    
    if (modelsOfSameType.length > 0) {
        // Activate another model of the same type (which deactivates this one)
        const otherModelId = modelsOfSameType[0].id;
        
        fetch(`/api/use_model/${modelType}/${otherModelId}`, {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showSuccess(`Modelis #${modelId} deaktyvuotas, aktyvuotas modelis #${otherModelId}`);
                refreshModelsList();
            } else {
                throw new Error(data.error || 'Nepavyko deaktyvuoti modelio');
            }
        })
        .catch(error => {
            console.error('Error deactivating model:', error);
            showError(`Klaida deaktyvuojant modelį: ${error.message}`);
        });
    } else {
        showError(`Nėra kitų ${modelType.toUpperCase()} modelių, kuriuos būtų galima aktyvuoti vietoj šio.`);
    }
};

// Delete model
window.deleteModel = function(modelId) {
    console.log(`Deleting model ${modelId}`);
    
    if (!confirm(`Ar tikrai norite ištrinti modelį #${modelId}? Šio veiksmo negalima atšaukti.`)) {
        return;
    }
    
    const modelType = getModelTypeById(modelId);
    if (!modelType) {
        showError('Modelio tipas nerastas');
        return;
    }
    
    fetch(`/api/delete_model_history/${modelType}/${modelId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showSuccess(`Modelis #${modelId} sėkmingai ištrintas`);
            refreshModelsList();
        } else {
            throw new Error(data.error || 'Nepavyko ištrinti modelio');
        }
    })
    .catch(error => {
        console.error('Error deleting model:', error);
        showError(`Klaida trinant modelį: ${error.message}`);
    });
};

// View model details
window.viewModelDetails = function(modelId) {
    console.log(`Viewing model details for ${modelId}`);
    
    const model = modelsData.find(m => m.id === modelId);
    if (!model) {
        showError('Modelio informacija nerasta');
        return;
    }
    
    const timestamp = model.timestamp ? new Date(model.timestamp).toLocaleString('lt-LT') : 'N/A';
    
    let detailsHtml = `
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Modelio #${model.id} detalės</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <div class="row">
                        <div class="col-md-6">
                            <h6>Pagrindinė informacija</h6>
                            <ul class="list-group mb-3">
                                <li class="list-group-item d-flex justify-content-between">
                                    <span>Modelio tipas:</span>
                                    <strong>${model.model_type}</strong>
                                </li>
                                <li class="list-group-item d-flex justify-content-between">
                                    <span>Sukurtas:</span>
                                    <span>${timestamp}</span>
                                </li>
                                <li class="list-group-item d-flex justify-content-between">
                                    <span>Statusas:</span>
                                    <span>${model.is_active ? 
                                        '<span class="badge bg-success">Aktyvus</span>' : 
                                        '<span class="badge bg-secondary">Neaktyvus</span>'}</span>
                                </li>
                                <li class="list-group-item d-flex justify-content-between">
                                    <span>Epochos:</span>
                                    <span>${model.epochs || 'N/A'}</span>
                                </li>
                                <li class="list-group-item d-flex justify-content-between">
                                    <span>Batch dydis:</span>
                                    <span>${model.batch_size || 'N/A'}</span>
                                </li>
                                <li class="list-group-item d-flex justify-content-between">
                                    <span>Mokymosi greitis:</span>
                                    <span>${model.learning_rate || 'N/A'}</span>
                                </li>
                            </ul>
                        </div>
                        <div class="col-md-6">
                            <h6>Efektyvumo metrikos</h6>
                            <ul class="list-group mb-3">
                                <li class="list-group-item d-flex justify-content-between">
                                    <span>R² koeficientas:</span>
                                    <strong>${model.r2 !== null ? model.r2.toFixed(4) : 'N/A'}</strong>
                                </li>
                                <li class="list-group-item d-flex justify-content-between">
                                    <span>MAE:</span>
                                    <span>${model.mae !== null ? model.mae.toFixed(2) : 'N/A'}</span>
                                </li>
                                <li class="list-group-item d-flex justify-content-between">
                                    <span>MSE:</span>
                                    <span>${model.mse !== null ? model.mse.toFixed(2) : 'N/A'}</span>
                                </li>
                                <li class="list-group-item d-flex justify-content-between">
                                    <span>RMSE:</span>
                                    <span>${model.rmse !== null ? model.rmse.toFixed(2) : 'N/A'}</span>
                                </li>
                                <li class="list-group-item d-flex justify-content-between">
                                    <span>Apmokymo Loss:</span>
                                    <span>${model.training_loss !== null ? model.training_loss.toFixed(4) : 'N/A'}</span>
                                </li>
                                <li class="list-group-item d-flex justify-content-between">
                                    <span>Validacijos Loss:</span>
                                    <span>${model.validation_loss !== null ? model.validation_loss.toFixed(4) : 'N/A'}</span>
                                </li>
                            </ul>
                        </div>
                    </div>
                    
                    ${model.notes ? `
                    <div class="row mt-3">
                        <div class="col-12">
                            <h6>Pastabos</h6>
                            <div class="card">
                                <div class="card-body">
                                    ${model.notes}
                                </div>
                            </div>
                        </div>
                    </div>
                    ` : ''}
                    
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Uždaryti</button>
                    ${!model.is_active ? `
                        <button type="button" class="btn btn-success" onclick="activateModel(${model.id}); modal.hide();">
                            <i class="fas fa-play"></i> Aktyvuoti modelį
                        </button>
                    ` : ''}
                    <button type="button" class="btn btn-danger" onclick="deleteModel(${model.id}); modal.hide();">
                        <i class="fas fa-trash"></i> Ištrinti modelį
                    </button>
                </div>
            </div>
        </div>
    `;
    
    // Create and show modal
    const modalElement = document.createElement('div');
    modalElement.className = 'modal fade';
    modalElement.id = `model-details-${modelId}`;
    modalElement.innerHTML = detailsHtml;
    document.body.appendChild(modalElement);
    
    // Initialize and show Bootstrap modal
    const modal = new bootstrap.Modal(modalElement);
    modal.show();
    
    // Clean up when modal is hidden
    modalElement.addEventListener('hidden.bs.modal', function() {
        document.body.removeChild(modalElement);
    });
};

// Helper function to get model type by ID
function getModelTypeById(modelId) {
    const model = modelsData.find(m => m.id === modelId);
    return model ? model.model_type.toLowerCase() : null;
}

// Train model
function trainModel(formData) {
    console.log('Training model with form data:', formData);
    
    // Show loading state
    const trainBtn = document.getElementById('train-btn');
    if (trainBtn) {
        trainBtn.disabled = true;
        trainBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Pradedama...';
    }
    
    // Submit form with fetch API
    fetch('/api/train_model', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        console.log('Training started:', data);
        
        if (data.success) {
            showSuccess(`Modelio ${data.model_type.toUpperCase()} apmokymas pradėtas sėkmingai.`);
            
            // Redirect to training status page after short delay
            setTimeout(() => {
                window.location.href = '/training_status';
            }, 2000);
        } else {
            throw new Error(data.error || 'Unknown error starting training');
        }
    })
    .catch(error => {
        console.error('Training error:', error);
        showError(`Nepavyko pradėti apmokymo: ${error.message}`);
    })
    .finally(() => {
        // Reset button state
        if (trainBtn) {
            trainBtn.disabled = false;
            trainBtn.innerHTML = '<i class="fas fa-play-circle"></i> Pradėti Apmokymą';
        }
    });
}

// Show model-specific parameters
function showModelSpecificParams(modelType) {
    // Hide all parameter divs
    const paramDivs = document.querySelectorAll('.model-specific-params');
    paramDivs.forEach(div => {
        div.style.display = 'none';
    });
    
    // Show the selected model's parameters
    const selectedParamDiv = document.getElementById(`${modelType}-params`);
    if (selectedParamDiv) {
        selectedParamDiv.style.display = 'block';
    }
}
