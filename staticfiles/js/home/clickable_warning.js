document.addEventListener('DOMContentLoaded', function () {
        const helpBtn = document.getElementById('duplicateHelpBtn');
        const tooltip = document.getElementById('duplicateTooltip');

        helpBtn.addEventListener('click', function (e) {
            e.stopPropagation(); // Prevent clicks from bubbling
            tooltip.classList.toggle('hidden');
        });

        // Click anywhere outside to close the tooltip
        document.addEventListener('click', function () {
            if (!tooltip.classList.contains('hidden')) {
                tooltip.classList.add('hidden');
            }
        });

        // Optional: prevent tooltip click from closing immediately
        tooltip.addEventListener('click', function (e) {
            e.stopPropagation();
        });

        // Make tooltip toggle on click
        helpBtn.addEventListener("click", function (e) {
            e.stopPropagation();          // prevent click from bubbling to document
            tooltip.classList.toggle("hidden");
        });

        // Close tooltip if clicking outside
        document.addEventListener("click", function (e) {
            // Only hide if clicked outside the help button or tooltip itself
            if (!tooltip.contains(e.target) && e.target !== helpBtn) {
                tooltip.classList.add("hidden");
            }
        });

        // Optional: allow touch devices to toggle tooltip
        helpBtn.addEventListener("touchstart", function(e) {
            e.stopPropagation();
            tooltip.classList.toggle("hidden");
        }, {passive: true});
    });