
$(document).ready(function () {
    const teacherSelect = $("#teacherSelect");

    if (!teacherSelect.length) {
        return;
    }

    // Avoid initializing Select2 more than once.
    if (teacherSelect.hasClass("select2-hidden-accessible")) {
        teacherSelect.select2("destroy");
    }

    
    teacherSelect.select2({
        placeholder: "Select Teacher",
        allowClear: true,
        minimumInputLength: 0,
        ajax: {
            url: teacherSelect.data("ajax-url"),
            dataType: "json",
            delay: 250,

            data: function (params) {
                return {
                    q: params.term || ""
                };
            },

            processResults: function (data) {
                return {
                    results: Array.isArray(data.results)
                        ? data.results
                        : []
                };
            },

            cache: true
        },
        width: "100%",
        dropdownCssClass: "dark-select2-dropdown",
        containerCssClass: "dark-select2-container"
    });


    function applyDarkMode() {
        const isDark = document.documentElement.classList.contains("dark");
        const select2Data = teacherSelect.data("select2");

        if (!select2Data) {
            return;
        }

        const $container = select2Data.$container.find(".select2-selection");
        const $dropdown = $(".select2-container--open .select2-dropdown");
        const $search = $dropdown.find(".select2-search__field");

        if (isDark) {
            $container.css({
                "background-color": "#374151",
                color: "white",
                "border-color": "#4b5563"
            });

            $container.find(".select2-selection__placeholder").css(
                "color",
                "#d1d5db"
            );

            $container.find(".select2-selection__rendered").css(
                "color",
                "white"
            );

            $search.css({
                "background-color": "#374151",
                color: "white",
                "border-color": "#4b5563"
            });
        } else {
            $container.css({
                "background-color": "",
                color: "",
                "border-color": ""
            });

            $container.find(".select2-selection__placeholder").css(
                "color",
                ""
            );

            $container.find(".select2-selection__rendered").css(
                "color",
                ""
            );

            $search.css({
                "background-color": "",
                color: "",
                "border-color": ""
            });
        }
    }

    applyDarkMode();

    // Apply styling when opening the Select2 dropdown.
    teacherSelect.on("select2:open", applyDarkMode);

    // Observe dynamic dark-mode toggles.
    const observer = new MutationObserver(applyDarkMode);

    observer.observe(document.documentElement, {
        attributes: true,
        attributeFilter: ["class"]
    });
});
