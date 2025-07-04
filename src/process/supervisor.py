"""Process supervision module.

This module handles process supervision, restart policies, and recovery.
"""
import logging
from datetime import datetime
from typing import Dict, Any

class ProcessSupervisor:
    """Supervises processes and handles restart policies."""

    def __init__(self, manager):
        self.manager = manager
        self.logger = logging.getLogger(__name__)

    def handle_exit(self, worker, exit_code: int):
        """Handle process exit event."""
        worker.exit_code = exit_code
        worker.stop_time = datetime.now()

        self.logger.info(f"Process {worker.name} exited with code {exit_code}")

        # Check if we should restart
        if self.should_restart(worker, exit_code):
            if self.can_retry(worker):
                self.logger.info(f"Restarting process {worker.name}")
                worker.restart()
            else:
                self.logger.warning(f"Process {worker.name} exceeded retry limit")
                worker.status = "fatal"
        else:
            worker.status = "stopped"

    def should_restart(self, worker, exit_code: int) -> bool:
        """Determine if process should be restarted."""
        autorestart = worker.config.get('autorestart', 'unexpected')
        exitcodes = worker.config.get('exitcodes', [0])

        if autorestart == 'always':
            return True
        elif autorestart == 'never':
            return False
        elif autorestart == 'unexpected':
            return exit_code not in exitcodes
        
        return False

    def can_retry(self, worker) -> bool:
        """Check if process can be retried."""
        startretries = worker.config.get('startretries', 3)
            
        return worker.restart_count < startretries
