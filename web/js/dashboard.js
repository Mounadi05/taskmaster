/**
 * Taskmaster Dashboard Main Application
 */

class TaskmasterDashboard {
    constructor() {
        this.processes = new Map();
        this.selectedProcesses = new Set();
        this.autoRefreshEnabled = true;
        this.autoRefreshInterval = null;
        this.refreshIntervalMs = 5000; // 5 seconds
        this.connectionStatus = 'disconnected';
        this.viewMode = 'grid'; // 'grid' or 'list'
        
        this.initializeElements();
        this.setupEventListeners();
        this.loadSettings();
        this.startApplication();
    }

    /**
     * Initialize DOM elements
     */
    initializeElements() {
        this.elements = {
            connectionStatus: DOMUtils.getElementById('connectionStatus'),
            statusIndicator: document.querySelector('.status-indicator'),
            statusText: document.querySelector('.status-text'),
            refreshBtn: DOMUtils.getElementById('refreshBtn'),
            autoRefreshToggle: DOMUtils.getElementById('autoRefreshToggle'),
            logoutBtn: DOMUtils.getElementById('logoutBtn'),
            // Add a container wrapper for process cards
            processesContainer: DOMUtils.getElementById('processesContainer'),
            processesGrid: document.querySelector('.process-grid'),
            
            // Summary cards
            runningCount: DOMUtils.getElementById('runningCount'),
            stoppedCount: DOMUtils.getElementById('stoppedCount'),
            errorCount: DOMUtils.getElementById('errorCount'),
            totalCount: DOMUtils.getElementById('totalCount'),
            
            // Bulk controls
            selectAllBtn: DOMUtils.getElementById('selectAllBtn'),
            deselectAllBtn: DOMUtils.getElementById('deselectAllBtn'),
            bulkStartBtn: DOMUtils.getElementById('bulkStartBtn'),
            bulkStopBtn: DOMUtils.getElementById('bulkStopBtn'),
            bulkRestartBtn: DOMUtils.getElementById('bulkRestartBtn'),
            
            // View controls
            gridViewBtn: DOMUtils.getElementById('gridViewBtn'),
            listViewBtn: DOMUtils.getElementById('listViewBtn'),
            
            // Modals
            errorModal: new Modal('errorModal'),
            detailModal: new Modal('detailModal')
        };
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Refresh button
        DOMUtils.addEventListener(this.elements.refreshBtn, 'click', () => {
            this.refreshProcesses();
        });

        // Auto-refresh toggle
        DOMUtils.addEventListener(this.elements.autoRefreshToggle, 'change', (e) => {
            this.setAutoRefresh(e.target.checked);
        });

        // Logout button
        DOMUtils.addEventListener(this.elements.logoutBtn, 'click', () => {
            this.logout();
        });

        // Bulk selection controls
        DOMUtils.addEventListener(this.elements.selectAllBtn, 'click', () => {
            this.selectAllProcesses();
        });

        DOMUtils.addEventListener(this.elements.deselectAllBtn, 'click', () => {
            this.deselectAllProcesses();
        });

        // Bulk action buttons
        DOMUtils.addEventListener(this.elements.bulkStartBtn, 'click', () => {
            this.performBulkAction('start');
        });

        DOMUtils.addEventListener(this.elements.bulkStopBtn, 'click', () => {
            this.performBulkAction('stop');
        });

        DOMUtils.addEventListener(this.elements.bulkRestartBtn, 'click', () => {
            this.performBulkAction('restart');
        });

        // View mode buttons
        DOMUtils.addEventListener(this.elements.gridViewBtn, 'click', () => {
            this.setViewMode('grid');
        });

        DOMUtils.addEventListener(this.elements.listViewBtn, 'click', () => {
            this.setViewMode('list');
        });

        // Keyboard shortcuts
        DOMUtils.addEventListener(document, 'keydown', (e) => {
            this.handleKeyboardShortcuts(e);
        });
    }

    /**
     * Load settings from localStorage
     */
    loadSettings() {
        this.autoRefreshEnabled = StorageUtils.getItem('autoRefresh', true);
        this.viewMode = StorageUtils.getItem('viewMode', 'grid');
        
        // Apply settings
        this.elements.autoRefreshToggle.checked = this.autoRefreshEnabled;
        this.setViewMode(this.viewMode);
    }

    /**
     * Save settings to localStorage
     */
    saveSettings() {
        StorageUtils.setItem('autoRefresh', this.autoRefreshEnabled);
        StorageUtils.setItem('viewMode', this.viewMode);
    }

