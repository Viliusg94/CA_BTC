// FullCalendar lietuvių kalbos lokalizacijos failas
// Šis failas užtikrina, kad kalendorius rodytų lietuviškus mėnesių ir dienų pavadinimus

document.addEventListener('DOMContentLoaded', function() {
    // Registruojame lietuvių kalbos nustatymus FullCalendar bibliotekai
    if (FullCalendar && FullCalendar.globalLocales) {
        FullCalendar.globalLocales.push({
            code: 'lt',
            week: {
                dow: 1, // Savaitė prasideda nuo pirmadienio
                doy: 4  // Metų pirma savaitė yra ta, kurioje yra sausio 4 d.
            },
            buttonText: {
                prev: 'Atgal',
                next: 'Pirmyn',
                today: 'Šiandien',
                month: 'Mėnuo',
                week: 'Savaitė',
                day: 'Diena',
                list: 'Sąrašas'
            },
            weekText: 'SAV',
            allDayText: 'Visą dieną',
            moreLinkText: 'daugiau',
            noEventsText: 'Nėra įvykių',
            // Mėnesių pavadinimai
            monthNames: [
                'Sausis', 'Vasaris', 'Kovas', 'Balandis', 'Gegužė', 'Birželis',
                'Liepa', 'Rugpjūtis', 'Rugsėjis', 'Spalis', 'Lapkritis', 'Gruodis'
            ],
            // Trumpi mėnesių pavadinimai
            monthNamesShort: [
                'Sau', 'Vas', 'Kov', 'Bal', 'Geg', 'Bir',
                'Lie', 'Rgp', 'Rgs', 'Spa', 'Lap', 'Grd'
            ],
            // Dienų pavadinimai
            dayNames: [
                'Sekmadienis', 'Pirmadienis', 'Antradienis', 'Trečiadienis',
                'Ketvirtadienis', 'Penktadienis', 'Šeštadienis'
            ],
            // Trumpi dienų pavadinimai
            dayNamesShort: [
                'Sek', 'Pir', 'Ant', 'Tre', 'Ket', 'Pen', 'Šeš'
            ]
        });
        
        console.log('Lietuvių kalbos lokalizacija sėkmingai užregistruota');
    } else {
        console.error('FullCalendar biblioteka nerasta. Įsitikinkite, kad ji įtraukta prieš šį failą.');
    }
});