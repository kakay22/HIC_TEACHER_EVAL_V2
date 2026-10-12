document.addEventListener("DOMContentLoaded", () => {

    const form = document.querySelector("form");
    const STORAGE_KEY = "teacher_evaluation_draft";

    if (!form) return;

    // ================= DEBOUNCE =================
    function debounce(func, delay = 600) {
        let timeout;
        return function (...args) {
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(this, args), delay);
        };
    }

    // ================= TOAST =================
    function showDraftToast() {

        const toast = document.getElementById("draftStatus");
        if (!toast) return;

        const inner = toast.querySelector(".toast-inner");
        const progress = document.getElementById("toastProgress");

        toast.classList.remove("hidden");

        // slide in
        setTimeout(() => {
            inner.classList.remove("translate-y-4", "opacity-0");
            inner.classList.add("translate-y-0", "opacity-100");
        }, 10);

        // reset progress
        if (progress) {
            progress.style.transition = "none";
            progress.style.width = "100%";

            setTimeout(() => {
                progress.style.transition = "width 1.2s linear";
                progress.style.width = "0%";
            }, 50);
        }

        clearTimeout(window.toastTimeout);

        window.toastTimeout = setTimeout(() => {

            inner.classList.add("translate-y-4", "opacity-0");
            inner.classList.remove("translate-y-0", "opacity-100");

            setTimeout(() => {
                toast.classList.add("hidden");
            }, 300);

        }, 1200);
    }

    // ================= SAVE DRAFT =================
    const saveDraft = debounce(function () {

    // Prevent saving while clearing
    if (isClearingForm) return;

        const formData = {};

        form.querySelectorAll("input, textarea, select").forEach(el => {

            if (!el.name) return;

            // RADIO
            if (el.type === "radio") {
                if (el.checked) {
                    formData[el.name] = el.value;
                }
                return;
            }

            // SELECT2 TEACHER
            if (el.name === "teacher") {

                const teacherData = $("#teacherSelect").select2("data")[0];

                if (teacherData) {
                    formData[el.name] = {
                        id: teacherData.id,
                        text: teacherData.text
                    };
                }

                return;
            }

            formData[el.name] = el.value;
        });

        localStorage.setItem(
            STORAGE_KEY,
            JSON.stringify(formData)
        );

        showDraftToast();

    }, 600);

    // ================= LOAD DRAFT =================
    function loadDraft() {

        const saved = localStorage.getItem(STORAGE_KEY);
        if (!saved) return;

        const data = JSON.parse(saved);

        Object.keys(data).forEach(name => {

            const value = data[name];

            // RADIO
            const radio = form.querySelector(
                `input[name="${name}"][value="${value}"]`
            );

            if (radio) {
                radio.checked = true;
                return;
            }

            // SELECT2
            if (
                name === "teacher" &&
                value &&
                typeof value === "object" &&
                value.id
            ) {
                const option = new Option(
                    value.text,
                    value.id,
                    true,
                    true
                );

                $("#teacherSelect")
                    .append(option)
                    .trigger("change");

                return;
            }

            // NORMAL INPUTS
            const field = form.querySelector(`[name="${name}"]`);

            if (field) {
                field.value = value;
            }
        });

        // refresh totals
        document.querySelectorAll(".rating-radio").forEach(radio => {
            radio.dispatchEvent(new Event("change"));
        });
    }

    // ================= EVENTS =================
    form.addEventListener("input", saveDraft);
    form.addEventListener("change", saveDraft);

    // ================= INIT =================
    loadDraft();

    form.addEventListener("submit", () => {
        localStorage.removeItem(STORAGE_KEY);
    });

});