    /**
     * Start the application
     */
    async startApplication() {
        this.updateConnectionStatus('connecting');

        try {
            await this.checkServerConnection();
            await this.checkAuthenticationStatus();
            await this.refreshProcesses();
            this.startAutoRefresh();
        } catch (error) {
            this.handleError('Failed to start application', error);
        }
    }

    /**
     * Check if authentication is enabled and show logout button if needed
     */
    async checkAuthenticationStatus() {
        // Check if we have a session cookie
        const hasSession = document.cookie.includes('taskmaster_session=');

        if (hasSession && this.elements.logoutBtn) {
            this.elements.logoutBtn.style.display = 'flex';
        }
    }

    /**
     * Logout user
     */
    async logout() {
        try {
            // Call logout endpoint
            const response = await fetch('/logout', {
                method: 'GET',
                credentials: 'same-origin'
            });

            if (response.redirected) {
                // Server redirected us to login page
                window.location.href = response.url;
            } else {
                // Fallback: redirect to login manually
                window.location.href = '/login';
            }
        } catch (error) {
            console.error('Logout error:', error);
            // Fallback: redirect to login
            window.location.href = '/login';
        }
    }

    /**
     * Check server connection
     */
    async checkServerConnection() {
        try {
            const response = await taskmasterAPI.checkAlive();
            if (APIResponseHandler.isSuccess(response)) {
                this.updateConnectionStatus('connected');
                return true;
            } else {
                throw new Error('Server not responding correctly');
            }
        } catch (error) {
            this.updateConnectionStatus('disconnected');
            throw error;
        }
    }

    /**
     * Update connection status
     * @param {string} status - Connection status (connected, connecting, disconnected)
     */
    updateConnectionStatus(status) {
        this.connectionStatus = status;
        
        if (this.elements.statusIndicator) {
            this.elements.statusIndicator.className = `status-indicator ${status}`;
        }
        
        if (this.elements.statusText) {
            const statusTexts = {
                connected: 'Connected',
                connecting: 'Connecting...',
                disconnected: 'Disconnected'
            };
            this.elements.statusText.textContent = statusTexts[status] || 'Unknown';
        }
    }

    /**
     * Set auto-refresh state
     * @param {boolean} enabled - Whether auto-refresh is enabled
     */
    setAutoRefresh(enabled) {
        this.autoRefreshEnabled = enabled;
        this.saveSettings();
        
        if (enabled) {
            this.startAutoRefresh();
        } else {
            this.stopAutoRefresh();
        }
    }

    /**
     * Start auto-refresh interval
     */
    startAutoRefresh() {
        this.stopAutoRefresh();
        
        if (this.autoRefreshEnabled) {
            this.autoRefreshInterval = setInterval(() => {
                this.refreshProcesses();
            }, this.refreshIntervalMs);
        }
    }

    /**
     * Stop auto-refresh interval
     */
    stopAutoRefresh() {
        if (this.autoRefreshInterval) {
            clearInterval(this.autoRefreshInterval);
            this.autoRefreshInterval = null;
        }
    }

    /**
     * Refresh processes data
     */
    async refreshProcesses() {
        try {
            loadingOverlay.show('Refreshing processes...');
            
            const response = await taskmasterAPI.getStatus();
            
            if (APIResponseHandler.isSuccess(response)) {
                const processesData = APIResponseHandler.normalizeProcessData(response.data);
                this.updateProcesses(processesData);
                this.updateSummaryCards();
                this.updateConnectionStatus('connected');
            } else {
                throw new Error(APIResponseHandler.getErrorMessage(response));
            }
        } catch (error) {
            this.updateConnectionStatus('disconnected');
            this.handleError('Failed to refresh processes', error);
        } finally {
            loadingOverlay.hide();
        }
    }

    /**
     * Update processes data and UI
     * @param {Object} processesData - Processes data from API
     */
    updateProcesses(processesData) {
        if (!processesData) {
            this.showEmptyState();
            return;
        }

        // Update existing processes and add new ones
        const currentProcessNames = new Set();
        
        Object.entries(processesData).forEach(([name, data]) => {
            currentProcessNames.add(name);
            
            if (this.processes.has(name)) {
                // Update existing process
                const processCard = this.processes.get(name);
                processCard.update(data);
            } else {
                // Add new process
                const processCard = new ProcessCard(data);
                this.processes.set(name, processCard);
                this.renderProcessCard(processCard);
            }
        });

        // Remove processes that no longer exist
        this.processes.forEach((processCard, name) => {
            if (!currentProcessNames.has(name)) {
                this.removeProcessCard(name);
            }
        });

        // Update bulk controls
        this.updateBulkControls();
    }

