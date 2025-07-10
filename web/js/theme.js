
/**
 * Theme Management for Taskmaster Dashboard
 * Handles dark/light mode functionality
 */
class ThemeManager {
    constructor() {
        this.themeKey = 'taskmaster-theme';
        this.darkTheme = 'dark';
        this.lightTheme = 'light';
        this.toggleBtn = document.getElementById('themeToggleBtn');
        this.toggleIcon = this.toggleBtn ? this.toggleBtn.querySelector('i') : null;

        this.initTheme();
        this.setupListeners();
    }

    /**
     * Initialize the theme based on user preference or system preference
     */
    initTheme() {
        // Check if user has previously selected a theme
        const savedTheme = localStorage.getItem(this.themeKey);
        
        if (savedTheme) {
            this.setTheme(savedTheme);
        } else {
            // Check if user prefers dark mode
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            this.setTheme(prefersDark ? this.darkTheme : this.lightTheme);
        }
    }

    /**
     * Set up event listeners
     */
    setupListeners() {
        if (this.toggleBtn) {
            this.toggleBtn.addEventListener('click', () => this.toggleTheme());
        }

        // Listen for system theme changes
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
            if (!localStorage.getItem(this.themeKey)) {
                this.setTheme(e.matches ? this.darkTheme : this.lightTheme);
            }
        });
    }

    /**
     * Toggle between dark and light themes
     */
    toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme') || this.lightTheme;
        const newTheme = currentTheme === this.darkTheme ? this.lightTheme : this.darkTheme;
        
        this.setTheme(newTheme);
        localStorage.setItem(this.themeKey, newTheme);
    }

    /**
     * Set the theme
     * @param {string} theme - The theme to set ('dark' or 'light')
     */
    setTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        
        if (this.toggleIcon) {
            this.toggleIcon.textContent = theme === this.darkTheme ? 'light_mode' : 'dark_mode';
        }
    }
}

// Initialize theme manager when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new ThemeManager();
});
