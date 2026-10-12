document.addEventListener('DOMContentLoaded', function () {
    const clearBtn = document.getElementById('clearBtn');
    const modal = document.getElementById('clearModal');
    const cancelBtn = document.getElementById('cancelClear');
    const confirmBtn = document.getElementById('confirmClear');
    const form = document.querySelector('form');

    // Open modal
    clearBtn.addEventListener('click', () => {
        modal.classList.remove('hidden');
        modal.classList.add('flex');
    });

    // Cancel
    cancelBtn.addEventListener('click', () => {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    });

    // Helper to reset validation errors
    function resetValidation() {
        const studentIdWarning = document.getElementById("studentIdWarning");
        const duplicateWarning = document.getElementById("duplicateWarning");
        const submitBtn = form.querySelector("button[type='submit']");

        // Hide warnings
        if (studentIdWarning) studentIdWarning.classList.add("hidden");
        if (duplicateWarning) duplicateWarning.classList.add("hidden");

        // Remove red borders
        ["student_id", "teacher", "subject", "semester", "academic_year"].forEach(name => {
            const el = form[name];
            if (!el) return;
            const tsControl = el.tomselect?.control;
            const select2Selection = el.nextElementSibling?.querySelector('.select2-selection');
            const target = tsControl || select2Selection || el;

            target.classList.remove("border-red-500");
            target.classList.add("border-gray-300", "dark:border-gray-600");
        });

        // Enable submit
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.classList.remove("opacity-50", "cursor-not-allowed");
        }
    }

    // Confirm clear
    confirmBtn.addEventListener('click', () => {

        // Reset form
        form.reset();

        // Remove saved draft from localStorage
        localStorage.removeItem("teacher_evaluation_draft");

        // Clear validation UI
        resetValidation();

        // Optional: clear Select2
        if ($("#teacherSelect").length) {
            $("#teacherSelect").val(null).trigger("change");
        }

        // Close modal
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    });

    // Click outside to close
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
        }
    });
});