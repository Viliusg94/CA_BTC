/**
 * Supaprastinta, garantuotai veikianti Bitcoin grafikų versija
 */

// Global chart variables
let candlestickChart = null;
let predictionsChart = null;

// Initialize charts when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing charts...');
    
    // Small delay to ensure all dependencies are loaded
    setTimeout(() => {
        initializeCandlestickChart();
        initializePredictionsChart();
        
        // Auto-refresh candlestick data every 30 seconds
        setInterval(updateCandlestickData, 30000);
    }, 500);
});

// Function to initialize the candlestick chart with fallback
function initializeCandlestickChart() {
    const canvas = document.getElementById('candlestick-chart');
    if (!canvas) {
        console.warn('Canvas element not found');
        return;
    }
    
    const ctx = canvas.getContext('2d');
    console.log('Initializing candlestick chart...');
    
    // Use fallback implementation as the financial plugin may not work properly
    initializeFallbackCandlestickChart(ctx);
}

// Fallback implementation using custom drawing
function initializeFallbackCandlestickChart(ctx) {
    console.log('Using fallback candlestick implementation');
    
    candlestickChart = new Chart(ctx, {
        type: 'scatter',
        data: {
            datasets: [{
                label: 'Bitcoin Price',
                data: [],
                pointRadius: 0,
                showLine: false,
                backgroundColor: 'transparent'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: 'index'
            },
            onHover: function(event, elements, chart) {
                const canvas = chart.canvas;
                canvas.style.cursor = elements.length > 0 ? 'crosshair' : 'default';
                
                if (elements.length > 0) {
                    const element = elements[0];
                    const dataIndex = element.index;
                    
                    createEnhancedCrosshair(chart.canvas, event);
                    updateChartInfoPanel(dataIndex);
                } else {
                    removeCrosshair();
                    resetChartInfoPanel();
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Bitcoin Live Candlestick Chart',
                    font: { size: 20, weight: 'bold' },
                    color: '#f3f4f6'
                },
                legend: { 
                    display: false 
                },
                tooltip: { 
                    enabled: false // Disable default tooltip as we use custom
                }
            },
            scales: {
                x: {
                    type: 'linear',
                    title: { 
                        display: true, 
                        text: '📅 Date', 
                        color: '#d1d5db',
                        font: { weight: 'bold' } 
                    },
                    grid: { color: 'rgba(156, 163, 175, 0.2)' },
                    ticks: { 
                        color: '#9ca3af',
                        callback: function(value, index) {
                            if (window.candlestickData && window.candlestickData[Math.floor(value)]) {
                                const item = window.candlestickData[Math.floor(value)];
                                return new Date(item.x).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
                            }
                            return '';
                        }
                    }
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
                duration: 1000,
                easing: 'easeInOutQuart'
            }
        },
        plugins: [{
            id: 'candlestick-draw',
            afterDatasetsDraw: function(chart) {
                drawCandlesticks(chart);
            }
        }]
    });
    
    updateCandlestickData();
}

// Custom candlestick drawing function
function drawCandlesticks(chart) {
    const ctx = chart.ctx;
    const chartArea = chart.chartArea;
    
    if (!window.candlestickData || window.candlestickData.length === 0) {
        console.log('No candlestick data to draw');
        return;
    }
    
    const candleWidth = Math.max(4, (chartArea.right - chartArea.left) / window.candlestickData.length * 0.6);
    
    window.candlestickData.forEach((candle, index) => {
        const x = chart.scales.x.getPixelForValue(index);
        const yHigh = chart.scales.y.getPixelForValue(candle.h);
        const yLow = chart.scales.y.getPixelForValue(candle.l);
        const yOpen = chart.scales.y.getPixelForValue(candle.o);
        const yClose = chart.scales.y.getPixelForValue(candle.c);
        
        const isBullish = candle.c >= candle.o;
        const color = isBullish ? '#34d399' : '#f87171';
        const fillColor = isBullish ? 'rgba(52, 211, 153, 0.8)' : 'rgba(248, 113, 113, 0.8)';
        
        // Draw wick (high-low line)
        ctx.strokeStyle = color;
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(x, yHigh);
        ctx.lineTo(x, yLow);
        ctx.stroke();
        
        // Draw body (open-close rectangle)
        const bodyTop = Math.min(yOpen, yClose);
        const bodyHeight = Math.abs(yClose - yOpen) || 1;
        
        ctx.fillStyle = fillColor;
        ctx.fillRect(x - candleWidth/2, bodyTop, candleWidth, bodyHeight);
        
        ctx.strokeStyle = color;
        ctx.lineWidth = 1;
        ctx.strokeRect(x - candleWidth/2, bodyTop, candleWidth, bodyHeight);
    });
}

// Enhanced crosshair with better styling
function createEnhancedCrosshair(canvas, event) {
    removeCrosshair();
    
    // Get mouse position relative to the canvas
    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    
    // Create crosshair container element
    const crosshair = document.createElement('div');
    crosshair.id = 'chart-crosshair';
    crosshair.className = 'chart-crosshair';
    crosshair.style.position = 'absolute';
    crosshair.style.pointerEvents = 'none';
    crosshair.style.zIndex = '999';
    crosshair.style.top = '0';
    crosshair.style.left = '0';
    crosshair.style.width = canvas.width + 'px';
    crosshair.style.height = canvas.height + 'px';
    
    // Add horizontal and vertical lines
    crosshair.innerHTML = `
        <div class="crosshair-line" style="position: absolute; left: ${x}px; top: 0; width: 2px; height: ${canvas.height}px; background: rgba(96, 165, 250, 0.7); box-shadow: 0 0 4px rgba(96, 165, 250, 0.8);"></div>
        <div class="crosshair-line" style="position: absolute; left: 0; top: ${y}px; width: ${canvas.width}px; height: 2px; background: rgba(96, 165, 250, 0.7); box-shadow: 0 0 4px rgba(96, 165, 250, 0.8);"></div>
        <div style="position: absolute; left: ${x - 4}px; top: ${y - 4}px; width: 8px; height: 8px; background: #60a5fa; border-radius: 50%; border: 2px solid white; box-shadow: 0 0 8px rgba(96, 165, 250, 0.8);"></div>
    `;
    
    // Ensure container is positioned relative for absolute positioning of crosshair
    const chartContainer = canvas.closest('.chart-container');
    if (chartContainer) {
        chartContainer.style.position = 'relative';
        chartContainer.appendChild(crosshair);
    } else {
        // Fallback to canvas parent
        canvas.parentElement.style.position = 'relative';
        canvas.parentElement.appendChild(crosshair);
    }
}

// Update the chart information panel with candlestick data
function updateChartInfoPanel(dataIndex) {
    if (!window.candlestickData || !window.candlestickData[dataIndex]) {
        console.log('No data for index:', dataIndex);
        return;
    }
    
    const data = window.candlestickData[dataIndex];
    const change = data.c - data.o;
    const changePercent = data.o > 0 ? ((change / data.o) * 100) : 0;
    
    // Calculate technical indicators
    const bodySize = Math.abs(data.c - data.o);
    const shadowSize = data.h - data.l;
    const upperShadow = data.h - Math.max(data.o, data.c);
    const lowerShadow = Math.min(data.o, data.c) - data.l;
    
    const panel = document.getElementById('chart-info-panel');
    if (!panel) return;
    
    panel.className = 'chart-info-panel active';
    
    panel.innerHTML = `
        <div style="text-align: center; margin-bottom: 12px;">
            <h6 style="color: ${change >= 0 ? '#34d399' : '#f87171'}; margin: 0; font-size: 16px; font-weight: bold;">
                ${change >= 0 ? '🚀 KYLANTIS TRENDAS' : '📉 KRINTANTIS TRENDAS'}
            </h6>
            <p style="margin: 5px 0 0 0; font-size: 13px; color: #9ca3af;">
                ${new Date(data.x).toLocaleDateString('lt-LT', { 
                    weekday: 'long',
                    month: 'long', 
                    day: 'numeric',
                    year: 'numeric'
                })}
            </p>
        </div>
        
        <div class="chart-info-content">
            <div class="info-group">
                <div class="info-label">Atidarymas</div>
                <div class="info-value" style="color: #60a5fa;">$${data.o.toLocaleString('en-US', {minimumFractionDigits: 2})}</div>
            </div>
            
            <div class="info-group">
                <div class="info-label">Aukščiausias</div>
                <div class="info-value" style="color: #34d399;">$${data.h.toLocaleString('en-US', {minimumFractionDigits: 2})}</div>
            </div>
            
            <div class="info-group">
                <div class="info-label">Žemiausias</div>
                <div class="info-value" style="color: #f87171;">$${data.l.toLocaleString('en-US', {minimumFractionDigits: 2})}</div>
            </div>
            
            <div class="info-group">
                <div class="info-label">Uždarymas</div>
                <div class="info-value" style="color: #fbbf24;">$${data.c.toLocaleString('en-US', {minimumFractionDigits: 2})}</div>
                <div class="info-change" style="color: ${change >= 0 ? '#34d399' : '#f87171'};">
                    ${change >= 0 ? '+' : ''}$${change.toFixed(2)} (${changePercent >= 0 ? '+' : ''}${changePercent.toFixed(2)}%)
                </div>
            </div>
        </div>
        
        <div style="margin-top: 12px; padding-top: 12px; border-top: 1px solid #4b5563;">
            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; text-align: center;">
                <div>
                    <div class="info-label">Amplitudė</div>
                    <div style="color: #d1d5db; font-weight: bold; font-size: 13px;">$${(data.h - data.l).toFixed(2)}</div>
                </div>
                
                <div>
                    <div class="info-label">Kūnas</div>
                    <div style="color: #d1d5db; font-weight: bold; font-size: 13px;">$${bodySize.toFixed(2)}</div>
                </div>
                
                <div>
                    <div class="info-label">Šešėliai</div>
                    <div style="color: #d1d5db; font-weight: bold; font-size: 13px;">$${(upperShadow + lowerShadow).toFixed(2)}</div>
                </div>
                
                <div>
                    <div class="info-label">Signalas</div>
                    <div style="color: ${bodySize > shadowSize * 0.7 ? '#34d399' : '#f87171'}; font-weight: bold; font-size: 13px;">
                        ${bodySize > shadowSize * 0.7 ? '💪 Stiprus' : '⚖️ Silpnas'}
                    </div>
                </div>
            </div>
        </div>
    `;
}

// Reset chart information panel to default state
function resetChartInfoPanel() {
    const panel = document.getElementById('chart-info-panel');
    if (!panel) return;
    
    panel.className = 'chart-info-panel';
    panel.innerHTML = `
        <div class="text-center">
            <i class="fas fa-chart-line" style="font-size: 24px; color: var(--text-muted); margin-bottom: 8px;"></i>
            <h6 style="margin: 8px 0 4px 0; color: var(--text-secondary); font-size: 14px;">Realaus laiko Bitcoin analizė</h6>
            <p style="margin: 0; color: var(--text-muted); font-size: 12px;">Pasirinkite bet kurią žvakę grafike detalesnei informacijai</p>
        </div>
    `;
}

// Remove the old hover info functions since we're using the panel now
function updateDetailedHoverInfo(dataIndex, event, chart) {
    // This function is no longer needed as we use the panel
    // But keep it for compatibility
}

function removeHoverInfo() {
    // This function is no longer needed as we use the panel
    // But keep it for compatibility
}

// Function to fetch and update candlestick data from Binance
async function updateCandlestickData() {
    try {
        console.log('Fetching candlestick data from Binance...');
        
        const endTime = Date.now();
        const startTime = endTime - (30 * 24 * 60 * 60 * 1000);
        
        const url = `https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1d&startTime=${startTime}&endTime=${endTime}&limit=30`;
        
        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error(`Binance API error: ${response.status}`);
        }
        
        const klineData = await response.json();
        
        if (!klineData || klineData.length === 0) {
            throw new Error('No data received from Binance');
        }
        
        const processedData = processKlineDataForCandlesticks(klineData);
        
        if (candlestickChart) {
            updateCandlestickChartData(candlestickChart, processedData);
        }
        
        const errorDiv = document.getElementById('candlestickError');
        if (errorDiv) {
            errorDiv.style.display = 'none';
        }
        
        console.log('Candlestick chart updated successfully with', processedData.length, 'data points');
        
    } catch (error) {
        console.error('Error fetching candlestick data:', error);
        
        const errorDiv = document.getElementById('candlestickError');
        if (errorDiv) {
            errorDiv.textContent = `Error loading chart data: ${error.message}`;
            errorDiv.style.display = 'block';
        }
        
        // Try to use fallback data from the API
        try {
            const response = await fetch('/api/price_history?days=30');
            const data = await response.json();
            
            if (data && data.status === 'success' && data.data) {
                const fallbackData = processFallbackDataForCandlesticks(data.data);
                if (candlestickChart) {
                    updateCandlestickChartData(candlestickChart, fallbackData);
                }
                console.log('Using fallback data from server API');
            }
        } catch (fallbackError) {
            console.error('Fallback data also failed:', fallbackError);
        }
    }
}

// Process Binance data for candlestick format
function processKlineDataForCandlesticks(klineData) {
    console.log('Processing', klineData.length, 'kline data points');
    
    return klineData.map((kline, index) => ({
        x: new Date(kline[0]),
        o: parseFloat(kline[1]), // open
        h: parseFloat(kline[2]), // high
        l: parseFloat(kline[3]), // low
        c: parseFloat(kline[4])  // close
    }));
}

// Process fallback data for candlestick format
function processFallbackDataForCandlesticks(data) {
    const result = [];
    
    for (let i = 0; i < data.dates.length; i++) {
        result.push({
            x: new Date(data.dates[i]),
            o: data.open ? data.open[i] : data.prices[i],
            h: data.high ? data.high[i] : data.prices[i],
            l: data.low ? data.low[i] : data.prices[i],
            c: data.close ? data.close[i] : data.prices[i]
        });
    }
    
    return result;
}

// Update chart with candlestick data
function updateCandlestickChartData(chart, data) {
    if (!chart || !data) {
        console.warn('Chart or data is missing');
        return;
    }
    
    console.log('Updating chart with', data.length, 'data points');
    
    // Store data globally for drawing
    window.candlestickData = data;
    
    // Update scatter chart data for interaction
    chart.data.datasets[0].data = data.map((item, index) => ({
        x: index,
        y: item.c
    }));
    
    chart.update('none');
}

// Enhanced remove functions
function removeCrosshair() {
    const crosshair = document.getElementById('chart-crosshair');
    if (crosshair) crosshair.remove();
}

function removeHoverInfo() {
    const hoverInfo = document.getElementById('detailed-hover-info');
    if (hoverInfo) hoverInfo.remove();
}

// Initialize predictions chart (enhanced implementation)
function initializePredictionsChart() {
    const canvas = document.getElementById('prediction-chart');
    if (!canvas) {
        console.log('Prediction chart canvas not found - probably not on predict page');
        return;
    }
    
    const ctx = canvas.getContext('2d');
    console.log('Initializing predictions chart...');
    
    predictionsChart = new Chart(ctx, {
        type: 'line',
        data: {
            datasets: [{
                label: 'Istorinės Kainos',
                data: [],
                borderColor: '#60a5fa',
                backgroundColor: 'rgba(96, 165, 250, 0.1)',
                tension: 0.4,
                pointRadius: 1,
                pointHoverRadius: 4
            }, {
                label: 'AI Prognozės',
                data: [],
                borderColor: '#34d399',
                backgroundColor: 'rgba(52, 211, 153, 0.1)',
                tension: 0.4,
                pointRadius: 2,
                pointHoverRadius: 5,
                borderDash: [10, 5]
            }, {
                label: 'Patikimumo Intervalas',
                data: [],
                borderColor: 'rgba(251, 191, 36, 0.3)',
                backgroundColor: 'rgba(251, 191, 36, 0.1)',
                fill: '+1',
                pointRadius: 0
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
                    text: 'Bitcoin Kainų Prognozės su AI',
                    font: { size: 18, weight: 'bold' },
                    color: '#f3f4f6'
                },
                legend: {
                    labels: {
                        color: '#d1d5db',
                        usePointStyle: true
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(17, 24, 39, 0.95)',
                    titleColor: '#f3f4f6',
                    bodyColor: '#d1d5db',
                    borderColor: '#60a5fa',
                    borderWidth: 1,
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': $' + context.parsed.y.toLocaleString('en-US', {
                                minimumFractionDigits: 2,
                                maximumFractionDigits: 2
                            });
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
                        text: '📅 Data',
                        color: '#d1d5db',
                        font: { weight: 'bold' }
                    },
                    grid: { color: 'rgba(156, 163, 175, 0.2)' },
                    ticks: { color: '#9ca3af' }
                },
                y: {
                    title: {
                        display: true,
                        text: '💰 Kaina (USD)',
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

// Global function to update charts
function updateCharts() {
    if (window.priceHistory && candlestickChart) {
        const data = processFallbackDataForCandlesticks(window.priceHistory);
        updateCandlestickChartData(candlestickChart, data);
    }
}

// Export functions
window.updateCharts = updateCharts;
window.updateCandlestickData = updateCandlestickData;