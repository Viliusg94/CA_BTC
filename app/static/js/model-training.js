/**
 * Model training status monitoring script
 */

// Function to update training status without page reload
function updateTrainingStatus() {
    const trainingStatusSection = document.getElementById('trainingStatusSection');
    
    if (!trainingStatusSection) return;
    
    // Get all model types from data attribute
    const modelTypes = document.querySelectorAll('[data-model-type]');
    const modelTypeSet = new Set();
    
    modelTypes.forEach(el => {
        const modelType = el.getAttribute('data-model-type');
        if (modelType) modelTypeSet.add(modelType);
    });
    
    // If no model types found, exit
    if (modelTypeSet.size === 0) return;
    
    // Check status for each model type
    modelTypeSet.forEach(modelType => {
        fetch(`/api/training_status/${modelType}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Update status indicator for this model
                    updateModelStatus(modelType, data);
                    
                    // Update the training status section if needed
                    if (data.is_training) {
                        refreshTrainingStatusSection();
                    }
                }
            })
            .catch(error => {
                console.error(`Error fetching training status for ${modelType}:`, error);
            });
    });
}

// Update the status indicator for a specific model
function updateModelStatus(modelType, data) {
    const statusIndicator = document.querySelector(`[data-status-indicator="${modelType}"]`);
    
    if (statusIndicator) {
        // Clear existing content
        statusIndicator.innerHTML = '';
        
        // Create new status badge
        const badge = document.createElement('span');
        badge.classList.add('badge');
        
        if (data.is_training) {
            badge.classList.add('bg-info');
            badge.textContent = 'Apmokomas';
            
            // Add progress information if available
            if (data.progress_percentage > 0) {
                const progressText = document.createElement('span');
                progressText.classList.add('ms-2');
                progressText.textContent = `${Math.round(data.progress_percentage)}%`;
                statusIndicator.appendChild(progressText);
            }
        } else if (data.model_status.status === 'Aktyvus') {
            badge.classList.add('bg-success');
            badge.textContent = 'Aktyvus';
        } else if (data.model_status.status === 'Klaida') {
            badge.classList.add('bg-danger');
            badge.textContent = 'Klaida';
        } else {
            badge.classList.add('bg-secondary');
            badge.textContent = data.model_status.status;
        }
        
        statusIndicator.appendChild(badge);
    }
}

// Refresh the training status section without full page reload
function refreshTrainingStatusSection() {
    fetch('/training_status_partial')
        .then(response => response.text())
        .then(html => {
            const trainingStatusSection = document.getElementById('trainingStatusSection');
            if (trainingStatusSection) {
                trainingStatusSection.innerHTML = html;
            }
        })
        .catch(error => {
            console.error('Error refreshing training status section:', error);
        });
}

// Initialize polling for training status updates
document.addEventListener('DOMContentLoaded', function() {
    // Start polling every 5 seconds
    setInterval(updateTrainingStatus, 5000);
    
    // Initial update
    updateTrainingStatus();
    
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.forEach(function(tooltipTriggerEl) {
        new bootstrap.Tooltip(tooltipTriggerEl);
    });
});
