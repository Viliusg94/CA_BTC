/**
 * Trading Dashboard JavaScript
 */

// Global variables
let selectedModel = null;
let availableModels = [];
let tradingChart = null;
let currentStrategy = 'bollinger_macd';

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing trading dashboard...');
    
    initializeEventHandlers();
    loadAvailableModels();
    initializeTradingChart();
    startLiveUpdates();
});

// Initialize event handlers
function initializeEventHandlers() {
    // Model selection
    document.getElementById('model-select').addEventListener('change', handleModelSelection);
    document.getElementById('apply-model-btn').addEventListener('click', applySelectedModel);
    document.getElementById('refresh-models-btn').addEventListener('click', loadAvailableModels);
    
    // Strategy configuration
    document.getElementById('strategy-select').addEventListener('change', handleStrategyChange);
    document.getElementById('risk-level').addEventListener('change', updateStrategyConfig);
    document.getElementById('position-size').addEventListener('change', updateStrategyConfig);
    
    // Backtest
    document.getElementById('run-backtest-btn').addEventListener('click', runBacktest);
}

// Load available models
async function loadAvailableModels() {
    try {
        console.log('Loading available models...');
        
        const response = await fetch('/api/models/available');
        const data = await response.json();
        
        if (data.success) {
            availableModels = data.models;
            populateModelSelect();
        } else {
            throw new Error(data.error || 'Failed to load models');
        }
    } catch (error) {
        console.error('Error loading models:', error);
        showError('Failed to load available models: ' + error.message);
    }
}

// Populate model selection dropdown
function populateModelSelect() {
    const select = document.getElementById('model-select');
    select.innerHTML = '<option value="">Select a model...</option>';
    
    availableModels.forEach(model => {
        const option = document.createElement('option');
        option.value = model.id;
        option.textContent = `${model.type.toUpperCase()} - R²: ${model.r2?.toFixed(3) || 'N/A'} - ${model.is_active ? 'Active' : 'Inactive'}`;
        option.dataset.modelType = model.type;
        option.dataset.accuracy = model.r2 || 0;
        option.dataset.mae = model.mae || 0;
        option.dataset.isActive = model.is_active;
        
        select.appendChild(option);
    });
}

// Handle model selection
function handleModelSelection() {
    const select = document.getElementById('model-select');
    const selectedOption = select.options[select.selectedIndex];
    
    if (select.value) {
        selectedModel = {
            id: select.value,
            type: selectedOption.dataset.modelType,
            accuracy: parseFloat(selectedOption.dataset.accuracy),
            mae: parseFloat(selectedOption.dataset.mae),
            isActive: selectedOption.dataset.isActive === 'true'
        };
        
        displayModelInfo(selectedModel);
        document.getElementById('apply-model-btn').disabled = false;
    } else {
        selectedModel = null;
        clearModelInfo();
        document.getElementById('apply-model-btn').disabled = true;
    }
}

// Display model information
function displayModelInfo(model) {
    const infoContainer = document.getElementById('model-info');
    
    const statusBadge = model.isActive ? 
        '<span class="badge bg-success">Active</span>' : 
        '<span class="badge bg-secondary">Inactive</span>';
    
    const accuracyColor = model.accuracy > 0.8 ? 'text-success' : 
                         model.accuracy > 0.6 ? 'text-warning' : 'text-danger';
    
    infoContainer.innerHTML = `
        <div class="alert alert-light border">
            <h6><i class="fas fa-brain"></i> ${model.type.toUpperCase()} Model ${statusBadge}</h6>
            <div class="row">
                <div class="col-6">
                    <small class="text-muted">Accuracy (R²):</small><br>
                    <span class="fw-bold ${accuracyColor}">${(model.accuracy * 100).toFixed(1)}%</span>
                </div>
                <div class="col-6">
                    <small class="text-muted">MAE:</small><br>
                    <span class="fw-bold">${model.mae.toFixed(2)}</span>
                </div>
            </div>
        </div>
    `;
    
    // Update performance metrics
    document.getElementById('model-accuracy').textContent = `${(model.accuracy * 100).toFixed(1)}%`;
}

// Clear model information
function clearModelInfo() {
    document.getElementById('model-info').innerHTML = `
        <div class="alert alert-info">
            <i class="fas fa-info-circle"></i>
            Select a model to view its performance metrics
        </div>
    `;
    
    document.getElementById('model-accuracy').textContent = '--';
}

