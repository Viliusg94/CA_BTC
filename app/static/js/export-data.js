// Grafikų duomenų eksportavimo funkcijos

// Eksportuoja grafiko duomenis CSV formatu
function exportChartDataToCsv(chartData, fileName) {
    // Tikriname ar yra duomenų
    if (!chartData || !chartData.labels || !chartData.close) {
        alert('Nėra duomenų eksportavimui!');
        return;
    }
    
    // Sukuriame CSV turinį
    let csvContent = 'data:text/csv;charset=utf-8,';
    
    // Pridedame antraštes
    csvContent += 'Data,Atidarymo,Aukščiausia,Žemiausia,Uždarymo,Apyvarta\n';
    
    // Pridedame duomenis
    for (let i = 0; i < chartData.labels.length; i++) {
        const row = [
            chartData.labels[i],
            chartData.open[i],
            chartData.high[i],
            chartData.low[i],
            chartData.close[i],
            chartData.volumes[i]
        ];
        
        csvContent += row.join(',') + '\n';
    }
    
    // Užkoduojame uri komponentes
    const encodedUri = encodeURI(csvContent);
    
    // Sukuriame nuorodą atsisiuntimui
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', fileName || 'chart-data.csv');
    
    // Pridedame į dokumentą
    document.body.appendChild(link);
    
    // Spaudžiame nuorodą atsisiuntimui
    link.click();
    
    // Šaliname nuorodą
    document.body.removeChild(link);
}

// Eksportuoja grafiko duomenis JSON formatu
function exportChartDataToJson(chartData, fileName) {
    // Tikriname ar yra duomenų
    if (!chartData) {
        alert('Nėra duomenų eksportavimui!');
        return;
    }
    
    // Sukuriame duomenų kopiją
    const exportData = {
        ...chartData,
        exportTime: new Date().toISOString(),
        symbol: document.getElementById('symbolSelector').value,
        interval: document.getElementById('intervalSelector').value
    };
    
    // Konvertuojame į JSON
    const jsonContent = JSON.stringify(exportData, null, 2);
    
    // Sukuriame Blob objektą
    const blob = new Blob([jsonContent], { type: 'application/json' });
    
    // Sukuriame nuorodą atsisiuntimui
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = fileName || 'chart-data.json';
    
    // Pridedame į dokumentą
    document.body.appendChild(link);
    
    // Spaudžiame nuorodą atsisiuntimui
    link.click();
    
    // Šaliname nuorodą
    document.body.removeChild(link);
    URL.revokeObjectURL(link.href);
}