/**
 * UI Components for Taskmaster Dashboard
 */

/**
 * Toast Notification Component
 */
class ToastNotification {
    constructor() {
        this.container = DOMUtils.getElementById('toastContainer');
        this.toasts = new Map();
    }

    /**
     * Show a toast notification
     * @param {string} title - Toast title
     * @param {string} message - Toast message
     * @param {string} type - Toast type (success, error, warning, info)
     * @param {number} duration - Auto-hide duration in ms (0 = no auto-hide)
     */
    show(title, message, type = 'info', duration = 5000) {
        const id = generateId();
        const toast = this.createToast(id, title, message, type);
        
        this.container.appendChild(toast);
        this.toasts.set(id, toast);
        
        // Trigger animation
        requestAnimationFrame(() => {
            toast.classList.add('show');
        });
        
        // Auto-hide if duration is set
        if (duration > 0) {
            setTimeout(() => {
                this.hide(id);
            }, duration);
        }
        
        return id;
    }

    /**
     * Hide a toast notification
     * @param {string} id - Toast ID
     */
    hide(id) {
        const toast = this.toasts.get(id);
        if (!toast) return;
        
        toast.classList.remove('show');
        
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
            this.toasts.delete(id);
        }, 300);
    }

    /**
     * Create toast element
     * @param {string} id - Toast ID
     * @param {string} title - Toast title
     * @param {string} message - Toast message
     * @param {string} type - Toast type
     * @returns {HTMLElement} Toast element
     */
    createToast(id, title, message, type) {
        const icons = {
            success: '✓',
            error: '✕',
            warning: '⚠',
            info: 'ⓘ'
        };

        return DOMUtils.createElement('div', {
            className: `toast ${type}`,
            dataset: { id }
        }, `
            <div class="toast-icon">${icons[type] || icons.info}</div>
            <div class="toast-content">
                <div class="toast-title">${escapeHtml(title)}</div>
                <div class="toast-message">${escapeHtml(message)}</div>
            </div>
            <button class="toast-close" onclick="window.toast.hide('${id}')">&times;</button>
        `);
    }

    /**
     * Clear all toasts
     */
    clear() {
        this.toasts.forEach((toast, id) => {
            this.hide(id);
        });
    }
}

/**
 * Modal Component
 */
class Modal {
    constructor(modalId) {
        this.modal = DOMUtils.getElementById(modalId);
        this.isOpen = false;
        
        if (this.modal) {
            this.setupEventListeners();
        }
    }

    /**
     * Setup modal event listeners
     */
    setupEventListeners() {
        // Close on overlay click
        DOMUtils.addEventListener(this.modal, 'click', (e) => {
            if (e.target === this.modal) {
                this.hide();
            }
        });

        // Close on escape key
        DOMUtils.addEventListener(document, 'keydown', (e) => {
            if (e.key === 'Escape' && this.isOpen) {
                this.hide();
            }
        });

        // Close buttons
        const closeButtons = this.modal.querySelectorAll('.modal-close');
        closeButtons.forEach(button => {
            DOMUtils.addEventListener(button, 'click', () => this.hide());
        });
    }

    /**
     * Show the modal
     */
    show() {
        if (!this.modal) return;
        
        this.modal.classList.add('show');
        this.isOpen = true;
        document.body.style.overflow = 'hidden';
        
        // Focus first focusable element
        const focusable = this.modal.querySelector('button, input, select, textarea, [tabindex]:not([tabindex="-1"])');
        if (focusable) {
            focusable.focus();
        }
    }

    /**
     * Hide the modal
     */
    hide() {
        if (!this.modal) return;
        
        this.modal.classList.remove('show');
        this.isOpen = false;
        document.body.style.overflow = '';
    }

    /**
     * Set modal content
     * @param {string} title - Modal title
     * @param {string} content - Modal content (HTML)
     */
    setContent(title, content) {
        if (!this.modal) return;
        
        const titleElement = this.modal.querySelector('.modal-title');
        const bodyElement = this.modal.querySelector('.modal-body');
        
        if (titleElement) {
            titleElement.textContent = title;
        }
        
        if (bodyElement) {
            bodyElement.innerHTML = content;
        }
    }
}

/**
 * Process Card Component
 */
class ProcessCard {
    constructor(processData) {
        this.data = processData;
        this.element = null;
        this.selected = false;
    }

    /**
     * Create the process card element
     * @returns {HTMLElement} Process card element
     */
    createElement() {
        const statusClass = APIResponseHandler.getStatusClass(this.data.status);
        const statusIcon = APIResponseHandler.getStatusIcon(this.data.status);
        const uptime = APIResponseHandler.formatUptime(this.data.uptime);

        this.element = DOMUtils.createElement('div', {
            className: `process-card status-${this.data.status}`,
            dataset: { processName: this.data.name }
        }, `
            <div class="process-header">
                <div class="process-select">
                    <input type="checkbox" id="select-${this.data.name}" 
                           onchange="window.dashboard.toggleProcessSelection('${this.data.name}', this.checked)">
                </div>
                <div class="process-info">
                    <div class="process-name">
                        ${escapeHtml(this.data.name)}
                    </div>
                    <div class="process-cmd">${escapeHtml(this.data.cmd)}</div>
                </div>
            </div>
            
            <div class="process-status">
                <div class="status-badge ${statusClass}">
                    <span class="status-icon">${statusIcon}</span>
                    ${this.data.status}
                </div>
                <div class="process-pid">
                    PID: ${this.data.pid || '-'}
                </div>
            </div>
            
            <div class="process-details">
                <div class="detail-item">
                    <div class="detail-label">Uptime</div>
                    <div class="detail-value">${uptime}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Restarts</div>
                    <div class="detail-value">${this.data.restarts}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Exit Code</div>
                    <div class="detail-value">${this.data.exitcode !== null ? this.data.exitcode : '-'}</div>
                </div>
            </div>
            
            <div class="process-actions">
                ${this.createActionButtons()}
            </div>
        `);

        return this.element;
    }

