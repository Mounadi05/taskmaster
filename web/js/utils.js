/**
 * Utility Functions for Taskmaster Dashboard
 */

/**
 * DOM Utilities
 */
class DOMUtils {
    /**
     * Get element by ID with error handling
     * @param {string} id - Element ID
     * @returns {HTMLElement|null} Element or null
     */
    static getElementById(id) {
        const element = document.getElementById(id);
        if (!element) {
            console.warn(`Element with ID '${id}' not found`);
        }
        return element;
    }

    /**
     * Create element with attributes and content
     * @param {string} tag - HTML tag name
     * @param {Object} attributes - Element attributes
     * @param {string|HTMLElement} content - Element content
     * @returns {HTMLElement} Created element
     */
    static createElement(tag, attributes = {}, content = '') {
        const element = document.createElement(tag);
        
        Object.entries(attributes).forEach(([key, value]) => {
            if (key === 'className') {
                element.className = value;
            } else if (key === 'dataset') {
                Object.entries(value).forEach(([dataKey, dataValue]) => {
                    element.dataset[dataKey] = dataValue;
                });
            } else {
                element.setAttribute(key, value);
            }
        });

        if (typeof content === 'string') {
            element.innerHTML = content;
        } else if (content instanceof HTMLElement) {
            element.appendChild(content);
        }

        return element;
    }

    /**
     * Add event listener with error handling
     * @param {HTMLElement} element - Target element
     * @param {string} event - Event type
     * @param {Function} handler - Event handler
     * @param {Object} options - Event options
     */
    static addEventListener(element, event, handler, options = {}) {
        if (!element) {
            console.warn('Cannot add event listener to null element');
            return;
        }

        element.addEventListener(event, (e) => {
            try {
                handler(e);
            } catch (error) {
                console.error(`Error in ${event} handler:`, error);
            }
        }, options);
    }

    /**
     * Toggle class on element
     * @param {HTMLElement} element - Target element
     * @param {string} className - Class name to toggle
     * @param {boolean} force - Force add/remove
     */
    static toggleClass(element, className, force = undefined) {
        if (!element) return;
        element.classList.toggle(className, force);
    }

    /**
     * Show/hide element
     * @param {HTMLElement} element - Target element
     * @param {boolean} show - Whether to show the element
     */
    static toggleVisibility(element, show) {
        if (!element) return;
        element.style.display = show ? '' : 'none';
    }
}

/**
 * Animation Utilities
 */
class AnimationUtils {
    /**
     * Fade in element
     * @param {HTMLElement} element - Target element
     * @param {number} duration - Animation duration in ms
     */
    static fadeIn(element, duration = 300) {
        if (!element) return;
        
        element.style.opacity = '0';
        element.style.display = '';
        
        const start = performance.now();
        
        function animate(currentTime) {
            const elapsed = currentTime - start;
            const progress = Math.min(elapsed / duration, 1);
            
            element.style.opacity = progress;
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        }
        
        requestAnimationFrame(animate);
    }

    /**
     * Fade out element
     * @param {HTMLElement} element - Target element
     * @param {number} duration - Animation duration in ms
     */
    static fadeOut(element, duration = 300) {
        if (!element) return;
        
        const start = performance.now();
        const startOpacity = parseFloat(getComputedStyle(element).opacity);
        
        function animate(currentTime) {
            const elapsed = currentTime - start;
            const progress = Math.min(elapsed / duration, 1);
            
            element.style.opacity = startOpacity * (1 - progress);
            
            if (progress >= 1) {
                element.style.display = 'none';
            } else {
                requestAnimationFrame(animate);
            }
        }
        
        requestAnimationFrame(animate);
    }

