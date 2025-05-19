// Paprastas JavaScript, kad atnaujintų užduočių būsenas

// Funkcija, kuri atnaujina užduočių būsenas
function updateTaskStatus() {
    // Gauname visas užduočių eilutes
    var taskRows = document.querySelectorAll('tr[data-task-id]');
    
    taskRows.forEach(function(row) {
        var taskId = row.getAttribute('data-task-id');
        
        // Išsiunčiame užklausą apie užduoties būseną
        fetch('/scheduler/api/task_status/' + taskId)
            .then(function(response) {
                return response.json();
            })
            .then(function(data) {
                // Atnaujiname būsenos lauką
                var statusCell = row.querySelector('td:nth-child(2)');
                if (statusCell) {
                    var badgeClass = 'bg-secondary';
                    var statusText = 'Nežinoma';
                    
                    if (data.status === 'pending') {
                        badgeClass = 'bg-secondary';
                        statusText = 'Laukianti';
                    } else if (data.status === 'running') {
                        badgeClass = 'bg-primary';
                        statusText = 'Vykdoma';
                    } else if (data.status === 'completed') {
                        badgeClass = 'bg-success';
                        statusText = 'Baigta';
                    } else if (data.status === 'failed') {
                        badgeClass = 'bg-danger';
                        statusText = 'Klaida';
                    }
                    
                    statusCell.innerHTML = '<span class="badge ' + badgeClass + '">' + statusText + '</span>';
                }
                
                // Jei užduotis vykdoma, rodome progreso juostą
                if (data.status === 'running' && data.progress !== undefined) {
                    // Tikriname, ar jau yra progreso eilutė
                    var progressRow = row.nextElementSibling;
                    if (!progressRow || !progressRow.classList.contains('progress-row')) {
                        // Sukuriame progreso eilutę
                        progressRow = document.createElement('tr');
                        progressRow.classList.add('progress-row');
                        progressRow.innerHTML = `
                            <td colspan="7">
                                <div class="progress">
                                    <div class="progress-bar progress-bar-striped progress-bar-animated" role="progressbar" 
                                        style="width: ${data.progress}%;" 
                                        aria-valuenow="${data.progress}" 
                                        aria-valuemin="0" 
                                        aria-valuemax="100">
                                        ${data.progress}%
                                    </div>
                                </div>
                            </td>
                        `;
                        
                        // Įterpiame po užduoties eilute
                        row.parentNode.insertBefore(progressRow, row.nextSibling);
                    } else {
                        // Atnaujiname esamą progreso juostą
                        var progressBar = progressRow.querySelector('.progress-bar');
                        if (progressBar) {
                            progressBar.style.width = data.progress + '%';
                            progressBar.setAttribute('aria-valuenow', data.progress);
                            progressBar.textContent = data.progress + '%';
                        }
                    }
                } else {
                    // Pašaliname progreso eilutę, jei užduotis nebevykdoma
                    var progressRow = row.nextElementSibling;
                    if (progressRow && progressRow.classList.contains('progress-row')) {
                        progressRow.parentNode.removeChild(progressRow);
                    }
                }
            })
            .catch(function(error) {
                console.error('Klaida gaunant užduoties būseną:', error);
            });
    });
}

// Atnaujinti užduočių būsenas kas 5 sekundes
setInterval(updateTaskStatus, 5000);

// Pradinis atnaujinimas
document.addEventListener('DOMContentLoaded', function() {
    updateTaskStatus();
});