    /**
     * Render a process card
     * @param {ProcessCard} processCard - Process card to render
     */
    renderProcessCard(processCard) {
        if (!this.elements.processesContainer) return;
        
        // Add to container
        const element = processCard.getElement();
        
        // Add animation delay based on number of cards
        const index = this.processes.size - 1;
        const delay = 0.1 * (index % 10); // Limit to 10 different delays
        element.style.animationDelay = `${0.5 + delay}s`; // Start after summary cards
        
        this.elements.processesContainer.appendChild(element);
        
        // If this is the first card, hide empty state
        if (this.processes.size === 1) {
            const emptyState = this.elements.processesContainer.querySelector('.empty-state');
            if (emptyState) {
                emptyState.style.display = 'none';
            }
        }
    }

    /**
     * Remove a process card
     * @param {string} processName - Name of process to remove
     */
    removeProcessCard(processName) {
        const processCard = this.processes.get(processName);
        
        if (processCard) {
            // Remove from DOM
            const element = processCard.getElement();
            if (element && element.parentNode) {
                element.parentNode.removeChild(element);
            }
            
            // Remove from selected processes
            this.selectedProcesses.delete(processName);
            
            // Remove from processes map
            this.processes.delete(processName);
            
            // If no processes left, show empty state
            if (this.processes.size === 0) {
                this.showEmptyState();
            }
            
            // Update bulk controls
            this.updateBulkControls();
        }
    }

    /**
     * Show empty state when no processes
     */
    showEmptyState() {
        if (!this.elements.processesContainer) return;
        
        // Clear container
        DOMUtils.clearElement(this.elements.processesContainer);
        
        // Add empty state
        const emptyState = document.createElement('div');
        emptyState.className = 'empty-state';
        emptyState.innerHTML = `
            <div class="empty-icon"><i class="icon-empty"></i></div>
            <h3>No Processes Found</h3>
            <p>There are no configured processes available.</p>
        `;
        
        this.elements.processesContainer.appendChild(emptyState);
    }

    /**
     * Update summary cards
     */
    updateSummaryCards() {
        const counts = {
            running: 0,
            stopped: 0,
            error: 0,
            total: 0
        };

        this.processes.forEach(processCard => {
            const status = processCard.getData().status;
            counts.total++;
            
            if (status === 'running') {
                counts.running++;
            } else if (['stopped', 'exited'].includes(status)) {
                counts.stopped++;
            } else if (['error', 'fatal'].includes(status)) {
                counts.error++;
            }
        });

        // Update UI
        if (this.elements.runningCount) this.elements.runningCount.textContent = counts.running;
        if (this.elements.stoppedCount) this.elements.stoppedCount.textContent = counts.stopped;
        if (this.elements.errorCount) this.elements.errorCount.textContent = counts.error;
        if (this.elements.totalCount) this.elements.totalCount.textContent = counts.total;

        // Add subtle pulse animation on summary cards when counts update
        ['runningCount','stoppedCount','errorCount','totalCount'].forEach(id => {
            const el = this.elements[id];
            if (el) {
                el.classList.add('action-success');
                setTimeout(() => el.classList.remove('action-success'), 600);
            }
        });
    }

    /**
     * Set view mode
     * @param {string} mode - View mode ('grid' or 'list')
     */
    setViewMode(mode) {
        this.viewMode = mode;
        this.saveSettings();
        
        // Update UI
        DOMUtils.toggleClass(this.elements.gridViewBtn, 'active', mode === 'grid');
        DOMUtils.toggleClass(this.elements.listViewBtn, 'active', mode === 'list');
        DOMUtils.toggleClass(this.elements.processesContainer, 'list-view', mode === 'list');
    }

    /**
     * Toggle process selection
     * @param {string} processName - Process name
     * @param {boolean} selected - Selection state
     */
    toggleProcessSelection(processName, selected) {
        if (selected) {
            this.selectedProcesses.add(processName);
        } else {
            this.selectedProcesses.delete(processName);
        }
        
        const processCard = this.processes.get(processName);
        if (processCard) {
            processCard.setSelected(selected);
        }
        
        this.updateBulkControls();
    }

