"""Process monitoring module.

This module handles process monitoring and health checks.
"""
import logging ,threading,time
from datetime import datetime
from typing import Dict, Any

class ProcessMonitor:
    """Monitors process health and status."""

    def __init__(self, manager):
        self.manager = manager
        self.logger = logging.getLogger(__name__)
        self.running = False
        self.monitor_thread = None


    def start_monitoring(self):
        """Start the monitoring thread."""
        self.running = True
        self.monitor_thread = threading.Thread(target=self.monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()

    def check_all(self):
        for name, worker in self.manager.processes.items():
            self.check_process(worker)

    def check_process(self, worker):
        if not worker.is_running():
        
            if self.should_restart(worker):
                self.logger.info(f"Restarting process {worker.name}")
                worker.start()
            

    def should_restart(self, worker):
        if not worker.should_autorestart():
            return False
        return True

    def monitor_loop(self):
        """Main monitoring loop."""
        while self.running:
            self.check_all()
            time.sleep(1)