"""Process manager module.

This module handles process lifecycle management and status tracking.
"""
import os
import signal
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

from .worker import ProcessWorker
from .monitor import ProcessMonitor

class ProcessManager:
    """Manages process lifecycle and status."""

    def __init__(self, config_manager, smtp_config=None):
        """Initialize the process manager."""
        self.config_manager = config_manager
        self.smtp_config = smtp_config
        self.logger = logging.getLogger(__name__)
        self.processes: Dict[str, ProcessWorker] = {}
        self.monitor = ProcessMonitor(self)
        self.load_programs()
        self.start_all_autostart()
        self.monitor.start_monitoring()
        
    

    def get_smtp_config(self) -> Dict[str, Any]:
        """Get SMTP configuration for notifications."""
        return self.smtp_config
    
    def load_programs(self):
        """Load program configurations and initialize workers."""
        programs = self.config_manager.get_all_program_configs()
        for name, config in programs.items():
            self.processes[name] = ProcessWorker(name, config, self)
    
    def program_exists(self, program_name: str) -> bool:
        """Check if a program exists in configuration."""
        return program_name in self.processes

    def start_program(self, program_name: str) -> bool:
        """Start a program."""
        if not self.program_exists(program_name):
            self.logger.error(f"Program '{program_name}' not found")
            return False

        worker = self.processes[program_name]
        return worker.start()

    def stop_program(self, program_name: str) -> bool:
        """Stop a program."""
        if not self.program_exists(program_name):
            self.logger.error(f"Program '{program_name}' not found")
            return False

        worker = self.processes[program_name]
        return worker.stop()

    def restart_program(self, program_name: str) -> bool:
        """Restart a program."""
        if not self.program_exists(program_name):
            self.logger.error(f"Program '{program_name}' not found")
            return False

        worker = self.processes[program_name]
        return worker.restart()

    def get_program_status(self, program_name: str) -> Dict[str, Any]:
        """Get status of a specific program."""
        if not self.program_exists(program_name):
            return {}

        worker = self.processes[program_name]
        return worker.get_status()

    def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all programs."""
        return {name: worker.get_status() for name, worker in self.processes.items()}

    def start_all_autostart(self):
        """Start all programs configured for autostart."""
        for name, worker in self.processes.items():
            if worker.config.get('autostart', False):
                self.logger.info(f"Auto-starting program: {name}")
                worker.start()

    def stop_all(self):
        """Stop all running programs."""
        for worker in self.processes.values():
            if worker.is_running():
                worker.stop()