/**
 * Taskmaster API Client
 * Handles communication with the Taskmaster HTTP API
 */

class TaskmasterAPI {
    constructor(baseUrl = '') {
        this.baseUrl = baseUrl;
        this.timeout = 10000; // 10 seconds
    }

    /**
     * Make an HTTP request to the API
     * @param {string} command - The command to send
     * @param {Array} args - Arguments for the command
     * @returns {Promise<Object>} API response
     */
    async makeRequest(command, args = []) {
        const url = new URL('/command', window.location.origin);
        const params = [command, ...args];
        url.searchParams.set('cmd', params.join(' '));

        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), this.timeout);

            const response = await fetch(url.toString(), {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                },
                credentials: 'same-origin', // Include cookies for authentication
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            if (response.status === 401) {
                // Authentication required - redirect to login
                window.location.href = '/login';
                throw new Error('Authentication required');
            }

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            return data;
        } catch (error) {
            if (error.name === 'AbortError') {
                throw new Error('Request timeout');
            }
            throw error;
        }
    }

    /**
     * Check if the server is alive
     * @returns {Promise<Object>} Server status
     */
    async checkAlive() {
        return this.makeRequest('alive');
    }

    /**
     * Get status of all processes or a specific process
     * @param {string} processName - Optional process name for specific status
     * @returns {Promise<Object>} Process status data
     */
    async getStatus(processName = null) {
        if (processName) {
            return this.makeRequest('detail', [processName]);
        }
        return this.makeRequest('status');
    }

    /**
     * Start a process
     * @param {string} processName - Name of the process to start
     * @returns {Promise<Object>} Operation result
     */
    async startProcess(processName) {
        return this.makeRequest('start', [processName]);
    }

    /**
     * Stop a process
     * @param {string} processName - Name of the process to stop
     * @returns {Promise<Object>} Operation result
     */
    async stopProcess(processName) {
        return this.makeRequest('stop', [processName]);
    }

    /**
     * Restart a process
     * @param {string} processName - Name of the process to restart
     * @returns {Promise<Object>} Operation result
     */
    async restartProcess(processName) {
        return this.makeRequest('restart', [processName]);
    }

    /**
     * Get detailed information about a specific process
     * @param {string} processName - Name of the process
     * @returns {Promise<Object>} Detailed process information
     */
    async getProcessDetail(processName) {
        return this.makeRequest('detail', [processName]);
    }

    /**
     * Perform bulk operations on multiple processes
     * @param {string} operation - Operation to perform (start, stop, restart)
     * @param {Array<string>} processNames - Array of process names
     * @returns {Promise<Array>} Array of operation results
     */
    async bulkOperation(operation, processNames) {
        const operations = processNames.map(name => {
            switch (operation) {
                case 'start':
                    return this.startProcess(name);
                case 'stop':
                    return this.stopProcess(name);
                case 'restart':
                    return this.restartProcess(name);
                default:
                    throw new Error(`Unknown operation: ${operation}`);
            }
        });

        try {
            const results = await Promise.allSettled(operations);
            return results.map((result, index) => ({
                processName: processNames[index],
                success: result.status === 'fulfilled',
                data: result.status === 'fulfilled' ? result.value : null,
                error: result.status === 'rejected' ? result.reason.message : null
            }));
        } catch (error) {
            throw new Error(`Bulk operation failed: ${error.message}`);
        }
    }
}

/**
 * API Response Handler
 * Utility class for handling API responses consistently
 */
class APIResponseHandler {
    /**
     * Check if an API response indicates success
     * @param {Object} response - API response object
     * @returns {boolean} True if successful
     */
    static isSuccess(response) {
        return response && response.status === 'success';
    }

    /**
     * Extract error message from API response
     * @param {Object} response - API response object
     * @returns {string} Error message
     */
    static getErrorMessage(response) {
        if (!response) {
            return 'Unknown error occurred';
        }
        return response.message || 'Operation failed';
    }

    /**
     * Extract process data from API response
     * @param {Object} response - API response object
     * @returns {Object|null} Process data or null
     */
    static getProcessData(response) {
        if (!this.isSuccess(response) || !response.data) {
            return null;
        }
        return response.data;
    }

    /**
     * Normalize process status data
     * @param {Object} processData - Raw process data from API
     * @returns {Object} Normalized process data
     */
    static normalizeProcessData(processData) {
        if (!processData) return null;

        // Handle both single process and multiple processes data
        if (typeof processData === 'object' && !Array.isArray(processData)) {
            const processes = {};
            
            for (const [name, data] of Object.entries(processData)) {
                processes[name] = {
                    name: data.name || name,
                    status: data.status || 'unknown',
                    pid: data.pid || null,
                    uptime: data.uptime || '0s',
                    restarts: data.restarts || 0,
                    exitcode: data.exitcode || null,
                    cmd: data.cmd || '',
                    config: data.config || {}
                };
            }
            
            return processes;
        }
        
        return processData;
    }

    /**
     * Format uptime string for display
     * @param {string} uptime - Uptime string from API
     * @returns {string} Formatted uptime
     */
    static formatUptime(uptime) {
        if (!uptime || uptime === '0s') {
            return '-';
        }
        return uptime;
    }

    /**
     * Get status color class for UI
     * @param {string} status - Process status
     * @returns {string} CSS class name
     */
    static getStatusClass(status) {
        const statusMap = {
            'running': 'running',
            'stopped': 'stopped',
            'starting': 'starting',
            'stopping': 'stopping',
            'error': 'error',
            'fatal': 'error',
            'exited': 'error'
        };
        return statusMap[status] || 'stopped';
    }

    /**
     * Get status icon for UI
     * @param {string} status - Process status
     * @returns {string} Icon character
     */
    static getStatusIcon(status) {
        const iconMap = {
            'running': '▶',
            'stopped': '⏸',
            'starting': '⏳',
            'stopping': '⏸',
            'error': '⚠',
            'fatal': '✕',
            'exited': '⏹'
        };
        return iconMap[status] || '?';
    }
}

// Create global API instance
window.taskmasterAPI = new TaskmasterAPI();
window.APIResponseHandler = APIResponseHandler;