    /**
     * Slide down element
     * @param {HTMLElement} element - Target element
     * @param {number} duration - Animation duration in ms
     */
    static slideDown(element, duration = 300) {
        if (!element) return;
        
        element.style.height = '0';
        element.style.overflow = 'hidden';
        element.style.display = '';
        
        const targetHeight = element.scrollHeight;
        const start = performance.now();
        
        function animate(currentTime) {
            const elapsed = currentTime - start;
            const progress = Math.min(elapsed / duration, 1);
            
            element.style.height = (targetHeight * progress) + 'px';
            
            if (progress >= 1) {
                element.style.height = '';
                element.style.overflow = '';
            } else {
                requestAnimationFrame(animate);
            }
        }
        
        requestAnimationFrame(animate);
    }
}

/**
 * Storage Utilities
 */
class StorageUtils {
    /**
     * Get item from localStorage with JSON parsing
     * @param {string} key - Storage key
     * @param {*} defaultValue - Default value if key doesn't exist
     * @returns {*} Stored value or default
     */
    static getItem(key, defaultValue = null) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (error) {
            console.warn(`Error reading from localStorage key '${key}':`, error);
            return defaultValue;
        }
    }

    /**
     * Set item in localStorage with JSON stringification
     * @param {string} key - Storage key
     * @param {*} value - Value to store
     */
    static setItem(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
        } catch (error) {
            console.warn(`Error writing to localStorage key '${key}':`, error);
        }
    }

    /**
     * Remove item from localStorage
     * @param {string} key - Storage key
     */
    static removeItem(key) {
        try {
            localStorage.removeItem(key);
        } catch (error) {
            console.warn(`Error removing localStorage key '${key}':`, error);
        }
    }
}

/**
 * Debounce function calls
 * @param {Function} func - Function to debounce
 * @param {number} wait - Wait time in ms
 * @param {boolean} immediate - Execute immediately
 * @returns {Function} Debounced function
 */
function debounce(func, wait, immediate = false) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            timeout = null;
            if (!immediate) func(...args);
        };
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func(...args);
    };
}

/**
 * Throttle function calls
 * @param {Function} func - Function to throttle
 * @param {number} limit - Time limit in ms
 * @returns {Function} Throttled function
 */
function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

/**
 * Format time duration
 * @param {number} seconds - Duration in seconds
 * @returns {string} Formatted duration
 */
function formatDuration(seconds) {
    if (!seconds || seconds < 0) return '0s';
    
    const units = [
        { name: 'd', value: 86400 },
        { name: 'h', value: 3600 },
        { name: 'm', value: 60 },
        { name: 's', value: 1 }
    ];
    
    const parts = [];
    let remaining = Math.floor(seconds);
    
    for (const unit of units) {
        if (remaining >= unit.value) {
            const count = Math.floor(remaining / unit.value);
            parts.push(`${count}${unit.name}`);
            remaining %= unit.value;
        }
    }
    
    return parts.length > 0 ? parts.slice(0, 2).join(' ') : '0s';
}

/**
 * Escape HTML to prevent XSS
 * @param {string} text - Text to escape
 * @returns {string} Escaped text
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Generate unique ID
 * @returns {string} Unique ID
 */
function generateId() {
    return 'id_' + Math.random().toString(36).substr(2, 9);
}

/**
 * Copy text to clipboard
 * @param {string} text - Text to copy
 * @returns {Promise<boolean>} Success status
 */
async function copyToClipboard(text) {
    try {
        if (navigator.clipboard && window.isSecureContext) {
            await navigator.clipboard.writeText(text);
            return true;
        } else {
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = text;
            textArea.style.position = 'fixed';
            textArea.style.left = '-999999px';
            textArea.style.top = '-999999px';
            document.body.appendChild(textArea);
            textArea.focus();
            textArea.select();
            const success = document.execCommand('copy');
            textArea.remove();
            return success;
        }
    } catch (error) {
        console.error('Failed to copy text:', error);
        return false;
    }
}

// Export utilities to global scope
window.DOMUtils = DOMUtils;
window.AnimationUtils = AnimationUtils;
window.StorageUtils = StorageUtils;
window.debounce = debounce;
window.throttle = throttle;
window.formatDuration = formatDuration;
window.escapeHtml = escapeHtml;
window.generateId = generateId;
window.copyToClipboard = copyToClipboard;
