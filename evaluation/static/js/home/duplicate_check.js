/* ===================== Debounce ===================== */
function debounce(func, delay = 400) {
    let timeout;
    return (...args) => {
        clearTimeout(timeout);
        timeout = setTimeout(() => func(...args), delay);
    };
}

/* ===================== INIT ===================== */
document.addEventListener("DOMContentLoaded", () => {

    /* ===================== Elements ===================== */
    const form = document.querySelector("form");

    const previewBtn = document.getElementById("previewBtn");
    const closePreview = document.getElementById("closePreview");
    const editPreview = document.getElementById("editPreview");
    const previewModal = document.getElementById("previewModal");

    const studentIdWarning = document.getElementById("studentIdWarning");
    const duplicateWarning = document.getElementById("duplicateWarning");

    const duplicateHelpBtn = document.getElementById("duplicateHelpBtn");
    const duplicateTooltip = document.getElementById("duplicateTooltip");

    const watchFields = ["student_id", "teacher", "subject", "semester", "academic_year"];

    if (!form) return;

    let isPreviewBlocked = false;

    // ✅ NEW: prevents race condition
    let lastValidationRequest = 0;

    /* ===================== Helpers ===================== */
    function setPreviewDisabled(disabled) {
        isPreviewBlocked = disabled;

        if (!previewBtn) return;
        
        // ✅ REAL disable
        previewBtn.disabled = disabled;

        previewBtn.classList.toggle("opacity-50", disabled);
        previewBtn.classList.toggle("cursor-not-allowed", disabled);
    }

    function highlightField(el, show) {
        if (!el) return;

        const tsControl = el.tomselect?.control;
        const select2Selection = el.nextElementSibling?.querySelector('.select2-selection');
        const target = tsControl || select2Selection || el;

        if (show) {
            target.classList.add("border-red-500");
            target.classList.remove("border-gray-300", "dark:border-gray-600");
        } else {
            target.classList.remove("border-red-500");
            target.classList.add("border-gray-300", "dark:border-gray-600");
        }
    }

    /* ===================== Warnings ===================== */
    function showStudentIdWarning(show) {
        if (!studentIdWarning) return;

        studentIdWarning.classList.toggle("hidden", !show);
        highlightField(form["student_id"], show);
    }

    function showDuplicateWarning(show) {
        if (!duplicateWarning) return;

        duplicateWarning.classList.toggle("hidden", !show);

        watchFields.forEach(name => {
            const el = form[name];
            if (el) highlightField(el, show);
        });
    }

    /* ===================== Validation ===================== */
    async function validateEvaluation() {
        const requestId = ++lastValidationRequest;

        const params = new URLSearchParams();

        watchFields.forEach(name => {
            const val = form[name]?.value?.trim();
            if (val) params.append(name, val);
        });

        if (!params.get("student_id")) {
            showStudentIdWarning(false);
            showDuplicateWarning(false);
            setPreviewDisabled(false);
            return { invalidId: false, duplicate: false };
        }

        try {
            const res = await fetch(
                `${window.location.origin}/validate-evaluation/?${params}`,
                {
                    headers: { "X-Requested-With": "XMLHttpRequest" },
                    credentials: "same-origin"
                }
            );

            const data = await res.json();

            // ✅ Ignore outdated responses
            if (requestId !== lastValidationRequest) return {};

            const invalidId = !data.student_exists;
            const duplicate = data.duplicate;

            showStudentIdWarning(invalidId);
            showDuplicateWarning(duplicate);
            setPreviewDisabled(invalidId || duplicate);

            return { invalidId, duplicate };

        } catch (err) {
            console.error("Validation error:", err);
            setPreviewDisabled(false);
            return { invalidId: false, duplicate: false };
        }
    }

    /* ===================== EVENT LISTENERS ===================== */

    const studentIdInput = form["student_id"];

    if (studentIdInput) {
        studentIdInput.addEventListener("input", debounce(validateEvaluation, 400));
        studentIdInput.addEventListener("change", validateEvaluation);
    }

    watchFields.forEach(name => {
        if (name === "student_id") return;

        const el = form[name];
        if (!el) return;

        el.addEventListener("input", debounce(validateEvaluation, 500));
        el.addEventListener("change", debounce(validateEvaluation, 500));
    });

    /* ===================== Preview Modal ===================== */
    previewBtn?.addEventListener("click", async () => {

        // 🚨 If button is disabled, do NOTHING except scroll
        if (previewBtn.disabled) {
            scrollToFirstError(previewBtn);
            return;
        }
    
        // 🔁 Get fresh validation result
        const result = await validateEvaluation();
    
        // 🚨 HARD BLOCK
        if (result?.invalidId || result?.duplicate) {
            scrollToFirstError(previewBtn);
            return;
        }
    
        // native validation
        if (!form.checkValidity()) {
            form.reportValidity();
            return;
        }
    
        // ✅ SAFE: open modal
        previewModal.classList.remove("hidden");
    
        document.getElementById("p_teacher").innerText =
            $("#teacherSelect option:selected").text();
    
        document.getElementById("p_subject").innerText =
            form.subject?.value || "";
    
        document.getElementById("p_semester").innerText =
            form.semester?.value || "";
    
        document.getElementById("p_year").innerText =
            form.academic_year?.value || "";
    
        document.getElementById("p_student_id").innerText =
            form.student_id?.value || "";
    
        document.getElementById("p_student_name").innerText =
            form.student_name?.value || "None";
    
        document.getElementById("p_comm").innerText =
            form.commendable_features?.value || "None";
    
        document.getElementById("p_suggest").innerText =
            form.suggestions_improvement?.value || "None";
    });

    /* ===================== Prevent invalid submit ===================== */
    form.addEventListener("submit", async (e) => {
        const result = await validateEvaluation();

        if (result?.invalidId || result?.duplicate) {
            e.preventDefault();
            scrollToFirstError(form);
        }
    });

    /* ===================== Modal Controls ===================== */
    closePreview?.addEventListener("click", () => {
        previewModal?.classList.add("hidden");
    });

    editPreview?.addEventListener("click", () => {
        previewModal?.classList.add("hidden");
    });

    /* ===================== Scroll Helpers ===================== */
    function smoothScrollTo(target, duration = 600) {
        const targetPosition = target.getBoundingClientRect().top + window.pageYOffset - 50;
        const startPosition = window.pageYOffset;
        const distance = targetPosition - startPosition;
        let startTime = null;

        function animation(currentTime) {
            if (startTime === null) startTime = currentTime;

            const timeElapsed = currentTime - startTime;
            const progress = Math.min(timeElapsed / duration, 1);

            const ease = progress < 0.5
                ? 2 * progress * progress
                : 1 - Math.pow(-2 * progress + 2, 2) / 2;

            window.scrollTo(0, startPosition + distance * ease);

            if (timeElapsed < duration) {
                requestAnimationFrame(animation);
            }
        }

        requestAnimationFrame(animation);
    }

    function scrollToFirstError(fromElement) {
        let target = null;

        if (!studentIdWarning.classList.contains("hidden")) {
            target = form["student_id"];
        } else if (!duplicateWarning.classList.contains("hidden")) {
            target = form[watchFields[0]];
        } else {
            target = form.querySelector(":invalid");
        }

        if (!target) return;

        const startY = fromElement.getBoundingClientRect().top + window.pageYOffset;
        const targetY = target.getBoundingClientRect().top + window.pageYOffset - 100;

        let startTime = null;
        const duration = 800;

        function animateScroll(currentTime) {
            if (startTime === null) startTime = currentTime;

            const time = currentTime - startTime;
            const progress = Math.min(time / duration, 1);

            const ease = 1 - Math.pow(1 - progress, 3);

            const currentY = startY + (targetY - startY) * ease;

            window.scrollTo(0, currentY);

            if (time < duration) {
                requestAnimationFrame(animateScroll);
            }
        }

        requestAnimationFrame(animateScroll);

        setTimeout(() => {
            target.focus({ preventScroll: true });

            target.classList.add("ring-2", "ring-red-400");
            setTimeout(() => {
                target.classList.remove("ring-2", "ring-red-400");
            }, 1500);

        }, duration);
    }

});