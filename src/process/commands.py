"""Process control commands module.

This module provides command handling functionality for process control.
"""
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime

from .worker import ProcessWorker
from .manager import ProcessManager

class ProcessCommands:
    """Handles process control commands."""

    def __init__(self, manager: ProcessManager):
        self.manager = manager
        self.logger = logging.getLogger(__name__)

    def start(self, program_name: str) -> Dict[str, Any]:
        try:
            if not self.manager.program_exists(program_name):
                return {
                    "status": "error",
                    "message": f"Program '{program_name}' not found",
                    "timestamp": datetime.now().isoformat()
                }

            result = self.manager.start_program(program_name)
            return {
                "status": "success" if result else "error",
                "message": f"Program '{program_name}' started successfully" if result else f"Failed to start program '{program_name}'",
                "timestamp": datetime.now().isoformat(),
                "data": self.manager.get_program_status(program_name)
            }
        except Exception as e:
            self.logger.error(f"Error starting program {program_name}: {e}")
            return {
                "status": "error",
                "message": f"Error starting program '{program_name}': {str(e)}",
                "timestamp": datetime.now().isoformat()
            }

    def stop(self, program_name: str) -> Dict[str, Any]:
        try:
            if not self.manager.program_exists(program_name):
                return {
                    "status": "error",
                    "message": f"Program '{program_name}' not found",
                    "timestamp": datetime.now().isoformat()
                }

            result = self.manager.stop_program(program_name)
            return {
                "status": "success" if result else "error",
                "message": f"Program '{program_name}' stopped successfully" if result else f"Failed to stop program '{program_name}'",
                "timestamp": datetime.now().isoformat(),
                "data": self.manager.get_program_status(program_name)
            }
        except Exception as e:
            self.logger.error(f"Error stopping program {program_name}: {e}")
            return {
                "status": "error",
                "message": f"Error stopping program '{program_name}': {str(e)}",
                "timestamp": datetime.now().isoformat()
            }

    def restart(self, program_name: str) -> Dict[str, Any]:
        try:
            if not self.manager.program_exists(program_name):
                return {
                    "status": "error",
                    "message": f"Program '{program_name}' not found",
                    "timestamp": datetime.now().isoformat()
                }

            stop_result = self.manager.stop_program(program_name)
            if not stop_result:
                return {
                    "status": "error",
                    "message": f"Failed to stop program '{program_name}' during restart",
                    "timestamp": datetime.now().isoformat()
                }

            start_result = self.manager.start_program(program_name)
            return {
                "status": "success" if start_result else "error",
                "message": f"Program '{program_name}' restarted successfully" if start_result else f"Failed to restart program '{program_name}'",
                "timestamp": datetime.now().isoformat(),
                "data": self.manager.get_program_status(program_name)
                
            }
        except Exception as e:
            self.logger.error(f"Error restarting program {program_name}: {e}")
            return {
                "status": "error",
                "message": f"Error restarting program '{program_name}': {str(e)}",
                "timestamp": datetime.now().isoformat()
            }

    def status(self, program_name: Optional[str] = None) -> Dict[str, Any]:
        """Get program status."""
        try:
            if program_name:
                if not self.manager.program_exists(program_name):
                    return {
                        "status": "error",
                        "message": f"Program '{program_name}' not found",
                        "timestamp": datetime.now().isoformat()
                    }
                status_data = self.manager.get_program_status(program_name)
                # print(f"Status data for {program_name}: {status_data}")
                return {
                    "status": "success",
                    "data": {program_name: status_data},
                    "timestamp": datetime.now().isoformat()
                }
            else:
                all_statuses = self.manager.get_all_status()
                # print(f"All statuses: {all_statuses}")
                return {
                    "status": "success",
                    "data": all_statuses,
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            self.logger.error(f"Error getting status for {program_name or 'all programs'}: {e}")
            return {
                "status": "error",
                "message": f"Error getting status: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }