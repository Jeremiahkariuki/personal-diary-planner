(function () {
    // Theme toggle logic
    const applyTheme = (theme) => {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);

        // Update UI if on page
        const lightBtn = document.getElementById('lightThemeBtn');
        const darkBtn = document.getElementById('darkThemeBtn');

        if (lightBtn && darkBtn) {
            if (theme === 'light') {
                lightBtn.classList.add('active');
                darkBtn.classList.remove('active');
            } else {
                darkBtn.classList.add('active');
                lightBtn.classList.remove('active');
            }
        }
    };

    // Initialize UI on DOMContentLoaded
    document.addEventListener('DOMContentLoaded', () => {
        const theme = localStorage.getItem('theme') || 'dark';
        applyTheme(theme);

        const lightBtn = document.getElementById('lightThemeBtn');
        const darkBtn = document.getElementById('darkThemeBtn');

        if (lightBtn) {
            lightBtn.addEventListener('click', () => applyTheme('light'));
        }
        if (darkBtn) {
            darkBtn.addEventListener('click', () => applyTheme('dark'));
        }
    });

    // Handle system theme changes (optional but nice)
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
        if (!localStorage.getItem('theme')) {
            applyTheme(e.matches ? 'dark' : 'light');
        }
    });
})();
