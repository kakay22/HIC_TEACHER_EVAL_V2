const main = document.querySelector('main');

// SAVE scroll
window.addEventListener('beforeunload', function () {
    if (main) {
        localStorage.setItem('scrollPosition', main.scrollTop);
    }
});

// RESTORE scroll (earlier = faster)
document.addEventListener('DOMContentLoaded', function () {
    const scrollPosition = localStorage.getItem('scrollPosition');

    if (main && scrollPosition !== null) {
        main.scrollTop = parseInt(scrollPosition);
        localStorage.removeItem('scrollPosition');
    }
});