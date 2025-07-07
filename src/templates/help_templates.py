"""Help templates and command documentation for Taskmaster"""

from enum import Enum
from typing import Dict, Any

class CommandCategory(Enum):
    PROGRAM_MANAGEMENT = "PROGRAM MANAGEMENT"
    INFORMATION = "INFORMATION & MONITORING"
    CONFIGURATION = "CONFIGURATION & SYSTEM"

class CommandHelpTemplates:
    @staticmethod
    def get_command_help() -> Dict[str, Dict[str, Any]]:
        return {
            'status': {
                'category': CommandCategory.INFORMATION,
                'syntax': 'status',
                'description': 'Display the status overview of all configured programs',
                'parameters': 'None',
                'examples': [
                    'status  # Show status of all programs'
                ],
                'details': [
                    'Shows a table with program name, status, PID, uptime, and restart count',
                    'Status can be: running, stopped, fatal, starting',
                    'This is the default view when starting the shell'
                ]
            },
            'start': {
                'category': CommandCategory.PROGRAM_MANAGEMENT,
                'syntax': 'start <program>',
                'description': 'Start a specific program',
                'parameters': '<program> - Name of the program to start',
                'examples': [
                    'start nginx     # Start the nginx program',
                    'start webapp    # Start the webapp program'
                ],
                'details': [
                    'Starts the specified program if it is not already running',
                    'If the program is already running, displays a message',
                    'The program must be defined in the configuration file'
                ]
            },
            'stop': {
                'category': CommandCategory.PROGRAM_MANAGEMENT,
                'syntax': 'stop <program>',
                'description': 'Stop a specific program',
                'parameters': '<program> - Name of the program to stop',
                'examples': [
                    'stop nginx      # Stop the nginx program',
                    'stop webapp     # Stop the webapp program'
                ],
                'details': [
                    'Stops the specified program if it is currently running',
                    'If the program is already stopped, displays a message',
                    'Uses the configured stop signal and timeout'
                ]
            },
            'restart': {
                'category': CommandCategory.PROGRAM_MANAGEMENT,
                'syntax': 'restart <program>',
                'description': 'Restart a specific program',
                'parameters': '<program> - Name of the program to restart',
                'examples': [
                    'restart nginx   # Restart the nginx program',
                    'restart webapp  # Restart the webapp program'
                ],
                'details': [
                    'Stops and then starts the specified program',
                    'Increments the restart counter for the program',
                    'Useful for applying configuration changes'
                ]
            },
            'detail': {
                'category': CommandCategory.INFORMATION,
                'syntax': 'detail <program>',
                'description': 'Show detailed information for a specific program',
                'parameters': '<program> - Name of the program to view',
                'examples': [
                    'detail nginx    # Show detailed info for nginx',
                    'detail webapp   # Show detailed info for webapp'
                ],
                'details': [
                    'Displays comprehensive information about the program',
                    'Includes status, PID, uptime, configuration settings',
                    'Shows command, autostart, autorestart, and log file paths'
                ]
            },
            'reload': {
                'category': CommandCategory.CONFIGURATION,
                'syntax': 'reload',
                'description': 'Reload the taskmaster configuration',
                'parameters': 'None',
                'examples': [
                    'reload          # Reload configuration from file'
                ],
                'details': [
                    'Reloads the configuration file without restarting taskmaster',
                    'New programs will be added, removed programs will be stopped',
                    'Configuration changes for existing programs will be applied'
                ]
            },
            'help': {
                'category': CommandCategory.CONFIGURATION,
                'syntax': 'help [command]',
                'description': 'Show help information',
                'parameters': '[command] - Optional command name for detailed help',
                'examples': [
                    'help            # Show general help with all commands',
                    'help start      # Show detailed help for start command',
                    'help stop       # Show detailed help for stop command'
                ],
                'details': [
                    'Without arguments: shows overview of all available commands',
                    'With command name: shows detailed help for that specific command',
                    'Lists available program names for commands that require them'
                ]
            },
            'quit': {
                'category': CommandCategory.CONFIGURATION,
                'syntax': 'quit',
                'description': 'Exit the taskmaster control shell',
                'parameters': 'None',
                'examples': [
                    'quit            # Exit the shell',
                    'exit            # Alternative way to exit'
                ],
                'details': [
                    'Cleanly exits the control shell interface',
                    'Does not affect running programs',
                    'Can also use Ctrl+C or Ctrl+D to exit'
                ]
            },
            'pid': {
                'category': CommandCategory.INFORMATION,
                'syntax': 'pid',
                'description': 'Get the PID of the taskmaster daemon',
                'parameters': 'None',
                'examples': [
                    'pid             # Get PID of taskmaster daemon'
                ],
                'details': [
                    'Displays the process ID of the running taskmaster daemon',
                    'Useful for debugging or process management tasks',
                    'Does not require any additional parameters'
                ]
    
            }
        }

    @staticmethod
    def get_overview_help() -> str:
        return """Interactive control interface for managing taskmaster programs.
Use commands below to control program lifecycle and view status."""

    @staticmethod
    def get_command_syntax_help() -> list[str]:
        return [
            "Commands are case-insensitive",
            "<program> refers to program names defined in configuration",
            "[command] indicates optional parameter",
            "Use 'help <command>' for detailed syntax and examples"
        ]

    @staticmethod
    def get_navigation_help() -> list[str]:
        return [
            "Type commands in the input field at the bottom",
            "Press Enter to execute commands", 
            "Use Ctrl+C or Ctrl+D to exit",
            "Type 'status' to return to the main status view"
        ]