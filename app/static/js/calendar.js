// Kalendoriaus inicializavimas ir duomenų atvaizdavimas

document.addEventListener('DOMContentLoaded', function() {
    // Gauname kalendoriaus elementą
    var calendarEl = document.getElementById('calendar');
    
    // Inicializuojame kalendorių
    var calendar = new FullCalendar.Calendar(calendarEl, {
        // Pagrindinės nuostatos
        initialView: 'dayGridMonth', // Pradinis vaizdas - mėnuo
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay'
        },
        
        // Lokalizacija (lietuvių kalba)
        locale: 'lt',
        
        // Leisti spustelėti ant užduočių
        eventClick: function(info) {
            showTaskModal(info.event);
        },
        
        // Gauti užduotis iš API
        events: {
            url: '/scheduler/api/calendar_events',
            method: 'GET',
            failure: function() {
                alert('Klaida gaunant kalendoriaus duomenis!');
            }
        },
        
        // Užduočių atvaizdavimas
        eventDidMount: function(info) {
            // Nustatome spalvą pagal užduoties būseną
            var status = info.event.extendedProps.status;
            
            if (status === 'pending') {
                info.el.classList.add('task-pending');
            } else if (status === 'running') {
                info.el.classList.add('task-running');
            } else if (status === 'completed') {
                info.el.classList.add('task-completed');
            } else if (status === 'failed') {
                info.el.classList.add('task-failed');
            }
        }
    });
    
    // Atvaizduojame kalendorių
    calendar.render();
    
    // Funkcija, kuri atidaro modalinį langą su užduoties informacija
    function showTaskModal(event) {
        // Gauname užduoties duomenis
        var taskId = event.id;
        var taskTitle = event.title;
        var taskStatus = event.extendedProps.status;
        var taskFrequency = event.extendedProps.frequency;
        var taskPriority = event.extendedProps.priority;
        var taskTime = event.start ? event.start.toLocaleString() : 'Nenustatyta';
        var taskDescription = event.extendedProps.description || 'Nėra aprašymo';
        
        // Užpildome modalinį langą duomenimis
        document.getElementById('modal-title').textContent = taskTitle;
        
        // Nustatome būsenos spalvą ir tekstą
        var statusElement = document.getElementById('modal-status');
        if (taskStatus === 'pending') {
            statusElement.innerHTML = '<span class="badge bg-secondary">Laukianti</span>';
        } else if (taskStatus === 'running') {
            statusElement.innerHTML = '<span class="badge bg-primary">Vykdoma</span>';
        } else if (taskStatus === 'completed') {
            statusElement.innerHTML = '<span class="badge bg-success">Baigta</span>';
        } else if (taskStatus === 'failed') {
            statusElement.innerHTML = '<span class="badge bg-danger">Klaida</span>';
        } else {
            statusElement.innerHTML = '<span class="badge bg-info">' + taskStatus + '</span>';
        }
        
        // Nustatome dažnumo tekstą
        var frequencyElement = document.getElementById('modal-frequency');
        if (taskFrequency === 'once') {
            frequencyElement.textContent = 'Vienkartinė';
        } else if (taskFrequency === 'daily') {
            frequencyElement.textContent = 'Kasdien';
        } else if (taskFrequency === 'weekly') {
            frequencyElement.textContent = 'Kas savaitę';
        } else if (taskFrequency === 'monthly') {
            frequencyElement.textContent = 'Kas mėnesį';
        } else {
            frequencyElement.textContent = taskFrequency;
        }
        
        // Nustatome prioriteto tekstą
        var priorityElement = document.getElementById('modal-priority');
        if (taskPriority === 1) {
            priorityElement.innerHTML = '<span class="text-danger">Aukštas</span>';
        } else if (taskPriority === 5) {
            priorityElement.innerHTML = '<span class="text-warning">Vidutinis</span>';
        } else if (taskPriority === 10) {
            priorityElement.innerHTML = '<span class="text-success">Žemas</span>';
        } else {
            priorityElement.textContent = taskPriority;
        }
        
        // Nustatome kitus laukus
        document.getElementById('modal-time').textContent = taskTime;
        document.getElementById('modal-description').textContent = taskDescription;
        
        // Nustatome nuorodas į veiksmus
        document.getElementById('modal-view-link').href = '/scheduler/view_task/' + taskId;
        document.getElementById('modal-edit-link').href = '/scheduler/edit_task/' + taskId;
        document.getElementById('modal-run-link').href = '/scheduler/run_task/' + taskId;
        
        // Jei užduotis jau vykdoma, išjungiame "Vykdyti" mygtuką
        if (taskStatus === 'running') {
            document.getElementById('modal-run-link').classList.add('disabled');
        } else {
            document.getElementById('modal-run-link').classList.remove('disabled');
        }
        
        // Atidarome modalinį langą
        var taskModal = new bootstrap.Modal(document.getElementById('taskModal'));
        taskModal.show();
    }
});