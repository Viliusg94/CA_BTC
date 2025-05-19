/**
 * Pranešimų sistema BTC prekybos platformai
 * Ši sistema priima pranešimus per WebSocket ir juos atvaizduoja
 */

// Globalus notifikacijų objektas
const BTCNotifications = {
    // Notifikacijų sąrašas puslapyje
    notifications: [],
    
    // Maksimalus rodomas pranešimų skaičius
    maxNotifications: 5,
    
    // Pranešimo gyvavimo trukmė (ms)
    duration: 5000,
    
    // Pranešimų konteineris
    container: null,
    
    // WebSocket ryšys
    socket: null,
    
    // Inicializuoja pranešimų sistemą
    init: function() {
        console.log("Inicializuojama pranešimų sistema...");
        
        // Sukuriame pranešimų konteinerį, jei jo nėra
        if (!this.container) {
            this.createNotificationContainer();
        }
        
        // Prisijungiame prie WebSocket serverio
        this.connectWebSocket();
        
        console.log("Pranešimų sistema inicializuota.");
    },
    
    // Sukuria pranešimų konteinerį
    createNotificationContainer: function() {
        // Sukuriam konteinerį
        this.container = document.createElement('div');
        this.container.className = 'notification-container';
        this.container.style.position = 'fixed';
        this.container.style.top = '20px';
        this.container.style.right = '20px';
        this.container.style.zIndex = '9999';
        this.container.style.maxWidth = '350px';
        
        // Įdedame į body
        document.body.appendChild(this.container);
    },
    
    // Prisijungia prie WebSocket serverio
    connectWebSocket: function() {
        // Jei jau prisijungta, pirmiau atsijungiame
        if (this.socket) {
            this.socket.close();
        }
        
        // Sukuriame WebSocket ryšį
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        console.log("Jungiamasi prie WebSocket:", wsUrl);
        
        try {
            this.socket = new WebSocket(wsUrl);
            
            // Nustatome įvykių klausytojus
            this.socket.onopen = () => {
                console.log("WebSocket ryšys užmegztas");
                this.showNotification("Sistema", "Pranešimų sistema prijungta", "info");
            };
            
            this.socket.onmessage = (event) => {
                this.handleWebSocketMessage(event);
            };
            
            this.socket.onclose = () => {
                console.log("WebSocket ryšys nutrauktas");
                // Pabandome iš naujo prisijungti po 5 sekundžių
                setTimeout(() => this.connectWebSocket(), 5000);
            };
            
            this.socket.onerror = (error) => {
                console.error("WebSocket klaida:", error);
            };
        } catch (error) {
            console.error("Klaida jungiantis prie WebSocket:", error);
        }
    },
    
    // Apdoroja gautą WebSocket pranešimą
    handleWebSocketMessage: function(event) {
        try {
            const message = JSON.parse(event.data);
            
            // Tikriname pranešimo tipą
            if (message.type === 'task_update') {
                this.handleTaskUpdate(message);
            } else if (message.type === 'notification') {
                // Tiesioginiai pranešimai
                this.showNotification(
                    message.title || 'Pranešimas',
                    message.message,
                    message.status || 'info'
                );
            }
        } catch (error) {
            console.error("Klaida apdorojant pranešimą:", error);
        }
    },
    
    // Apdoroja užduoties atnaujinimo pranešimą
    handleTaskUpdate: function(message) {
        const taskId = message.task_id;
        const status = message.status;
        const progress = message.progress;
        
        // Atvaizduojame pranešimą pagal būseną
        if (status === 'running' && progress === 0) {
            // Užduotis pradėta vykdyti
            this.showNotification(
                "Užduotis pradėta", 
                `Užduotis #${taskId} pradėta vykdyti`, 
                "primary"
            );
        } else if (status === 'running' && progress === 100) {
            // Užduotis beveik baigta
            this.showNotification(
                "Užduotis baigiama", 
                `Užduotis #${taskId} beveik baigta (${progress}%)`, 
                "info"
            );
        } else if (status === 'completed') {
            // Užduotis sėkmingai baigta
            this.showNotification(
                "Užduotis baigta", 
                `Užduotis #${taskId} sėkmingai baigta`, 
                "success"
            );
        } else if (status === 'failed') {
            // Užduotis nepavyko
            this.showNotification(
                "Užduotis nepavyko", 
                `Užduotis #${taskId} nepavyko įvykdyti`, 
                "danger"
            );
        }
        
        // Atnaujiname UI elementus, jei tokių yra
        this.updateTaskUI(taskId, status, progress);
    },
    
    // Rodo naują pranešimą
    showNotification: function(title, message, status = 'info') {
        // Sukuriame pranešimo elementą
        const notification = document.createElement('div');
        notification.className = `toast show bg-light`;
        notification.setAttribute('role', 'alert');
        notification.setAttribute('aria-live', 'assertive');
        notification.setAttribute('aria-atomic', 'true');
        
        // Nustatome spalvą pagal būseną
        let borderColor;
        switch (status) {
            case 'success':
                borderColor = '#28a745';
                break;
            case 'danger':
                borderColor = '#dc3545';
                break;
            case 'warning':
                borderColor = '#ffc107';
                break;
            case 'primary':
                borderColor = '#007bff';
                break;
            default:
                borderColor = '#17a2b8'; // info
        }
        
        notification.style.borderLeft = `4px solid ${borderColor}`;
        notification.style.marginBottom = '10px';
        notification.style.boxShadow = '0 4px 8px rgba(0,0,0,0.1)';
        
        // Sukuriame pranešimo turinį
        notification.innerHTML = `
            <div class="toast-header">
                <strong class="me-auto">${title}</strong>
                <small class="text-muted">Ką tik</small>
                <button type="button" class="btn-close" aria-label="Uždaryti"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        `;
        
        // Nustatome uždarymo mygtuko veikimą
        const closeButton = notification.querySelector('.btn-close');
        closeButton.addEventListener('click', () => {
            this.removeNotification(notification);
        });
        
        // Įtraukiame į pranešimų sąrašą
        this.notifications.push(notification);
        
        // Įdedame į konteinerį
        this.container.prepend(notification);
        
        // Tikriname ar neviršijome maksimalaus kiekio
        this.checkNotificationsLimit();
        
        // Nustatome automatinį pranešimo išnykimą
        setTimeout(() => {
            this.removeNotification(notification);
        }, this.duration);
        
        return notification;
    },
    
    // Pašalina pranešimą
    removeNotification: function(notification) {
        // Jei pranešimas jau pašalintas, išeiname
        if (!notification.parentNode) {
            return;
        }
        
        // Pridedame išnykimo animaciją
        notification.classList.add('fade-out');
        
        // Pašaliname po animacijos
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
                
                // Pašaliname iš sąrašo
                const index = this.notifications.indexOf(notification);
                if (index > -1) {
                    this.notifications.splice(index, 1);
                }
            }
        }, 300);
    },
    
    // Tikriname ar neviršijome maksimalaus pranešimų kiekio
    checkNotificationsLimit: function() {
        if (this.notifications.length > this.maxNotifications) {
            // Pašaliname seniausius pranešimus
            const notificationsToRemove = this.notifications.slice(0, this.notifications.length - this.maxNotifications);
            
            notificationsToRemove.forEach(notification => {
                this.removeNotification(notification);
            });
        }
    },
    
    // Atnaujina užduoties elementus UI, jei jie yra puslapyje
    updateTaskUI: function(taskId, status, progress) {
        // Atnaujiname progreso juostas
        const progressBars = document.querySelectorAll(`.progress-bar[data-task-id="${taskId}"]`);
        progressBars.forEach(bar => {
            bar.style.width = `${progress}%`;
            bar.textContent = `${progress}%`;
            bar.setAttribute('aria-valuenow', progress);
        });
        
        // Atnaujiname būsenos žymas
        const statusBadges = document.querySelectorAll(`.task-status[data-task-id="${taskId}"]`);
        statusBadges.forEach(badge => {
            // Pašaliname visas būsenos klases
            badge.classList.remove('bg-secondary', 'bg-primary', 'bg-success', 'bg-danger');
            
            // Pridedame naują būsenos klasę
            if (status === 'pending') {
                badge.classList.add('bg-secondary');
                badge.textContent = 'Laukianti';
            } else if (status === 'running') {
                badge.classList.add('bg-primary');
                badge.textContent = 'Vykdoma';
            } else if (status === 'completed') {
                badge.classList.add('bg-success');
                badge.textContent = 'Baigta';
            } else if (status === 'failed') {
                badge.classList.add('bg-danger');
                badge.textContent = 'Klaida';
            }
        });
    }
};

// Inicializuojame pranešimų sistemą, kai puslapis užkraunamas
document.addEventListener('DOMContentLoaded', function() {
    BTCNotifications.init();
});