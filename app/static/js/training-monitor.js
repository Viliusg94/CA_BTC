/**
 * Training monitor script for the Bitcoin Price Prediction App
 * This script handles real-time monitoring of model training progress
 */

// Function to check training status of all models
function checkAllModelsTrainingStatus() {
    // Get all model types from the page
    var modelTypeElements = document.querySelectorAll('[data-model-type]');
    var modelTypes = [];
    
    // Convert to array safely for older browsers
    for (var i = 0; i < modelTypeElements.length; i++) {
        modelTypes.push(modelTypeElements[i].getAttribute('data-model-type'));
    }
    
    // If no model types found, try with hardcoded defaults
    if (!modelTypes.length) {
        return checkDefaultModelsTrainingStatus();
    }
    
    var anyTraining = false;
    var promises = [];
    
    // Check status for each model type
    modelTypes.forEach(function(modelType) {
        var promise = fetch('/api/training_progress/' + modelType)
            .then(function(response) {
                if (!response.ok) {
                    throw new Error('HTTP error! Status: ' + response.status);
                }
                return response.json();
            })
            .then(function(data) {
                if (data.success) {
                    updateModelTrainingUI(modelType, data);
                    
                    if (data.is_training) {
                        anyTraining = true;
                        console.log('Model ' + modelType + ' is training: ' + data.progress.progress + '%');
                    }
                }
                return data.is_training;
            })
            .catch(function(error) {
                console.error('Error checking training status for ' + modelType + ':', error);
                return false;
            });
            
        promises.push(promise);
    });
    
    // Process all promises
    Promise.all(promises).then(function(results) {
        // If any model is training but page isn't showing it, reload
        var trainingBanner = document.querySelector('.training-status-banner');
        var anyModelTraining = false;
        
        for (var i = 0; i < results.length; i++) {
            if (results[i]) {
                anyModelTraining = true;
                break;
            }
        }
        
        if (anyModelTraining && !trainingBanner) {
            console.log('Training in progress but status banner not found, reloading page');
            location.reload();
        }
    });
}

// Fallback to check status of default model types
function checkDefaultModelsTrainingStatus() {
    var defaultModelTypes = ['lstm', 'gru', 'transformer', 'cnn', 'cnn_lstm'];
    var anyTraining = false;
    
    defaultModelTypes.forEach(function(modelType) {
        fetch('/api/training_progress/' + modelType)
            .then(function(response) {
                if (!response.ok) {
                    throw new Error('HTTP error! Status: ' + response.status);
                }
                return response.json();
            })
            .then(function(data) {
                if (data.success && data.is_training) {
                    anyTraining = true;
                    console.log('Model ' + modelType + ' is training: ' + data.progress.progress + '%');
                    
                    // If training is happening but UI doesn't show it, reload
                    var trainingBanner = document.querySelector('.training-status-banner');
                    if (!trainingBanner) {
                        console.log('Training in progress but status banner not found, reloading page');
                        location.reload();
                    }
                }
            })
            .catch(function(error) {
                console.error('Error checking training status for ' + modelType + ':', error);
            });
    });
}

// Update UI for a specific model's training status
function updateModelTrainingUI(modelType, data) {
    // Update progress container if exists
    var progressContainer = document.getElementById(modelType + 'ProgressContainer');
    var progressBar = document.getElementById(modelType + 'ProgressBar');
    var progressStatus = document.getElementById(modelType + 'ProgressStatus');
    
    if (progressContainer && progressBar && progressStatus) {
        if (data.is_training) {
            // Show progress container
            progressContainer.style.display = 'block';
            
            // Update progress bar
            var progress = data.progress.progress || 0;
            progressBar.style.width = progress + '%';
            progressBar.setAttribute('aria-valuenow', progress);
            progressBar.textContent = Math.round(progress) + '%';
            
            // Update status text
            progressStatus.textContent = 'Apmokomas: ' + Math.round(progress) + '%';
        } else {
            // Hide progress if not training
            progressContainer.style.display = 'none';
            
            // Update button if it's in "starting" state
            var trainButton = document.getElementById(modelType + 'TrainBtn');
            if (trainButton && trainButton.disabled) {
                trainButton.disabled = false;
                trainButton.innerHTML = '<i class="fas fa-play me-2"></i>Apmokyti modelį';
            }
        }
    }
}

// Initialize training monitoring
document.addEventListener('DOMContentLoaded', function() {
    console.log('Training monitor initialized');
    
    // Initial check
    checkAllModelsTrainingStatus();
    
    // Set up polling
    setInterval(checkAllModelsTrainingStatus, 5000);
});
