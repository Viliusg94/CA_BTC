document.addEventListener('DOMContentLoaded', function() {
    // Inicializuojame grafikus
    initCharts();
    
    // Nustatome periodišką atnaujinimą
    setInterval(updateDashboard, 5000);
});

// Grafikų objektai
let statusChart = null;
let frequencyChart = null;

// Funkcija, kuri inicializuoja grafikus
function initCharts() {
    // Gauname statistikos duomenis
    fetch('/scheduler/api/task_stats')
        .then(response => response.json())
        .then(data => {
            // Inicializuojame būsenų grafiką
            const statusCtx = document.getElementById('status-chart').getContext('2d');
            statusChart = new Chart(statusCtx, {
                type: 'doughnut',
                data: {
                    labels: ['Laukiančios', 'Vykdomos', 'Baigtos', 'Klaidos'],
                    datasets: [{
                        data: [
                            data.status.pending,
                            data.status.running,
                            data.status.completed,
                            data.status.failed
                        ],
                        backgroundColor: [
                            '#ffc107', // geltona - laukiančios
                            '#0d6efd', // mėlyna - vykdomos
                            '#198754', // žalia - baigtos
                            '#dc3545'  // raudona - klaidos
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'right',
                        },
                        title: {
                            display: true,
                            text: 'Užduočių būsenos'
                        }
                    }
                }
            });
            
            // Inicializuojame dažnumo grafiką
            const frequencyCtx = document.getElementById('frequency-chart').getContext('2d');
            frequencyChart = new Chart(frequencyCtx, {
                type: 'bar',
                data: {
                    labels: ['Vienkartinės', 'Kasdienės', 'Savaitinės', 'Mėnesinės'],
                    datasets: [{
                        label: 'Užduočių skaičius',
                        data: [
                            data.frequency.once,
                            data.frequency.daily,
                            data.frequency.weekly,
                            data.frequency.monthly
                        ],
                        backgroundColor: [
                            '#6c757d', // pilka - vienkartinės
                            '#17a2b8', // šviesiai mėlyna - kasdienės
                            '#6f42c1', // violetinė - savaitinės
                            '#fd7e14'  // oranžinė - mėnesinės
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            display: false
                        },
                        title: {
                            display: true,
                            text: 'Užduočių dažnumas'
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                precision: 0
                            }
                        }
                    }
                }
            });
        })
        .catch(error => {
            console.error('Klaida gaunant statistikos duomenis:', error);
        });
}

// Funkcija, kuri atnaujina grafikų duomenis
function updateCharts() {
    fetch('/scheduler/api/task_stats')
        .then(response => response.json())
        .then(data => {
            if (statusChart) {
                statusChart.data.datasets[0].data = [
                    data.status.pending,
                    data.status.running,
                    data.status.completed,
                    data.status.failed
                ];
                statusChart.update();
            }
            
            if (frequencyChart) {
                frequencyChart.data.datasets[0].data = [
                    data.frequency.once,
                    data.frequency.daily,
                    data.frequency.weekly,
                    data.frequency.monthly
                ];
                frequencyChart.update();
            }
            
            // Atnaujiname statistikos korteles
            document.getElementById('total-tasks').textContent = data.total;
            document.getElementById('pending-tasks').textContent = data.status.pending;
            document.getElementById('running-tasks').textContent = data.status.running;
            document.getElementById('completed-tasks').textContent = data.status.completed;
        })
        .catch(error => {
            console.error('Klaida atnaujinant grafikus:', error);
        });
}

// Funkcija, kuri atnaujina vykdomų užduočių progresą
function updateRunningTasks() {
    fetch('/scheduler/api/running_tasks')
        .then(response => response.json())
        .then(tasks => {
            // Gauname visas progreso juostas
            const progressBars = document.querySelectorAll('.progress-bar[data-task-id]');
            
            // Sukuriame žemėlapį, kad greitai rastume progreso juostas pagal ID
            const progressBarMap = {};
            progressBars.forEach(bar => {
                const taskId = bar.getAttribute('data-task-id');
                progressBarMap[taskId] = bar;
            });
            
            // Atnaujiname progreso juostas
            tasks.forEach(task => {
                const bar = progressBarMap[task.id];
                if (bar) {
                    bar.style.width = task.progress + '%';
                    bar.setAttribute('aria-valuenow', task.progress);
                    bar.textContent = task.progress + '%';
                }
            });
        })
        .catch(error => {
            console.error('Klaida atnaujinant vykdomas užduotis:', error);
        });
}

// Funkcija, kuri atnaujina visą skydelį
function updateDashboard() {
    updateCharts();
    updateRunningTasks();
}