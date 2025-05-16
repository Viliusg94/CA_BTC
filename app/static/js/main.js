// Pagrindinis JavaScript failas

document.addEventListener("DOMContentLoaded", function() {
    // Automatiškai paslepia pranešimų laukelius po 5 sekundžių
    var alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            alert.style.opacity = '0';
            setTimeout(function() {
                alert.style.display = 'none';
            }, 500);
        }, 5000);
    });
    
    // Atnaujina laikrodį kas sekundę
    setInterval(function() {
        var timeElement = document.getElementById('current-time');
        if (timeElement) {
            var now = new Date();
            var formattedTime = now.getFullYear() + '-' + 
                                pad(now.getMonth() + 1) + '-' + 
                                pad(now.getDate()) + ' ' + 
                                pad(now.getHours()) + ':' + 
                                pad(now.getMinutes()) + ':' + 
                                pad(now.getSeconds());
            timeElement.textContent = formattedTime;
        }
    }, 1000);
});

// Pagalbinė funkcija skaičiams su nuliu priekyje
function pad(num) {
    return (num < 10) ? '0' + num : num;
}