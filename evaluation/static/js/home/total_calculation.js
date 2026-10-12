document.addEventListener('change', function (e) {
    if (!e.target.matches('input[type="radio"][data-section]')) return;

    const section = e.target.dataset.section;
    const checked = document.querySelectorAll(`input[data-section="${section}"]:checked`);

    let total = 0;
    checked.forEach(radio => {
        if (!isNaN(radio.value)) {
            total += parseInt(radio.value);
        }
    });

    document.getElementById(`total_${section}`).textContent = total;
});