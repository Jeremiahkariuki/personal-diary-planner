(function () {
    // ── Dark / Light theme ──────────────────────────────────────────────────────
    const applyTheme = (theme) => {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);

        const lightBtn = document.getElementById('lightThemeBtn');
        const darkBtn  = document.getElementById('darkThemeBtn');

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

    // ── Custom colour palette (saved from Settings > Customise) ─────────────────
    const applyCustomColors = () => {
        const p = localStorage.getItem('color_accentPrimary');
        const s = localStorage.getItem('color_accentSecondary');
        const b = localStorage.getItem('color_background');
        if (p) document.documentElement.style.setProperty('--accent-primary',   p);
        if (s) document.documentElement.style.setProperty('--accent-secondary', s);
        if (b) document.documentElement.style.setProperty('--bg-color',         b);
    };

    // Apply custom colors immediately (before paint)
    applyCustomColors();

    // Init UI after DOM is ready
    document.addEventListener('DOMContentLoaded', () => {
        const theme = localStorage.getItem('theme') || 'dark';
        applyTheme(theme);

        const lightBtn = document.getElementById('lightThemeBtn');
        const darkBtn  = document.getElementById('darkThemeBtn');

        if (lightBtn) lightBtn.addEventListener('click', () => applyTheme('light'));
        if (darkBtn)  darkBtn.addEventListener('click',  () => applyTheme('dark'));

        // Smooth scroll and highlight customize section if landed with hash
        const customiseSection = document.getElementById('customiseSection');
        if (customiseSection && window.location.hash === '#customiseSection') {
            setTimeout(() => {
                customiseSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
                customiseSection.style.outline = '2px solid var(--accent-primary)';
                setTimeout(() => {
                    customiseSection.style.outline = 'none';
                }, 1500);
            }, 300);
        }
    });

    // Handle system theme changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
        if (!localStorage.getItem('theme')) {
            applyTheme(e.matches ? 'dark' : 'light');
        }
    });
})();
