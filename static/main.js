document.addEventListener('DOMContentLoaded', function () {
    const officeSelect = document.getElementById('office');
    const dateInput = document.getElementById('date');
    const timeSelect = document.getElementById('time');
    let officeHours = {};

    updateAvailableDates();
    updateAvailableTimes();
    officeSelect.addEventListener('change', updateAvailableDates);
    dateInput.addEventListener('change', updateAvailableTimes);

    function updateAvailableDates() {
        const selectedOffice = officeSelect.value;
        const url = `/get_office_schedule/${selectedOffice}`;
        fetch(url)
            .then(response => response.json())
            .then(data => {
                officeHours = data;
                dateInput._flatpickr.set('disable', getDisabledDates());
            });
    }

    function getDisabledDates() {
        const today = new Date();
        return [
            function (date) {
                const dayOfWeek = date.toLocaleString('en-EN', {weekday: 'short'}).toLowerCase();
                return !officeHours[dayOfWeek] || !officeHours[dayOfWeek].start;
            }
        ];
    }


    function updateAvailableTimes() {
        const selectedOffice = officeSelect.value;
        const selectedDate = new Date(dateInput.value);
        const dayOfWeek = selectedDate.toLocaleString('en-EN', {weekday: 'short'}).toLowerCase();
        const url = `/get_office_schedule/${selectedOffice}`;
        const reqsUrl = `/get_records/${selectedOffice}/${dateInput.value}`;
        const excsUrl = `/get_exceptions/${selectedOffice}/${dateInput.value}`;

        fetch(url)
            .then(response => response.json())
            .then(data => {
                const officeHours = data[dayOfWeek];
                timeSelect.innerHTML = '';

                if (officeHours && officeHours.start) {
                    fetch(reqsUrl)
                        .then(response => response.json())
                        .then(records => {
                            fetch(excsUrl)
                                .then(response => response.json())
                                .then(excData => {

                                    let startHour = parseInt(officeHours.start.split(':')[0]);
                                    let endHour = parseInt(officeHours.end.split(':')[0]);
                                    const isActiveAtypical = document.querySelector('#atypical').checked;
                                    if (excData['start_time'] && excData['end_time'] && isActiveAtypical) {
                                        startHour = parseInt(excData['start_time'].split(':')[0]);
                                        endHour = parseInt(excData['end_time'].split(':')[0]);
                                    }
                                    const breakTime = officeHours.break ? officeHours.break.split('-') : [];
                                    for (let hour = startHour; hour < endHour; hour++) {
                                        if (breakTime.length && hour >= parseInt(breakTime[0].split(':')[0]) && hour < parseInt(breakTime[1].split(':')[0])) {
                                            continue;
                                        }
                                        const timeString = `${hour}:00`;
                                        if (!records.includes(timeString)) {
                                            const option = document.createElement('option');
                                            option.value = timeString;
                                            option.text = timeString;
                                            timeSelect.appendChild(option);
                                        }
                                    }
                                });
                        });
                }
            });
    }

    flatpickr(dateInput, {
        locale: "ru",
        firstDayOfWeek: 1,
        minDate: 'today',
        maxDate: new Date().fp_incr(365),
        disable: getDisabledDates()
    });
    document.querySelectorAll('.status-radio').forEach(elem => {
        elem.addEventListener('change', function (event) {
            const reqId = this.name;
            const newStatus = this.value;
            console.log(newStatus);
            updateStatus(reqId, newStatus);
        });
    });

    function updateStatus(reqId, newStatus) {
        fetch(`/update_status/${reqId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({status: newStatus}),
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    console.log('Статус успешно обновлен');
                    if (newStatus !== 'Новый') {
                        const reqRow = document.querySelector(`.req-${reqId}`);
                        console.log(reqRow);
                        if (reqRow) {
                            reqRow.remove();
                        }
                    }
                } else {
                    console.error('Ошибка обновления статуса');
                }
            })
            .catch(err => {
                console.log(err);
            });
    }

    updateAvailableDates();
});

document.querySelector('.open-form').addEventListener('click', () => {
    document.querySelector('.form--form').classList.remove('hidden');
});


document.querySelector('.close-form').addEventListener('click', () => {
    document.querySelector('.form--form').classList.add('hidden');
});

function sortTable(columnIndex) {
    const table = document.querySelector('.requests-table');
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.rows);

    rows.sort((rowA, rowB) => {
        const cellA = rowA.cells[columnIndex].textContent.trim();
        const cellB = rowB.cells[columnIndex].textContent.trim();

        if (columnIndex === 5) { // Сортировка по дате
            const dateA = new Date(cellA.split('.').reverse().join('-'));
            const dateB = new Date(cellB.split('.').reverse().join('-'));
            return dateA - dateB;
        } else if (columnIndex === 6) { // Сортировка по времени
            const dateA = new Date(rowA.cells[5].textContent.trim().split('.').reverse().join('-'));
            const dateB = new Date(rowB.cells[5].textContent.trim().split('.').reverse().join('-'));
            if (dateA - dateB === 0) { // Если даты одинаковые, сортируем по времени
                const timeA = rowA.cells[6].textContent.trim();
                const timeB = rowB.cells[6].textContent.trim();
                return timeA.localeCompare(timeB);
            } else {
                return dateA - dateB;
            }
        } else {
            return cellA.localeCompare(cellB);
        }
    });

    // Перерисовка таблицы в новом порядке с учетом заголовка
    rows.forEach(row => {
        tbody.appendChild(row); // Переносим строки в порядке сортировки
    });
}

const filterOfficeSelect = document.getElementById('filter-office');
filterOfficeSelect.addEventListener('change', function () {
    const selectedOffice = this.value.toLowerCase();

    const table = document.querySelector('.requests-table');
    const rows = Array.from(table.rows);
    console.log(rows[0].cells);
    rows.forEach(row => {
        const officeCell = row.cells[4].textContent.trim().toLowerCase();
        if (selectedOffice === '' || officeCell === selectedOffice) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
    rows[0].style.display = '';
});


function exportToExcel() {
    const table = document.querySelector('.requests-table');
    const rows = Array.from(table.querySelectorAll('tbody tr'));
    rows.shift();

    const data = rows.map(row => {
        // Проверяем стиль display у строки
        if (window.getComputedStyle(row).display !== 'none') {
            // Формируем массив данных для текущей видимой строки
            const rowData = Array.from(row.cells).map(cell => cell.textContent.trim());
            // Устанавливаем значение "Новый" в столбец "Статус"
            rowData[7] = 'Новый'; // 5 - индекс столбца "Статус"
            return rowData;
        }
        return null; // Пропускаем скрытые строки
    }).filter(Boolean);
    console.log(data);
    const worksheet = XLSX.utils.aoa_to_sheet([['Фамилия', 'Имя', 'Отчество', 'Телефон', 'Офис', 'Дата', 'Время', 'Статус'], ...data]);
    worksheet['!cols'] = [
        {wch: 18}, // Ширина столбца для ФИО
        {wch: 18}, // Ширина столбца для ФИО
        {wch: 18}, // Ширина столбца для ФИО
        {wch: 12}, // Ширина столбца для Телефон
        {wch: 30}, // Ширина столбца для Офис
        {wch: 10}, // Ширина столбца для Дата
        {wch: 10}, // Ширина столбца для Время
        {wch: 10}, // Ширина столбца для Статус
    ];
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, 'Записи');

    const today = new Date();
    const fileName = 'records_' + today.getFullYear() + '-' + (today.getMonth() + 1) + '-' + today.getDate() + '.xlsx';

    XLSX.writeFile(workbook, fileName);
}
