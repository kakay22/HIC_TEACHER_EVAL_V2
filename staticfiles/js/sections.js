document.addEventListener('DOMContentLoaded', () => {


    // ✅ RESTORE ACTIVE SECTION
    const activeSection = localStorage.getItem('activeSection');

    document.querySelectorAll('.section-header').forEach(header => {
        const id = header.dataset.sectionId;
        const body = document.getElementById(`section-${id}`);
        const icon = header.querySelector('.arrow-icon');

        if (id === activeSection) {
            body.classList.remove('d-none');
            icon.classList.add('rotate');
        } else {
            body.classList.add('d-none');
            icon.classList.remove('rotate');
        }
    });

    // ✅ ACCORDION BEHAVIOR (ONLY ONE OPEN)
    document.querySelectorAll('.section-header').forEach(header => {
        header.addEventListener('click', (e) => {
            if(e.target.closest('.dropdown') || e.target.closest('button')) return;

            const id = header.dataset.sectionId;
            const body = document.getElementById(`section-${id}`);
            const icon = header.querySelector('.arrow-icon');

            const isCurrentlyOpen = !body.classList.contains('d-none');

            // 🔴 CLOSE ALL
            document.querySelectorAll('.section-body').forEach(b => b.classList.add('d-none'));
            document.querySelectorAll('.arrow-icon').forEach(i => i.classList.remove('rotate'));

            if (!isCurrentlyOpen) {
                // ✅ OPEN SELECTED
                body.classList.remove('d-none');
                icon.classList.add('rotate');

                localStorage.setItem('activeSection', id);
            } else {
                // ❌ CLOSE ALL (no active section)
                localStorage.removeItem('activeSection');
            }
        });
    });

    // ADD SECTION
    showAddSectionForm.onclick = () => addSectionForm.classList.remove('d-none');
    cancelAddSection.onclick = () => addSectionForm.classList.add('d-none');

    // EDIT SECTION
    document.querySelectorAll('.edit-section-btn').forEach(btn => {
        btn.onclick = () => document.getElementById(`editSectionForm-${btn.dataset.sectionId}`).classList.toggle('d-none');
    });
    document.querySelectorAll('.cancel-edit-section').forEach(btn => {
        btn.onclick = () => document.getElementById(`editSectionForm-${btn.dataset.sectionId}`).classList.add('d-none');
    });

    // ADD QUESTION
    document.querySelectorAll('.show-add-question-form').forEach(btn => {
        btn.onclick = () => {
            const id = btn.dataset.sectionId;
            document.getElementById(`addQuestionForm-${id}`).classList.remove('d-none');
            btn.classList.add('d-none');
        };
    });
    document.querySelectorAll('.cancel-add-question').forEach(btn => {
        btn.onclick = () => {
            const id = btn.dataset.sectionId;
            document.getElementById(`addQuestionForm-${id}`).classList.add('d-none');
            document.querySelector(`.show-add-question-form[data-section-id="${id}"]`).classList.remove('d-none');
        };
    });

    // EDIT QUESTION
    document.querySelectorAll('.edit-question-btn').forEach(btn => {
        btn.onclick = () => {
            const id = btn.dataset.questionId;
            document.getElementById(`editQuestionInput-${id}`).classList.remove('d-none');
            document.getElementById(`editQuestionForm-${id}`).classList.remove('d-none');
            document.querySelector(`.question-text-${id}`).classList.add('d-none');
            // Hide ellipsis button for this question
            btn.closest('.question-item').querySelector('.dropdown').classList.add('d-none');
        };
    });
    document.querySelectorAll('.cancel-edit-question').forEach(btn => {
        btn.onclick = () => {
            const id = btn.dataset.questionId;
            document.getElementById(`editQuestionInput-${id}`).classList.add('d-none');
            document.getElementById(`editQuestionForm-${id}`).classList.add('d-none');
            document.querySelector(`.question-text-${id}`).classList.remove('d-none');
            // Show ellipsis button again
            btn.closest('.question-item').querySelector('.dropdown').classList.remove('d-none');
        };
    });

    // SUBMIT EDIT QUESTION
    document.querySelectorAll('.edit-question-form').forEach(form => {
        form.addEventListener('submit', () => {
            const id = form.id.split('-')[1];
            form.querySelector('.question-hidden-input').value =
                document.getElementById(`editQuestionInput-${id}`).value;
        });
    });

    // DELETE SECTION CONFIRMATION
    let deleteForm = document.getElementById('deleteForm');
    document.querySelectorAll('.delete-section-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const sectionId = btn.dataset.sectionId;
                deleteForm.action = `/sections/${sectionId}/delete/`;
                new bootstrap.Modal(document.getElementById('deleteConfirmModal')).show();
            });
        });
    });

    // DELETE QUESTION CONFIRMATION
    document.querySelectorAll('.delete-question-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const questionId = btn.dataset.questionId;
            deleteForm.action = `/questions/${questionId}/delete/`;
            new bootstrap.Modal(document.getElementById('deleteConfirmModal')).show();
        });
    });