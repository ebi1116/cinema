document.addEventListener('DOMContentLoaded', () => {
    const selectedSeats = document.querySelector('#selectedSeats');
    const seatInputs = document.querySelectorAll('.seat input[type="checkbox"]');

    if (!selectedSeats || !seatInputs.length) {
        return;
    }

    const updateSelectedSeats = () => {
        const seats = Array.from(seatInputs)
            .filter((input) => input.checked)
            .map((input) => input.value);
        selectedSeats.textContent = seats.length ? seats.join(', ') : 'None';
    };

    seatInputs.forEach((input) => input.addEventListener('change', updateSelectedSeats));
});
