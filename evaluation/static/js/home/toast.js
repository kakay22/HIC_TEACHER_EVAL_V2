document.addEventListener("DOMContentLoaded", () => {

    document.querySelectorAll('.animate-slideUp').forEach(toast => {

        let startX = 0;
        let currentX = 0;
        let isDragging = false;

        const threshold = 80;

        const start = (e) => {
            isDragging = true;
            startX = e.touches ? e.touches[0].clientX : e.clientX;
            toast.style.transition = 'none';
        };

        const move = (e) => {
            if (!isDragging) return;

            currentX = e.touches ? e.touches[0].clientX : e.clientX;
            let diff = currentX - startX;

            toast.style.transform = `translateX(${diff}px)`;
            toast.style.opacity = 1 - Math.abs(diff) / 200;
        };

        const end = () => {
            if (!isDragging) return;
            isDragging = false;

            let diff = currentX - startX;

            toast.style.transition = 'all 0.3s ease';

            if (Math.abs(diff) > threshold) {
                toast.style.transform = `translateX(${diff > 0 ? 300 : -300}px)`;
                toast.style.opacity = '0';
                setTimeout(() => toast.remove(), 300);
            } else {
                toast.style.transform = 'translateX(0)';
                toast.style.opacity = '1';
            }
        };

        // EVENTS
        toast.addEventListener('touchstart', start);
        toast.addEventListener('touchmove', move);
        toast.addEventListener('touchend', end);

        toast.addEventListener('mousedown', start);
        toast.addEventListener('mousemove', move);
        toast.addEventListener('mouseup', end);
        toast.addEventListener('mouseleave', end);

        // AUTO DISMISS
        let timeout = setTimeout(() => {
            toast.style.transition = 'all 0.3s ease';
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(10px)';
            setTimeout(() => toast.remove(), 300);
        }, 2500);

        // PAUSE ON INTERACT
        toast.addEventListener('mouseenter', () => clearTimeout(timeout));
        toast.addEventListener('touchstart', () => clearTimeout(timeout));
    });

});