    /**
     * Create action buttons based on process status
     * @returns {string} Action buttons HTML
     */
    createActionButtons() {
        const canStart = ['stopped', 'exited', 'fatal', 'error'].includes(this.data.status);
        const canStop = ['running', 'starting'].includes(this.data.status);
        const canRestart = ['running', 'stopped', 'exited', 'fatal', 'error'].includes(this.data.status);

        return `
            <button class="action-btn start"
                    onclick="window.dashboard.startProcess('${this.data.name}')"
                    ${!canStart ? 'disabled' : ''}>
                <span>▶</span> Start
            </button>
            <button class="action-btn stop"
                    onclick="window.dashboard.stopProcess('${this.data.name}')"
                    ${!canStop ? 'disabled' : ''}>
                <span>⏹</span> Stop
            </button>
            <button class="action-btn restart"
                    onclick="window.dashboard.restartProcess('${this.data.name}')"
                    ${!canRestart ? 'disabled' : ''}>
                <span>↻</span> Restart
            </button>
            <button class="action-btn detail"
                    onclick="window.dashboard.showProcessDetail('${this.data.name}')">
                <span>ⓘ</span> Detail
            </button>
        `;
    }

    /**
     * Update the process card with new data
     * @param {Object} newData - Updated process data
     */
    update(newData) {
        this.data = { ...this.data, ...newData };
        
        if (this.element) {
            // Update status badge
            const statusBadge = this.element.querySelector('.status-badge');
            const statusClass = APIResponseHandler.getStatusClass(this.data.status);
            const statusIcon = APIResponseHandler.getStatusIcon(this.data.status);
            
            statusBadge.className = `status-badge ${statusClass}`;
            statusBadge.innerHTML = `
                <span class="status-icon">${statusIcon}</span>
                ${this.data.status}
            `;

            // Update card class
            this.element.className = `process-card status-${this.data.status}${this.selected ? ' selected' : ''}`;

            // Update PID
            const pidElement = this.element.querySelector('.process-pid');
            pidElement.textContent = `PID: ${this.data.pid || '-'}`;

            // Update details
            const detailValues = this.element.querySelectorAll('.detail-value');
            if (detailValues.length >= 3) {
                detailValues[0].textContent = APIResponseHandler.formatUptime(this.data.uptime);
                detailValues[1].textContent = this.data.restarts;
                detailValues[2].textContent = this.data.exitcode !== null ? this.data.exitcode : '-';
            }

            // Update action buttons
            const actionsContainer = this.element.querySelector('.process-actions');
            actionsContainer.innerHTML = this.createActionButtons();
        }
    }

    /**
     * Set selection state
     * @param {boolean} selected - Selection state
     */
    setSelected(selected) {
        this.selected = selected;
        
        if (this.element) {
            DOMUtils.toggleClass(this.element, 'selected', selected);
            
            const checkbox = this.element.querySelector('input[type="checkbox"]');
            if (checkbox) {
                checkbox.checked = selected;
            }
        }
    }

    /**
     * Get the process name
     * @returns {string} Process name
     */
    getName() {
        return this.data.name;
    }

    /**
     * Get the process data
     * @returns {Object} Process data
     */
    getData() {
        return this.data;
    }
}

/**
 * Loading Overlay Component
 */
class LoadingOverlay {
    constructor() {
        this.overlay = DOMUtils.getElementById('loadingOverlay');
        this.isVisible = false;
    }

    /**
     * Show the loading overlay
     * @param {string} message - Loading message
     */
    show(message = 'Loading...') {
        if (!this.overlay) return;
        
        const textElement = this.overlay.querySelector('.loading-text');
        if (textElement) {
            textElement.textContent = message;
        }
        
        this.overlay.classList.add('show');
        this.isVisible = true;
    }

    /**
     * Hide the loading overlay
     */
    hide() {
        if (!this.overlay) return;
        
        this.overlay.classList.remove('show');
        this.isVisible = false;
    }

    /**
     * Check if overlay is visible
     * @returns {boolean} Visibility state
     */
    isShowing() {
        return this.isVisible;
    }
}

// Export components to global scope
window.ToastNotification = ToastNotification;
window.Modal = Modal;
window.ProcessCard = ProcessCard;
window.LoadingOverlay = LoadingOverlay;

// Create global instances
window.toast = new ToastNotification();
window.loadingOverlay = new LoadingOverlay();
