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
        """Check health of all managed processes."""
        for name, worker in self.manager.processes.items():
            self.check_process(worker)

    def check_process(self, worker):
        """Check health of a single process."""
        try:
            # Check if process is running
            if worker.is_running():
                # Check if process has been running long enough to be considered stable
                if worker.start_time:
                    uptime = (datetime.now() - worker.start_time).total_seconds()
                    if uptime >= worker.config.get('startsecs', 1):
                        worker.status = "running"
                        
            else:
                # Process is not running
                if worker.status not in ["stopped", "stopping", "killed"]:
                    self.logger.warning(f"Process {worker.name} died unexpectedly")
                    self.handle_process_death(worker)

        except Exception as e:
            self.logger.error(f"Error checking process {worker.name}: {e}")

    def handle_process_death(self, worker):
        """Handle unexpected process death."""

        if worker.process:
            exit_code = worker.process.returncode
            worker.exit_code = exit_code
            
            autorestart = worker.config.get('autorestart', 'unexpected')
            exitcodes = worker.config.get('exitcodes', [0])
            print(f"Process {worker.name} with PID {worker.pid} has exited with code {exit_code}")
            print(" ************** checking autorestart policy...")
            print(f"Autorestart policy: {autorestart}, Exit codes: {exitcodes}")
            if autorestart == 'always':
                self.logger.info(f"Auto-restarting process {worker.name} (always)")
                worker.restart()
            # elif autorestart == 'unexpected' and exit_code not in exitcodes:
            #     self.logger.info(f"Auto-restarting process {worker.name} (unexpected exit {exit_code})")
            #     worker.restart()
            else:
                worker.status = "stopped"
    def monitor_loop(self):
        """Main monitoring loop."""
        while self.running:
            self.check_all()
            time.sleep(1)