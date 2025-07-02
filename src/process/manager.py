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
from .supervisor import ProcessSupervisor

class ProcessManager:
    """Manages process lifecycle and status."""

    def __init__(self, config_manager):
        """Initialize the process manager."""
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        self.processes: Dict[str, ProcessWorker] = {}
        self.monitor = ProcessMonitor(self)
        self.supervisor = ProcessSupervisor(self)
        self.load_programs()
        self.start_all_autostart()
        
    def load_programs(self):
        """Load program configurations and initialize workers."""
        programs = self.config_manager.get_all_program_configs()
        # print("------------------------------------------------------------------")
        # print(programs)
        # print("------------------------------------------------------------------")
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
        print("-----------")
        for name, worker in self.processes.items():
            if worker.config.get('autostart', False):
                print(worker.config)
                self.logger.info(f"Auto-starting program: {name}")
                worker.start()

    def stop_all(self):
        """Stop all running programs."""
        for worker in self.processes.values():
            if worker.is_running():
                worker.stop()

    # def reload_config(self):
    #     """Reload program configurations."""
    #     # Store old program states
    #     old_states = {name: worker.get_status() for name, worker in self.processes.items()}
    #     old_programs = set(self.processes.keys())

    #     # Load new configurations
    #     programs = self.config_manager.get_all_program_configs()
    #     new_programs = set(programs.keys())

    #     # Stop removed programs
    #     for name in old_programs - new_programs:
    #         if name in self.processes:
    #             self.logger.info(f"Stopping removed program: {name}")
    #             self.processes[name].stop()
    #             del self.processes[name]

    #     # Update existing and add new programs
    #     for name, config in programs.items():
    #         if name in self.processes:
    #             # Update existing program
    #             worker = self.processes[name]
    #             was_running = worker.is_running()
    #             worker.update_config(config)
    #             if was_running:
    #                 worker.restart()
    #         else:
    #             # Add new program
    #             self.processes[name] = ProcessWorker(name, config, self)
    #             if config.get('autostart', False):
    #                 self.processes[name].start()

    def handle_program_exit(self, program_name: str, exit_code: int):
        """Handle program exit event."""
        if not self.program_exists(program_name):
            return

        worker = self.processes[program_name]
        self.supervisor.handle_exit(worker, exit_code)

    def check_health(self):
        """Check health of all programs."""
        self.monitor.check_all()
