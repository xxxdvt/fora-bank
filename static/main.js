document.addEventListener('DOMContentLoaded', function () {
    const officeSelect = document.getElementById('office');
    const dateInput = document.getElementById('date');
    const timeSelect = document.getElementById('time');
    let officeHours = {};

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

        fetch(url)
            .then(response => response.json())
            .then(data => {
                const officeHours = data[dayOfWeek];
                timeSelect.innerHTML = '';

                if (officeHours && officeHours.start) {
                    fetch(reqsUrl)
                        .then(response => response.json())
                        .then(records => {
                            const startHour = parseInt(officeHours.start.split(':')[0]);
                            const endHour = parseInt(officeHours.end.split(':')[0]);
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
                }
            });
    }

    flatpickr(dateInput, {
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