    /**
     * Select all processes
     */
    selectAllProcesses() {
        this.processes.forEach((processCard, name) => {
            this.selectedProcesses.add(name);
            processCard.setSelected(true);
        });
        this.updateBulkControls();
    }

    /**
     * Deselect all processes
     */
    deselectAllProcesses() {
        this.selectedProcesses.clear();
        this.processes.forEach(processCard => {
            processCard.setSelected(false);
        });
        this.updateBulkControls();
    }

    /**
     * Update bulk control buttons state
     */
    updateBulkControls() {
        const hasSelection = this.selectedProcesses.size > 0;
        
        if (this.elements.bulkStartBtn) {
            this.elements.bulkStartBtn.disabled = !hasSelection;
        }
        if (this.elements.bulkStopBtn) {
            this.elements.bulkStopBtn.disabled = !hasSelection;
        }
        if (this.elements.bulkRestartBtn) {
            this.elements.bulkRestartBtn.disabled = !hasSelection;
        }
    }

    /**
     * Handle keyboard shortcuts
     * @param {KeyboardEvent} e - Keyboard event
     */
    handleKeyboardShortcuts(e) {
        // Ctrl/Cmd + R: Refresh
        if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
            e.preventDefault();
            this.refreshProcesses();
        }
        
        // Ctrl/Cmd + A: Select all
        if ((e.ctrlKey || e.metaKey) && e.key === 'a') {
            e.preventDefault();
            this.selectAllProcesses();
        }
        
