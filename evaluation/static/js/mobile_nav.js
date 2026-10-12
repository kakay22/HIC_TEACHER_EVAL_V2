
document.addEventListener("DOMContentLoaded", function () {

    const nav = document.getElementById("mobileNav");
    if (!nav) return;

    let lastScroll = 0;
    let isHidden = false;
    let idleTimer;

    function showNav() {
        nav.style.transform = "translateY(0)";
        nav.style.opacity = "1";
        isHidden = false;
    }

    function hideNav() {
        nav.style.transform = "translateY(120%)";
        nav.style.opacity = "0";
        isHidden = true;
    }

    // 🔥 ONE handler for ALL scroll sources
    function handleScroll(currentScroll) {
        if (currentScroll > lastScroll) {
            if (!isHidden) hideNav();
        } else {
            if (isHidden) showNav();
        }

        lastScroll = currentScroll;
        resetIdleTimer();
    }

    // ✅ WINDOW scroll
    window.addEventListener("scroll", () => {
        handleScroll(window.pageYOffset);
    });

    // ✅ ALL SCROLLABLE ELEMENTS
    document.querySelectorAll("*").forEach(el => {
        const style = getComputedStyle(el);

        if (style.overflowY === "auto" || style.overflowY === "scroll") {
            el.addEventListener("scroll", () => {
                handleScroll(el.scrollTop);
            });
        }
    });

    // TOUCH → show nav
    document.addEventListener("touchstart", () => {
        showNav();
        resetIdleTimer();
    });

    // IDLE
    function resetIdleTimer() {
        clearTimeout(idleTimer);
        idleTimer = setTimeout(() => {
            hideNav();
        }, 6000);
    }

    resetIdleTimer();

});