// Apply selected model
async function applySelectedModel() {
    if (!selectedModel) {
        showError('No model selected');
        return;
    }
    
    try {
        const btn = document.getElementById('apply-model-btn');
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Applying...';
        
        const response = await fetch('/api/trading/set-model', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                model_id: selectedModel.id,
                model_type: selectedModel.type
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showSuccess(`${selectedModel.type.toUpperCase()} model applied successfully`);
            loadTradingSignals(); // Refresh signals with new model
        } else {
            throw new Error(data.error || 'Failed to apply model');
        }
    } catch (error) {
        console.error('Error applying model:', error);
        showError('Failed to apply model: ' + error.message);
    } finally {
        const btn = document.getElementById('apply-model-btn');
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-check"></i> Apply Selected Model';
    }
}

// Handle strategy change
function handleStrategyChange() {
    currentStrategy = document.getElementById('strategy-select').value;
    updateStrategyConfig();
    loadTradingSignals(); // Refresh signals with new strategy
}

// Update strategy configuration
function updateStrategyConfig() {
    const riskLevel = document.getElementById('risk-level').value;
    const positionSize = document.getElementById('position-size').value;
    
    console.log('Strategy config updated:', {
        strategy: currentStrategy,
        riskLevel: riskLevel,
        positionSize: positionSize
    });
    
    // Update risk-based parameters
    updateRiskParameters(riskLevel);
}

// Update risk parameters based on risk level
function updateRiskParameters(riskLevel) {
    let stopLoss, takeProfit;
    
    switch (riskLevel) {
        case 'conservative':
            stopLoss = 2; // 2%
            takeProfit = 3; // 3%
            break;
        case 'moderate':
            stopLoss = 3; // 3%
            takeProfit = 5; // 5%
            break;
        case 'aggressive':
            stopLoss = 5; // 5%
            takeProfit = 8; // 8%
            break;
    }
    
    console.log('Risk parameters:', { stopLoss, takeProfit, riskLevel });
}

// Load trading signals
async function loadTradingSignals() {
    try {
        const params = new URLSearchParams({
            strategy: currentStrategy,
            model_id: selectedModel?.id || '',
            risk_level: document.getElementById('risk-level').value
        });
        
        const response = await fetch(`/api/trading/signals?${params}`);
        const data = await response.json();
        
        if (data.success) {
            displayTradingSignals(data.signals);
            updatePerformanceMetrics(data.metrics);
        } else {
            throw new Error(data.error || 'Failed to load signals');
        }
    } catch (error) {
        console.error('Error loading trading signals:', error);
        document.getElementById('trading-signals').innerHTML = `
            <div class="alert alert-warning">
                <i class="fas fa-exclamation-triangle"></i>
                Failed to load trading signals: ${error.message}
            </div>
        `;
    }
}

