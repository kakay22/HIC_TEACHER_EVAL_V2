function resetFilters() {

    // 1. Reset all selects (desktop + mobile) WITHOUT triggering change
    document.querySelectorAll('select').forEach(select => {
        select.value = "";
    });

    // 2. Reset text inputs
    document.querySelectorAll('input[type="text"]').forEach(input => {
        input.value = "";
    });

    // 3. Reset TomSelect / Select2 safely
    document.querySelectorAll('select').forEach(select => {
        if (select.tomselect) {
            select.tomselect.clear();
        }
    });

    // 4. Ensure sort explicitly resets
    const sort = document.getElementById('sortSelect');
    if (sort) sort.value = "";

    const sortMobile = document.getElementById('sortSelectMobile');
    if (sortMobile) sortMobile.value = "";

    // 5. SINGLE CONTROLLED FETCH (prevents flicker)
    setTimeout(() => {
        try {
            fetchData();
        } catch (err) {
            console.error("fetchData failed:", err);
        }
    }, 50);
}