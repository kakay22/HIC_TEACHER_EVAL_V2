// =================== Dark Theme Handler ===================

// Immediately apply theme from localStorage or system preference
(function () {

    const html = document.documentElement;
    const savedTheme = localStorage.getItem("theme");

    if (
        savedTheme === "dark" ||
        (!savedTheme && window.matchMedia("(prefers-color-scheme: dark)").matches)
    ) {
        html.classList.add("dark");
    } else {
        html.classList.remove("dark");
    }

})();


// Update icon after page loads
document.addEventListener("DOMContentLoaded", updateThemeIcon);


// Function to toggle theme manually
function toggleTheme() {

    const html = document.documentElement;

    if (html.classList.contains("dark")) {
        html.classList.remove("dark");
        localStorage.setItem("theme", "light");
    } else {
        html.classList.add("dark");
        localStorage.setItem("theme", "dark");
    }

    updateThemeIcon();

}


// Change the icon
function updateThemeIcon() {

    const icon = document.getElementById("themeIcon");

    if (!icon) return;

    if (document.documentElement.classList.contains("dark")) {
        icon.textContent = "light_mode"; // sun icon
    } else {
        icon.textContent = "dark_mode"; // moon icon
    }

}


// Tailwind config
tailwind.config = {
    darkMode: "class",
    theme: {
        extend: {
            transitionProperty: {
                width: "width",
            },
        },
    },
};