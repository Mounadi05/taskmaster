/**
 * UI Components for Taskmaster Dashboard
 */

/**
 * Toast Notification Component
 */
class ToastNotification {
    constructor() {
        this.container = document.getElementById('toastContainer');
        this.toasts = new Map();
        this.counter = 0;
    }

    /**
     * Show a toast notification
     * @param {string} title - Toast title
     * @param {string} message - Toast message
     * @param {string} type - Toast type (success, error, warning, info)
     * @param {number} duration - Duration in ms (0 for no auto-hide)
     */
    show(title, message, type = 'info', duration = 5000) {
        const id = `toast-${++this.counter}`;
        
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.id = id;
        
        let iconName = 'info';
        if (type === 'success') iconName = 'check_circle';
        if (type === 'error') iconName = 'error';
        if (type === 'warning') iconName = 'warning';
        
        toast.innerHTML = `
            <div class="toast-icon"><i class="material-icons">${iconName}</i></div>
            <div class="toast-content">
                <div class="toast-title">${escapeHtml(title)}</div>
                <div class="toast-message">${escapeHtml(message)}</div>
            </div>
            <button class="toast-close"><i class="material-icons">close</i></button>
        `;
        
        toast.querySelector('.toast-close').addEventListener('click', () => {
            this.hide(id);
        });
        
        this.container.appendChild(toast);
        this.toasts.set(id, { element: toast, timer: null });
        
        // Force reflow to ensure animation works
        toast.offsetHeight;
        
        // Show toast with animation
        toast.classList.add('show');
        
        // Set auto-hide timer if duration > 0
        if (duration > 0) {
            const timer = setTimeout(() => {
                this.hide(id);
            }, duration);
            
            this.toasts.get(id).timer = timer;
        }
        
        return id;
    }

    /**
     * Hide a toast notification
     * @param {string} id - Toast ID
     */
    hide(id) {
        const toast = this.toasts.get(id);
        
        if (toast) {
            // Clear timer if exists
            if (toast.timer) {
                clearTimeout(toast.timer);
            }
            
            // Remove show class to trigger animation
            toast.element.classList.remove('show');
            
            // Remove element after animation
            setTimeout(() => {
                if (toast.element.parentNode) {
                    toast.element.parentNode.removeChild(toast.element);
                }
                this.toasts.delete(id);
            }, 300);
        }
    }

    /**
     * Hide all toast notifications
     */
    hideAll() {
        this.toasts.forEach((toast, id) => {
            this.hide(id);
        });
    }
}

/**
 * Modal Component
 */
class Modal {
    constructor(id) {
        this.id = id;
        this.element = document.getElementById(id);
        this.closeButtons = this.element ? this.element.querySelectorAll('[id^="' + id + 'Close"]') : [];
        
        this.closeButtons.forEach(button => {
            button.addEventListener('click', () => this.hide());
        });
        
        // Close on click outside modal content
        if (this.element) {
            this.element.addEventListener('click', event => {
                if (event.target === this.element) {
                    this.hide();
                }
            });
        }
    }

    /**
     * Show the modal
     */
    show() {
        if (this.element) {
            this.element.classList.add('open');
        }
    }

    /**
     * Hide the modal
     */
    hide() {
        if (this.element) {
            this.element.classList.remove('open');
        }
    }

    /**
     * Set modal content
     * @param {string} content - HTML content
     */
    setContent(content) {
        const body = this.element ? this.element.querySelector('.modal-body') : null;
        if (body) {
            body.innerHTML = content;
        }
    }

    /**
     * Set modal title
     * @param {string} title - Modal title
     */
    setTitle(title) {
        const titleElement = this.element ? this.element.querySelector('.modal-header h4') : null;
        if (titleElement) {
            titleElement.textContent = title;
        }
    }
}

/**
 * Process Card Component
 */
class ProcessCard {
    constructor(data) {
        this.data = data;
        this.element = null;
        this.selected = false;
        this.render();
        this.attachEventListeners();
    }

    /**
     * Render process card
     */
    render() {
        const statusClass = APIResponseHandler.getStatusClass(this.data.status);
        const uptime = APIResponseHandler.formatUptime(this.data.uptime);
        
        this.element = document.createElement('div');
        this.element.className = 'process-card';
        this.element.classList.add(statusClass);
        this.element.dataset.name = this.data.name;
        
        this.element.innerHTML = `
            <div class="card-header">
                <div class="card-title">
                    <h3>${escapeHtml(this.data.name)}</h3>
                </div>
                <span class="process-status ${statusClass}">
                    <i class="material-icons">${statusClass === 'running' ? 'play_arrow' : statusClass === 'stopped' ? 'stop' : 'error'}</i>
                    ${escapeHtml(this.data.status)}
                </span>
            </div>
            <div class="card-body">
                <div class="info-row">
                    <div class="label">PID</div>
                    <div class="value">${this.data.pid || '-'}</div>
                </div>
                <div class="info-row">
                    <div class="label">Uptime</div>
                    <div class="value">${uptime}</div>
                </div>
                <div class="info-row">
                    <div class="label">Restarts</div>
                    <div class="value">${this.data.restarts}</div>
                </div>
                <div class="info-row">
                    <div class="label">Command</div>
                    <div class="value truncate" title="${escapeHtml(this.data.cmd)}">${escapeHtml(this.data.cmd)}</div>
                </div>
            </div>
            <div class="card-footer">
                <div class="card-actions">
                    <button class="btn btn-sm btn-icon action-detail" title="View Details">
                        <i class="material-icons">info</i>
                    </button>
                    <button class="btn btn-sm btn-icon btn-success action-start" title="Start Process"${this.data.status === 'running' ? ' disabled' : ''}>
                        <i class="material-icons">play_arrow</i>
                    </button>
                    <button class="btn btn-sm btn-icon btn-danger action-stop" title="Stop Process"${this.data.status !== 'running' ? ' disabled' : ''}>
                        <i class="material-icons">stop</i>
                    </button>
                    <button class="btn btn-sm btn-icon btn-warning action-restart" title="Restart Process">
                        <i class="material-icons">refresh</i>
                    </button>
                </div>
                <label class="card-checkbox">
                    <input type="checkbox" ${this.selected ? 'checked' : ''}>
                </label>
            </div>
        `;
    }

