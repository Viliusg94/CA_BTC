/**
 * Bitcoin Price Prediction Charts
 * This file contains functions for creating and updating prediction charts
 */

// Global charts
let predictionChart = null;

// Initialize charts when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing prediction charts...');
    
    // Create chart for predictions
    initializePredictionChart();
    
    // Load initial data with a small delay
    setTimeout(() => {
        updatePredictionData();
    }, 500);
});

// Initialize prediction chart
function initializePredictionChart() {
    const canvas = document.getElementById('prediction-chart');
    if (!canvas) {
        console.warn('Prediction chart canvas not found');
        return;
    }
    
    const ctx = canvas.getContext('2d');
    console.log('Initializing prediction chart...');
    
    predictionChart = new Chart(ctx, {
        type: 'line',
        data: {
            datasets: [{
                label: 'Historical Price',
                data: [],
                borderColor: '#60a5fa',
                backgroundColor: 'rgba(96, 165, 250, 0.1)',
                borderWidth: 2,
                tension: 0.4,
                pointRadius: 3,
                pointHoverRadius: 6
            }, {
                label: 'Predicted Price',
                data: [],
                borderColor: '#34d399',
                backgroundColor: 'rgba(52, 211, 153, 0.1)',
                borderWidth: 2,
                tension: 0.3,
                pointRadius: 4,
                pointHoverRadius: 7,
                borderDash: [5, 5]
            }, {
                label: 'Upper Bound',
                data: [],
                borderColor: 'rgba(251, 191, 36, 0.5)',
                backgroundColor: 'transparent',
                borderWidth: 1,
                tension: 0.3,
                pointRadius: 0,
                borderDash: [3, 3]
            }, {
                label: 'Lower Bound',
                data: [],
                borderColor: 'rgba(251, 191, 36, 0.5)',
                backgroundColor: 'rgba(251, 191, 36, 0.1)',
                borderWidth: 1,
                tension: 0.3,
                pointRadius: 0,
                fill: '-1',
                borderDash: [3, 3]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: 'index'
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Bitcoin Price Prediction',
                    font: { size: 18, weight: 'bold' },
                    color: '#f3f4f6'
                },
                legend: {
                    labels: {
                        color: '#d1d5db',
                        usePointStyle: true,
                        font: {
                            size: 12
                        }
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(17, 24, 39, 0.95)',
                    titleColor: '#f3f4f6',
                    bodyColor: '#d1d5db',
                    borderColor: '#60a5fa',
                    borderWidth: 1,
                    padding: 12,
                    displayColors: true,
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.parsed.y !== null) {
                                label += new Intl.NumberFormat('en-US', {
                                    style: 'currency',
                                    currency: 'USD'
                                }).format(context.parsed.y);
                            }
                            return label;
                        }
                    }
                }
            },
            scales: {
                x: {
                    type: 'time',
                    time: {
                        unit: 'day',
                        displayFormats: {
                            day: 'MMM dd'
                        }
                    },
                    title: {
                        display: true,
                        text: '📅 Date',
                        color: '#d1d5db',
                        font: { weight: 'bold' }
                    },
                    grid: { color: 'rgba(156, 163, 175, 0.2)' },
                    ticks: { color: '#9ca3af' }
                },
                y: {
                    title: {
                        display: true,
                        text: '💰 Price (USD)',
                        color: '#d1d5db',
                        font: { weight: 'bold' }
                    },
                    grid: { color: 'rgba(156, 163, 175, 0.2)' },
                    ticks: {
                        color: '#9ca3af',
                        callback: function(value) {
                            return '$' + value.toLocaleString();
                        }
                    }
                }
            },
            animation: {
                duration: 1500,
                easing: 'easeInOutQuart'
            }
        }
    });
}

// Update prediction data and chart
async function updatePredictionData() {
    try {
        console.log('Updating prediction data...');
        
        // Load recent price history for historical part of the chart
        const historyResponse = await fetch('/api/price_history?days=30');
        const historyData = await historyResponse.json();
        
        if (!historyData || historyData.status !== 'success') {
            throw new Error('Failed to load price history');
        }
        
        // Store historical data
        window.priceHistory = historyData.data;
        
        // If we have a predictionChart, update it with historical data only
        if (predictionChart) {
            updateHistoricalDataInChart(predictionChart, historyData.data);
        }
        
    } catch (error) {
        console.error('Error updating prediction data:', error);
    }
}

// Update historical data in chart
function updateHistoricalDataInChart(chart, data) {
    if (!chart || !data) return;
    
    // Format historical data for chart
    const historicalData = [];
    
    // Use the last 30 days of historical data
    const maxPoints = Math.min(30, data.dates.length);
    for (let i = data.dates.length - maxPoints; i < data.dates.length; i++) {
        historicalData.push({
            x: new Date(data.dates[i]),
            y: data.prices[i] || data.close[i]
        });
    }
    
    // Update chart with historical data
    chart.data.datasets[0].data = historicalData;
    chart.update();
}

// Update prediction chart with new prediction data
function updatePredictionChart(predictionData) {
    if (!predictionChart || !predictionData) {
        console.error('Chart or prediction data is missing');
        return;
    }
    
    console.log('Updating prediction chart with:', predictionData);
    
    // Clear previous prediction data
    predictionChart.data.datasets[1].data = [];
    predictionChart.data.datasets[2].data = [];
    predictionChart.data.datasets[3].data = [];
    
    // Get current price to add as starting point
    const currentPrice = predictionData.current_price;
    const today = new Date();
    
    // Add current price as first point in prediction
    const predictionPoints = [{
        x: today,
        y: currentPrice
    }];
    
    // Add prediction points
    for (let i = 0; i < predictionData.dates.length; i++) {
        predictionPoints.push({
            x: new Date(predictionData.dates[i]),
            y: predictionData.values[i]
        });
    }
    
    // Update prediction line
    predictionChart.data.datasets[1].data = predictionPoints;
    
    // Update confidence intervals if available
    if (predictionData.lower_bounds && predictionData.upper_bounds) {
        const lowerBounds = [{
            x: today,
            y: currentPrice
        }];
        
        const upperBounds = [{
            x: today,
            y: currentPrice
        }];
        
        for (let i = 0; i < predictionData.dates.length; i++) {
            lowerBounds.push({
                x: new Date(predictionData.dates[i]),
                y: predictionData.lower_bounds[i]
            });
            
            upperBounds.push({
                x: new Date(predictionData.dates[i]),
                y: predictionData.upper_bounds[i]
            });
        }
        
        predictionChart.data.datasets[2].data = upperBounds;
        predictionChart.data.datasets[3].data = lowerBounds;
    }
    
    // Update chart
    predictionChart.update();
    
    // Show the chart if it was previously hidden
    const loadingEl = document.getElementById('prediction-loading');
    if (loadingEl) loadingEl.style.display = 'none';
    
    const messageEl = document.getElementById('no-prediction-message');
    if (messageEl) messageEl.style.display = 'none';
}

// Export the updatePredictionChart function to make it available globally
window.updatePredictionChart = updatePredictionChart;