// Display trading signals
function displayTradingSignals(signals) {
    const container = document.getElementById('trading-signals');
    
    if (!signals || signals.length === 0) {
        container.innerHTML = `
            <div class="alert alert-info">
                <i class="fas fa-info-circle"></i>
                No trading signals available. Ensure a model is selected and configured.
            </div>
        `;
        return;
    }
    
    let signalsHtml = '<div class="row">';
    
    signals.forEach((signal, index) => {
        const signalColor = signal.action === 'BUY' ? 'success' : 
                           signal.action === 'SELL' ? 'danger' : 'secondary';
        const signalIcon = signal.action === 'BUY' ? 'arrow-up' : 
                          signal.action === 'SELL' ? 'arrow-down' : 'minus';
        
        signalsHtml += `
            <div class="col-md-6 mb-3">
                <div class="card border-${signalColor}">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-center">
                            <div>
                                <h6 class="card-title text-${signalColor}">
                                    <i class="fas fa-${signalIcon}"></i> ${signal.action}
                                </h6>
                                <p class="card-text mb-1">
                                    <small class="text-muted">Price:</small> $${signal.price?.toFixed(2) || 'N/A'}<br>
                                    <small class="text-muted">Confidence:</small> ${(signal.confidence * 100)?.toFixed(1) || 'N/A'}%
                                </p>
                            </div>
                            <div class="text-end">
                                <small class="text-muted">${signal.timestamp || 'Now'}</small>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    });
    
    signalsHtml += '</div>';
    container.innerHTML = signalsHtml;
}

// Update performance metrics
function updatePerformanceMetrics(metrics) {
    if (metrics) {
        document.getElementById('signal-confidence').textContent = 
            metrics.avgConfidence ? `${(metrics.avgConfidence * 100).toFixed(1)}%` : '--';
        document.getElementById('last-update').textContent = 
            new Date().toLocaleTimeString();
    }
}

// Initialize trading chart
function initializeTradingChart() {
    const canvas = document.getElementById('trading-chart');
    const ctx = canvas.getContext('2d');
    
    tradingChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Bitcoin Price',
                    data: [],
                    borderColor: '#60a5fa',
                    backgroundColor: 'rgba(96, 165, 250, 0.1)',
                    borderWidth: 2,
                    fill: true
                },
                {
                    label: 'Buy Signals',
                    data: [],
                    backgroundColor: '#34d399',
                    borderColor: '#34d399',
                    pointRadius: 8,
                    pointStyle: 'triangle',
                    showLine: false
                },
                {
                    label: 'Sell Signals',
                    data: [],
                    backgroundColor: '#f87171',
                    borderColor: '#f87171',
                    pointRadius: 8,
                    pointStyle: 'triangle',
                    rotation: 180,
                    showLine: false
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Bitcoin Price with Trading Signals',
                    color: '#f3f4f6',
                    font: { size: 16 }
                },
                legend: {
                    labels: { color: '#d1d5db' }
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Time',
                        color: '#d1d5db'
                    },
                    ticks: { color: '#9ca3af' },
                    grid: { color: 'rgba(156, 163, 175, 0.2)' }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Price (USD)',
                        color: '#d1d5db'
                    },
                    ticks: { color: '#9ca3af' },
                    grid: { color: 'rgba(156, 163, 175, 0.2)' }
                }
            }
        }
    });
    
    // Load initial chart data
    loadChartData();
}

// Load chart data
async function loadChartData() {
    try {
        const response = await fetch('/api/trading/chart-data');
        const data = await response.json();
        
        if (data.success) {
            updateTradingChart(data.data);
        }
    } catch (error) {
        console.error('Error loading chart data:', error);
    }
}

// Update trading chart
function updateTradingChart(data) {
    if (!tradingChart || !data) return;
    
    tradingChart.data.labels = data.timestamps || [];
    tradingChart.data.datasets[0].data = data.prices || [];
    tradingChart.data.datasets[1].data = data.buySignals || [];
    tradingChart.data.datasets[2].data = data.sellSignals || [];
    
    tradingChart.update();
}

// Run backtest
async function runBacktest() {
    if (!selectedModel) {
        showError('Please select a model first');
        return;
    }
    
    try {
        const btn = document.getElementById('run-backtest-btn');
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Running...';
        
        document.getElementById('backtest-status').innerHTML = `
            <i class="fas fa-spinner fa-spin"></i>
            Running backtest with ${selectedModel.type.toUpperCase()} model...
        `;
        
        const response = await fetch('/api/trading/backtest', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                model_id: selectedModel.id,
                strategy: currentStrategy,
                risk_level: document.getElementById('risk-level').value,
                position_size: document.getElementById('position-size').value
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            displayBacktestResults(data.results);
        } else {
            throw new Error(data.error || 'Backtest failed');
        }
    } catch (error) {
        console.error('Error running backtest:', error);
        showError('Backtest failed: ' + error.message);
    } finally {
        const btn = document.getElementById('run-backtest-btn');
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-play"></i> Run Backtest';
    }
}

// Display backtest results
function displayBacktestResults(results) {
    const container = document.getElementById('backtest-results');
    
    const totalReturnColor = results.total_return > 0 ? 'text-success' : 'text-danger';
    const winRateColor = results.win_rate > 50 ? 'text-success' : 'text-warning';
    
    container.innerHTML = `
        <div class="row">
            <div class="col-md-3">
                <div class="card border-primary">
                    <div class="card-body text-center">
                        <h6 class="card-title">Total Return</h6>
                        <h4 class="${totalReturnColor}">${results.total_return?.toFixed(2) || 0}%</h4>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card border-info">
                    <div class="card-body text-center">
                        <h6 class="card-title">Win Rate</h6>
                        <h4 class="${winRateColor}">${results.win_rate?.toFixed(1) || 0}%</h4>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card border-warning">
                    <div class="card-body text-center">
                        <h6 class="card-title">Max Drawdown</h6>
                        <h4 class="text-danger">${results.max_drawdown?.toFixed(2) || 0}%</h4>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card border-success">
                    <div class="card-body text-center">
                        <h6 class="card-title">Total Trades</h6>
                        <h4 class="text-primary">${results.total_trades || 0}</h4>
                    </div>
                </div>
            </div>
        </div>
        <div class="mt-3">
            <h6>Performance Summary:</h6>
            <p class="text-muted">${results.summary || 'No summary available'}</p>
        </div>
    `;
    
    container.style.display = 'block';
    
    document.getElementById('backtest-status').innerHTML = `
        <i class="fas fa-check-circle text-success"></i>
        Backtest completed successfully!
    `;
}

// Start live updates
function startLiveUpdates() {
    // Update trading signals every 30 seconds
    setInterval(() => {
        if (selectedModel) {
            loadTradingSignals();
        }
    }, 30000);
    
    // Update chart data every 60 seconds
    setInterval(() => {
        loadChartData();
    }, 60000);
}

// Utility functions
function showSuccess(message) {
    // You can implement a toast notification system here
    console.log('Success:', message);
}

function showError(message) {
    // You can implement a toast notification system here
    console.error('Error:', message);
}