    /**
     * Attach event listeners
     */
    attachEventListeners() {
        if (!this.element) return;
        
        // Process selection
        const checkbox = this.element.querySelector('input[type="checkbox"]');
        if (checkbox) {
            checkbox.addEventListener('change', () => {
                this.selected = checkbox.checked;
                window.dashboard.toggleProcessSelection(this.data.name, this.selected);
            });
        }
        
        // Action buttons
        this.element.querySelector('.action-detail').addEventListener('click', () => {
            window.dashboard.showProcessDetail(this.data.name);
        });
        
        this.element.querySelector('.action-start').addEventListener('click', () => {
            window.dashboard.startProcess(this.data.name);
        });
        
        this.element.querySelector('.action-stop').addEventListener('click', () => {
            window.dashboard.stopProcess(this.data.name);
        });
        
        this.element.querySelector('.action-restart').addEventListener('click', () => {
            window.dashboard.restartProcess(this.data.name);
        });
    }

    /**
     * Update process data
     * @param {Object} data - New process data
     */
    update(data) {
        this.data = data;
        
        // Update status badge
        const statusBadge = this.element.querySelector('.status-badge');
        if (statusBadge) {
            statusBadge.className = `status-badge ${APIResponseHandler.getStatusClass(data.status)}`;
            statusBadge.textContent = data.status;
        }
        
        // Update PID
        const pidElement = this.element.querySelector('.info-row:nth-child(1) div:last-child');
        if (pidElement) {
            pidElement.textContent = data.pid || '-';
        }
        
        // Update uptime
        const uptimeElement = this.element.querySelector('.info-row:nth-child(2) div:last-child');
        if (uptimeElement) {
            uptimeElement.textContent = APIResponseHandler.formatUptime(data.uptime);
        }
        
        // Update restarts
        const restartsElement = this.element.querySelector('.info-row:nth-child(3) div:last-child');
        if (restartsElement) {
            restartsElement.textContent = data.restarts;
        }
        
        // Update command if changed
        const cmdElement = this.element.querySelector('.info-row:nth-child(4) div:last-child');
        if (cmdElement && cmdElement.title !== data.cmd) {
            cmdElement.title = escapeHtml(data.cmd);
            cmdElement.textContent = escapeHtml(data.cmd);
        }
        
        // Update button states based on status
        const startButton = this.element.querySelector('.action-start');
        if (startButton) {
            startButton.disabled = data.status === 'running';
        }
        
        const stopButton = this.element.querySelector('.action-stop');
        if (stopButton) {
            stopButton.disabled = data.status !== 'running';
        }
    }

    /**
     * Set selected state
     * @param {boolean} selected - Selected state
     */
    setSelected(selected) {
        this.selected = selected;
        
        // Update checkbox
        const checkbox = this.element.querySelector('input[type="checkbox"]');
        if (checkbox) {
            checkbox.checked = selected;
        }
        
        // Update card class
        if (selected) {
            this.element.classList.add('selected');
        } else {
            this.element.classList.remove('selected');
        }
    }

    /**
     * Get process data
     * @returns {Object} Process data
     */
    getData() {
        return this.data;
    }

    /**
     * Get process element
     * @returns {HTMLElement} Process element
     */
    getElement() {
        return this.element;
    }
}

/**
 * Loading Overlay Component
 */
class LoadingOverlay {
    constructor() {
        this.element = document.createElement('div');
        this.element.className = 'loading-overlay';
        this.element.innerHTML = `
            <div class="loading-spinner"></div>
            <div class="loading-message">Loading...</div>
        `;
        
        document.body.appendChild(this.element);
    }

    /**
     * Show loading overlay
     * @param {string} message - Loading message
     */
    show(message = 'Loading...') {
        const messageElement = this.element.querySelector('.loading-message');
        if (messageElement) {
            messageElement.textContent = message;
        }
        
        this.element.classList.add('show');
    }

    /**
     * Hide loading overlay
     */
    hide() {
        this.element.classList.remove('show');
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