        // Escape: Deselect all
        if (e.key === 'Escape') {
            this.deselectAllProcesses();
        }
    }

    /**
     * Start a process
     * @param {string} processName - Process name
     */
    async startProcess(processName) {
        try {
            const response = await taskmasterAPI.startProcess(processName);

            if (APIResponseHandler.isSuccess(response)) {
                toast.show('Process Started', `${processName} started successfully`, 'success');
                await this.refreshProcesses();
            } else {
                throw new Error(APIResponseHandler.getErrorMessage(response));
            }
        } catch (error) {
            this.handleError(`Failed to start ${processName}`, error);
        }
    }

    /**
     * Stop a process
     * @param {string} processName - Process name
     */
    async stopProcess(processName) {
        try {
            const response = await taskmasterAPI.stopProcess(processName);

            if (APIResponseHandler.isSuccess(response)) {
                toast.show('Process Stopped', `${processName} stopped successfully`, 'success');
                await this.refreshProcesses();
            } else {
                throw new Error(APIResponseHandler.getErrorMessage(response));
            }
        } catch (error) {
            this.handleError(`Failed to stop ${processName}`, error);
        }
    }

    /**
     * Restart a process
     * @param {string} processName - Process name
     */
    async restartProcess(processName) {
        try {
            const response = await taskmasterAPI.restartProcess(processName);

            if (APIResponseHandler.isSuccess(response)) {
                toast.show('Process Restarted', `${processName} restarted successfully`, 'success');
                await this.refreshProcesses();
            } else {
                throw new Error(APIResponseHandler.getErrorMessage(response));
            }
        } catch (error) {
            this.handleError(`Failed to restart ${processName}`, error);
        }
    }

    /**
     * Show process detail modal
     * @param {string} processName - Process name
     */
    async showProcessDetail(processName) {
        try {
            const response = await taskmasterAPI.getProcessDetail(processName);

            if (APIResponseHandler.isSuccess(response)) {
                const processData = response.data[processName];
                this.renderProcessDetail(processName, processData);
                this.elements.detailModal.show();
            } else {
                throw new Error(APIResponseHandler.getErrorMessage(response));
            }
        } catch (error) {
            this.handleError(`Failed to get details for ${processName}`, error);
        }
    }

    /**
     * Render process detail content
     * @param {string} processName - Process name
     * @param {Object} processData - Process data
     */
    renderProcessDetail(processName, processData) {
        const config = processData.config || {};
        const statusIcon = APIResponseHandler.getStatusIcon(processData.status);

        const content = `
            <div class="process-detail">
                <div class="detail-header">
                    <h4>${escapeHtml(processName)} ${statusIcon}</h4>
                    <div class="detail-status">
                        <span class="status-badge ${APIResponseHandler.getStatusClass(processData.status)}">
                            ${processData.status}
                        </span>
                    </div>
                </div>

                <div class="detail-sections">
                    <div class="detail-section">
                        <h5>Process Information</h5>
                        <div class="detail-grid">
                            <div class="detail-row">
                                <span class="detail-label">Command:</span>
                                <span class="detail-value">${escapeHtml(processData.cmd)}</span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">PID:</span>
                                <span class="detail-value">${processData.pid || '-'}</span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">Uptime:</span>
                                <span class="detail-value">${APIResponseHandler.formatUptime(processData.uptime)}</span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">Restarts:</span>
                                <span class="detail-value">${processData.restarts}</span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">Exit Code:</span>
                                <span class="detail-value">${processData.exitcode !== null ? processData.exitcode : '-'}</span>
                            </div>
                        </div>
                    </div>

                    <div class="detail-section">
                        <h5>Configuration</h5>
                        <div class="detail-grid">
                            <div class="detail-row">
                                <span class="detail-label">Auto Start:</span>
                                <span class="detail-value">${config.autostart ? 'Yes' : 'No'}</span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">Auto Restart:</span>
                                <span class="detail-value">${config.autorestart || 'No'}</span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">Start Retries:</span>
                                <span class="detail-value">${config.startretries || 0}</span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">Start Seconds:</span>
                                <span class="detail-value">${config.startsecs || 1}s</span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">Stop Signal:</span>
                                <span class="detail-value">${config.stopsignal || 'TERM'}</span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">Stop Timeout:</span>
                                <span class="detail-value">${config.stoptsecs || 10}s</span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">Working Directory:</span>
                                <span class="detail-value">${config.workingdir || '-'}</span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">Number of Processes:</span>
                                <span class="detail-value">${config.numprocs || 1}</span>
                            </div>
                        </div>
                    </div>

                    ${config.user || config.group || config.umask || config.priority ? `
                    <div class="detail-section">
                        <h5>Process Control</h5>
                        <div class="detail-grid">
                            ${config.user ? `
                            <div class="detail-row">
                                <span class="detail-label">User:</span>
                                <span class="detail-value">${config.user}</span>
                            </div>
                            ` : ''}
                            ${config.group ? `
                            <div class="detail-row">
                                <span class="detail-label">Group:</span>
                                <span class="detail-value">${config.group}</span>
                            </div>
                            ` : ''}
                            ${config.umask ? `
                            <div class="detail-row">
                                <span class="detail-label">Umask:</span>
                                <span class="detail-value">${config.umask}</span>
                            </div>
                            ` : ''}
                            ${config.priority ? `
                            <div class="detail-row">
                                <span class="detail-label">Priority:</span>
                                <span class="detail-value">${config.priority}</span>
                            </div>
                            ` : ''}
                        </div>
                    </div>
                    ` : ''}

                    ${processData.stdout || processData.stderr ? `
                    <div class="detail-section">
                        <h5>Logging</h5>
                        <div class="detail-grid">
                            ${processData.stdout ? `
                            <div class="detail-row">
                                <span class="detail-label">Stdout:</span>
                                <span class="detail-value">${typeof processData.stdout === 'object' ? 
                                    (processData.stdout.path + (processData.stdout.maxbytes ? ` (max ${processData.stdout.maxbytes} bytes)` : '')) : 
                                    processData.stdout}</span>
                            </div>
                            ` : ''}
                            ${processData.stderr ? `
                            <div class="detail-row">
                                <span class="detail-label">Stderr:</span>
                                <span class="detail-value">${typeof processData.stderr === 'object' ? 
                                    (processData.stderr.path + (processData.stderr.maxbytes ? ` (max ${processData.stderr.maxbytes} bytes)` : '')) : 
                                    processData.stderr}</span>
                            </div>
                            ` : ''}
                        </div>
                    </div>
                    ` : ''}

                    ${processData.env && Object.keys(processData.env).length > 0 ? `
                    <div class="detail-section">
                        <h5>Environment Variables</h5>
                        <div class="detail-grid">
                            ${Object.entries(processData.env).map(([key, value]) => `
                            <div class="detail-row">
                                <span class="detail-label">${escapeHtml(key)}:</span>
                                <span class="detail-value">${escapeHtml(value)}</span>
                            </div>
                            `).join('')}
                        </div>
                    </div>
                    ` : ''}

                    <div class="detail-section">
                        <h5>Actions</h5>
                        <div class="detail-actions">
                            <button class="btn btn-success action-start" ${processData.status === 'running' ? 'disabled' : ''}>
                                <i class="material-icons">play_arrow</i> Start
                            </button>
                            <button class="btn btn-danger action-stop" ${processData.status !== 'running' ? 'disabled' : ''}>
                                <i class="material-icons">stop</i> Stop
                            </button>
                            <button class="btn btn-warning action-restart">
                                <i class="material-icons">refresh</i> Restart
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        this.elements.detailModal.setContent(content);
        
        // Add event listeners to action buttons
        const detailModalBody = document.getElementById('detailModalBody');
        
        if (detailModalBody) {
            const startBtn = detailModalBody.querySelector('.action-start');
            if (startBtn) {
                startBtn.addEventListener('click', () => {
                    this.elements.detailModal.hide();
                    this.startProcess(processName);
                });
            }
            
            const stopBtn = detailModalBody.querySelector('.action-stop');
            if (stopBtn) {
                stopBtn.addEventListener('click', () => {
                    this.elements.detailModal.hide();
                    this.stopProcess(processName);
                });
            }
            
            const restartBtn = detailModalBody.querySelector('.action-restart');
            if (restartBtn) {
                restartBtn.addEventListener('click', () => {
                    this.elements.detailModal.hide();
                    this.restartProcess(processName);
                });
            }
        }
    }

    /**
     * Perform bulk action on selected processes
     * @param {string} action - Action to perform (start, stop, restart)
     */
    async performBulkAction(action) {
        if (this.selectedProcesses.size === 0) {
            toast.show('No Selection', 'Please select processes first', 'warning');
            return;
        }

        const processNames = Array.from(this.selectedProcesses);
        const actionText = action.charAt(0).toUpperCase() + action.slice(1);

        try {
            loadingOverlay.show(`${actionText}ing ${processNames.length} process(es)...`);

            const results = await taskmasterAPI.bulkOperation(action, processNames);

            let successCount = 0;
            let errorCount = 0;

            results.forEach(result => {
                if (result.success) {
                    successCount++;
                } else {
                    errorCount++;
                    console.error(`Failed to ${action} ${result.processName}:`, result.error);
                }
            });

            if (successCount > 0) {
                toast.show(
                    `Bulk ${actionText}`,
                    `${successCount} process(es) ${action}ed successfully`,
                    'success'
                );
            }

            if (errorCount > 0) {
                toast.show(
                    `Bulk ${actionText} Errors`,
                    `${errorCount} process(es) failed to ${action}`,
                    'error'
                );
            }

            await this.refreshProcesses();

        } catch (error) {
            this.handleError(`Bulk ${action} failed`, error);
        } finally {
            loadingOverlay.hide();
        }
    }

    /**
     * Handle errors
     * @param {string} title - Error title
     * @param {Error} error - Error object
     */
    handleError(title, error) {
        console.error(title, error);
        
        // Show error in modal for serious errors
        if (this.elements.errorModal) {
            this.elements.errorModal.setTitle(title);
            const errorMessage = document.getElementById('errorModalMessage');
            if (errorMessage) {
                errorMessage.textContent = error.message || 'An unknown error occurred';
            }
            this.elements.errorModal.show();
        } else {
            // Fallback to toast
            toast.show(title, error.message || 'An unknown error occurred', 'error');
        }
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new TaskmasterDashboard();
});

// Add some additional CSS for the detail modal
const additionalCSS = `
<style>
.process-detail {
    font-family: inherit;
}

.detail-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.5rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid #e2e8f0;
}

.detail-header h4 {
    margin: 0;
    font-size: 1.25rem;
    color: #2d3748;
}

.detail-sections {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
}

.detail-section h5 {
    margin: 0 0 1rem 0;
    font-size: 1rem;
    color: #4a5568;
    font-weight: 600;
}

.detail-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 1rem;
}

.detail-row {
    display: flex;
    flex-direction: column;
}

.detail-label {
    font-weight: 500;
    color: #718096;
    margin-bottom: 0.25rem;
}

.detail-value {
    color: #2d3748;
    word-break: break-word;
}

.detail-actions {
    display: flex;
    gap: 0.5rem;
}

@media (prefers-color-scheme: dark) {
    .detail-header {
        border-bottom-color: #2d3748;
    }
    
    .detail-header h4 {
        color: #e2e8f0;
    }
    
    .detail-section h5 {
        color: #a0aec0;
    }
    
    .detail-label {
        color: #a0aec0;
    }
    
    .detail-value {
        color: #e2e8f0;
    }
}
</style>
`;

document.head.insertAdjacentHTML('beforeend', additionalCSS);
