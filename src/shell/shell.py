# Main shell interface
# Interactive control shell with line editing and command processing
"""
Taskmaster Control Shell
Interactive urwid-based control interface
"""

import urwid
import random
import logging



# Application state
current_view = "status"  # status, detail, help
selected_program = None
command_history = []
command_input = ""

class TaskmasterUI:
    def __init__(self, process_manager=None, daemon=None):
        self.process_manager = process_manager
        self.daemon = daemon
        self.logger = logging.getLogger(__name__)
        self.use_mock_data = process_manager is None

        self.setup_ui()

    def get_programs(self):
        """Get programs data from process manager or mock data"""
        if self.process_manager is None:
            # Mock data for testing purposes
            return {
                'nginx': {
                    'status': 'running',
                    'pid': 1234,
                    'uptime': '2h 15m',
                    'restarts': 0,
                    'cmd': '/usr/sbin/nginx -g "daemon off;"',
                    'numprocs': 1,
                    'autostart': True,
                    'autorestart': 'unexpected',
                    'exitcodes': [0, 2],
                    'startretries': 3,
                    'starttime': 1,
                    'stopsignal': 'TERM',
                    'stoptime': 10,
                    'stdout': '/var/log/nginx/stdout.log',
                    'stderr': '/var/log/nginx/stderr.log'
                },
                # Add more mock programs as needed
            }
        return self.process_manager.get_all_status() 

    def setup_ui(self):
        # Create main components
        self.header = urwid.Text("Taskmaster Control Shell", align='center')
        self.body_walker = urwid.SimpleFocusListWalker([])
        self.body = urwid.ListBox(self.body_walker)
        self.footer = urwid.Text("")

        # Create command input
        self.command_edit = urwid.Edit("taskmaster> ")

        # Create footer pile with command input and status
        self.footer_pile = urwid.Pile([
            urwid.Divider(),
            self.command_edit,
            urwid.AttrMap(self.footer, 'footer')
        ])

        # Main frame
        self.main_frame = urwid.Frame(
            self.body,
            header=urwid.AttrMap(self.header, 'header'),
            footer=self.footer_pile
        )

        # Set focus to command input by default
        self.footer_pile.focus_position = 1

        self.refresh_view()

    def refresh_view(self):
        if current_view == "status":
            self.show_status_view()
        elif current_view == "detail":
            self.show_detail_view()
        elif current_view == "help":
            self.show_help_view()

    def show_status_view(self):
        self.body_walker[:] = [
            urwid.Text(('title', "Program Status Overview")),
            urwid.Divider(),
            urwid.Text(('header', f"{'Name':<15} {'Status':<10} {'PID':<8} {'Uptime':<10} {'Restarts':<8}")),
            urwid.Divider('-'),
        ]

        programs = self.get_programs()
        for name, info in programs.items():
            status_color = self.get_status_color(info['status'])
            line = f"{name:<15} {info['status']:<10} {str(info['pid'] or '-'):<8} {info['uptime']:<10} {info['restarts']:<8}"
            self.body_walker.append(urwid.Text((status_color, line)))

        self.body_walker.append(urwid.Divider())

        self.footer.set_text("Type 'help' for available commands")

    def show_detail_view(self):
        programs = self.get_programs()
        if not selected_program or selected_program not in programs:
            self.body_walker[:] = [urwid.Text("No program selected or program not found")]
            return

        prog = programs[selected_program]
        self.body_walker[:] = [
            urwid.Text(('title', f"Program Details: {selected_program}")),
            urwid.Divider(),
            urwid.Text(f"Status: {prog['status']}"),
            urwid.Text(f"PID: {prog['pid'] or 'N/A'}"),
            urwid.Text(f"Uptime: {prog['uptime']}"),
            urwid.Text(f"Restarts: {prog['restarts']}"),
            urwid.Divider(),
            urwid.Text("Configuration:"),
            urwid.Text(f"  Command: {prog['cmd']}"),
            urwid.Text(f"  Processes: {prog['numprocs']}"),
            urwid.Text(f"  Autostart: {prog['autostart']}"),
            urwid.Text(f"  Autorestart: {prog['autorestart']}"),
            urwid.Text(f"  Exit codes: {prog['exitcodes']}"),
            urwid.Text(f"  Start retries: {prog['startretries']}"),
            urwid.Text(f"  Start time: {prog['starttime']}s"),
            urwid.Text(f"  Stop signal: {prog['stopsignal']}"),
            urwid.Text(f"  Stop time: {prog['stoptime']}s"),
            urwid.Text(f"  Stdout: {prog['stdout']}"),
            urwid.Text(f"  Stderr: {prog['stderr']}"),
            urwid.Divider(),
            urwid.Text("Type 'status' to return to main view")
        ]

        self.footer.set_text(f"Viewing details for {selected_program}")

    def show_help_view(self):
        self.body_walker[:] = [
            urwid.Text(('title', "TASKMASTER CONTROL SHELL - HELP")),
            urwid.Divider(),
            urwid.Text(('header', "OVERVIEW:")),
            urwid.Text("  Interactive control interface for managing taskmaster programs."),
            urwid.Text("  Use commands below to control program lifecycle and view status."),
            urwid.Divider(),
            urwid.Text(('header', "AVAILABLE COMMANDS:")),
            urwid.Divider(),
            urwid.Text(('success', "PROGRAM MANAGEMENT:")),
            urwid.Text("  start <program>        - Start a specific program"),
            urwid.Text("  stop <program>         - Stop a specific program"),
            urwid.Text("  restart <program>      - Restart a specific program"),
            urwid.Divider(),
            urwid.Text(('info', "INFORMATION & MONITORING:")),
            urwid.Text("  status                 - Show status overview of all programs"),
            urwid.Text("  detail <program>       - Show detailed information for a program"),
            urwid.Divider(),
            urwid.Text(('warning', "CONFIGURATION & SYSTEM:")),
            urwid.Text("  reload                 - Reload taskmaster configuration"),
            urwid.Text("  help [command]         - Show general help or detailed command help"),
            urwid.Text("  quit                   - Exit the control shell"),
            urwid.Divider(),
            urwid.Text(('header', "COMMAND SYNTAX:")),
            urwid.Text("  • Commands are case-insensitive"),
            urwid.Text("  • <program> refers to program names defined in configuration"),
            urwid.Text("  • [command] indicates optional parameter"),
            urwid.Text("  • Use 'help <command>' for detailed syntax and examples"),
            urwid.Divider(),
        ]

        # Show available programs if any exist
        programs = self.get_programs()
        if programs:
            self.body_walker.extend([
                urwid.Text(('header', "AVAILABLE PROGRAMS:")),
                urwid.Divider(),
            ])

            # Group programs by status for better organization
            running_programs = []
            stopped_programs = []
            other_programs = []

            for name, info in programs.items():
                status = info.get('status', 'unknown')
                if status == 'running':
                    running_programs.append(name)
                elif status == 'stopped':
                    stopped_programs.append(name)
                else:
                    other_programs.append(name)

            if running_programs:
                self.body_walker.append(urwid.Text(('success', "  Running:")))
                for name in sorted(running_programs):
                    self.body_walker.append(urwid.Text(f"    {name}"))

            if stopped_programs:
                self.body_walker.append(urwid.Text(('warning', "  Stopped:")))
                for name in sorted(stopped_programs):
                    self.body_walker.append(urwid.Text(f"    {name}"))

            if other_programs:
                self.body_walker.append(urwid.Text(('info', "  Other:")))
                for name in sorted(other_programs):
                    self.body_walker.append(urwid.Text(f"    {name}"))

            self.body_walker.append(urwid.Divider())
        else:
            self.body_walker.extend([
                urwid.Text(('warning', "No programs currently configured.")),
                urwid.Text("Use 'reload' to load configuration or check your config file."),
                urwid.Divider(),
            ])

        self.body_walker.extend([
            urwid.Text(('header', "USAGE EXAMPLES:")),
            urwid.Text("  help start             - Show detailed help for start command"),
            urwid.Text("  start nginx            - Start the nginx program"),
            urwid.Text("  status                 - View all program statuses"),
            urwid.Text("  detail webapp          - View detailed info for webapp"),
            urwid.Text("  restart nginx          - Restart the nginx program"),
            urwid.Divider(),
            urwid.Text(('header', "NAVIGATION:")),
            urwid.Text("  • Type commands in the input field at the bottom"),
            urwid.Text("  • Press Enter to execute commands"),
            urwid.Text("  • Use Ctrl+C or Ctrl+D to exit"),
            urwid.Text("  • Type 'status' to return to the main status view"),
            urwid.Divider(),
            urwid.Text(('info', "For detailed help on any command, type: help <command>"))
        ])

        self.footer.set_text("General Help - Type 'help <command>' for detailed command help")

    def show_command_help(self, command_name):
        """Show detailed help for a specific command"""
        command_name = command_name.lower()

        # Define detailed help for each command
        command_help = {
            'status': {
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
            }
        }

        # Check if command exists
        if command_name not in command_help:
            self.body_walker[:] = [
                urwid.Text(('title', f"COMMAND HELP - UNKNOWN COMMAND")),
                urwid.Divider(),
                urwid.Text(('error', f"ERROR: '{command_name}' is not a valid command.")),
                urwid.Divider(),
                urwid.Text(('header', "AVAILABLE COMMANDS:")),
                urwid.Text(('success', "  Program Management:")),
                urwid.Text("    start, stop, restart"),
                urwid.Text(('info', "  Information & Monitoring:")),
                urwid.Text("    status, detail"),
                urwid.Text(('warning', "  Configuration & System:")),
                urwid.Text("    reload, help, quit"),
                urwid.Divider(),
                urwid.Text(('header', "SUGGESTIONS:")),
                urwid.Text("  • Type 'help' to see the complete help overview"),
                urwid.Text("  • Type 'help <command>' for detailed help on a specific command"),
                urwid.Text("  • Check your spelling - commands are case-insensitive"),
                urwid.Divider(),
                urwid.Text(('header', "NAVIGATION:")),
                urwid.Text("  • Type 'help' to return to general help"),
                urwid.Text("  • Type 'status' to return to main status view"),
            ]
            self.footer.set_text(f"Invalid command: '{command_name}' - Type 'help' for available commands")
            return

        # Display detailed help for the command
        help_info = command_help[command_name]
        self.body_walker[:] = [
            urwid.Text(('title', f"COMMAND HELP - {command_name.upper()}")),
            urwid.Divider(),
            urwid.Text(('header', "SYNTAX:")),
            urwid.Text(('info', f"  {help_info['syntax']}")),
            urwid.Divider(),
            urwid.Text(('header', "DESCRIPTION:")),
            urwid.Text(f"  {help_info['description']}"),
            urwid.Divider(),
            urwid.Text(('header', "PARAMETERS:")),
            urwid.Text(f"  {help_info['parameters']}"),
            urwid.Divider(),
            urwid.Text(('header', "USAGE EXAMPLES:")),
        ]

        for i, example in enumerate(help_info['examples'], 1):
            self.body_walker.append(urwid.Text(('success', f"  {i}. {example}")))

        self.body_walker.extend([
            urwid.Divider(),
            urwid.Text(('header', "DETAILED INFORMATION:")),
        ])

        for detail in help_info['details']:
            self.body_walker.append(urwid.Text(f"  • {detail}"))

        # Add program names for commands that need them
        if command_name in ['start', 'stop', 'restart', 'detail']:
            programs = self.get_programs()
            if programs:
                self.body_walker.extend([
                    urwid.Divider(),
                    urwid.Text(('header', "AVAILABLE PROGRAMS:")),
                ])

                # Group programs by status for better organization
                running_programs = []
                stopped_programs = []
                other_programs = []

                for name, info in programs.items():
                    status = info.get('status', 'unknown')
                    if status == 'running':
                        running_programs.append(name)
                    elif status == 'stopped':
                        stopped_programs.append(name)
                    else:
                        other_programs.append(name)

                if running_programs:
                    self.body_walker.append(urwid.Text(('success', "  Running:")))
                    for name in sorted(running_programs):
                        self.body_walker.append(urwid.Text(f"    {name}"))

                if stopped_programs:
                    self.body_walker.append(urwid.Text(('warning', "  Stopped:")))
                    for name in sorted(stopped_programs):
                        self.body_walker.append(urwid.Text(f"    {name}"))

                if other_programs:
                    self.body_walker.append(urwid.Text(('info', "  Other:")))
                    for name in sorted(other_programs):
                        self.body_walker.append(urwid.Text(f"    {name}"))
            else:
                self.body_walker.extend([
                    urwid.Text(('warning', "  No programs currently available.")),
                    urwid.Text("  Use 'reload' to load configuration."),
                ])

        self.body_walker.extend([
            urwid.Divider(),
            urwid.Text(('header', "NAVIGATION:")),
            urwid.Text("  • Type 'help' to return to general help"),
            urwid.Text("  • Type 'status' to return to main status view"),
            urwid.Text("  • Type 'help <other_command>' for help on other commands"),
        ])

        self.footer.set_text(f"Detailed help for '{command_name}' command")

    def get_status_color(self, status):
        colors = {
            'running': 'success',
            'stopped': 'warning',
            'fatal': 'error',
            'starting': 'info'
        }
        return colors.get(status, 'normal')

    def handle_command(self, command):
        global current_view, selected_program

        command = command.strip().lower()
        parts = command.split()

        if not parts:
            return

        cmd = parts[0]
        args = parts[1:] if len(parts) > 1 else []

        if cmd == "quit" or cmd == "exit":
            raise urwid.ExitMainLoop()
        elif cmd == "status":
            current_view = "status"
            self.refresh_view()
        elif cmd == "help":
            if args:
                # Show detailed help for specific command
                self.show_command_help(args[0])
            else:
                # Show general help view
                current_view = "help"
                self.refresh_view()
        elif cmd == "detail" and args:
            program_name = args[0]
            programs = self.get_programs()
            if program_name in programs:
                selected_program = program_name
                current_view = "detail"
                self.refresh_view()
            else:
                self.footer.set_text(f"Error: Program '{program_name}' not found")
        elif cmd == "start" and args:
            self.start_program(args[0])
        elif cmd == "stop" and args:
            self.stop_program(args[0])
        elif cmd == "restart" and args:
            self.restart_program(args[0])
        elif cmd == "reload":
            self.reload_config()
        else:
            self.footer.set_text(f"Unknown command: {command}. Type 'help' for available commands")

    def start_program(self, name):
        programs = self.get_programs()
        if name not in programs:
            self.footer.set_text(f"Error: Program '{name}' not found")
            return

        if self.use_mock_data:
            prog = programs[name]
            if prog['status'] == 'running':
                self.footer.set_text(f"{name}: already started")
            else:
                prog['status'] = 'running'
                prog['pid'] = random.randint(1000, 9999)
                prog['uptime'] = "0m"
                self.footer.set_text(f"{name}: started")
                if current_view == "status":
                    self.refresh_view()
        else:
            # TODO: Use real process manager
            self.footer.set_text(f"Starting {name}...")

    def stop_program(self, name):
        programs = self.get_programs()
        if name not in programs:
            self.footer.set_text(f"Error: Program '{name}' not found")
            return

        if self.use_mock_data:
            prog = programs[name]
            if prog['status'] == 'stopped':
                self.footer.set_text(f"{name}: already stopped")
            else:
                prog['status'] = 'stopped'
                prog['pid'] = None
                prog['uptime'] = "0m"
                self.footer.set_text(f"{name}: stopped")
                if current_view == "status":
                    self.refresh_view()
        else:
            # TODO: Use real process manager
            self.footer.set_text(f"Stopping {name}...")

    def restart_program(self, name):
        programs = self.get_programs()
        if name not in programs:
            self.footer.set_text(f"Error: Program '{name}' not found")
            return

        if self.use_mock_data:
            prog = programs[name]
            prog['status'] = 'running'
            prog['pid'] = random.randint(1000, 9999)
            prog['uptime'] = "0m"
            prog['restarts'] += 1
            self.footer.set_text(f"{name}: restarted")
            if current_view == "status":
                self.refresh_view()
        else:
            # TODO: Use real process manager
            self.footer.set_text(f"Restarting {name}...")

    def reload_config(self):
        self.footer.set_text("Configuration reloaded (mock)")
        if current_view == "status":
            self.refresh_view()

def on_input(key):
    # Always ensure focus is on command input
    if ui.main_frame.focus_position != 'footer':
        ui.main_frame.focus_position = 'footer'
        ui.footer_pile.focus_position = 1

    if key == 'enter':
        command = ui.command_edit.get_edit_text()
        if command.strip():
            command_history.append(command)
            ui.handle_command(command)
            ui.command_edit.set_edit_text("")
        # Keep focus on command input after processing command
        ui.main_frame.focus_position = 'footer'
        ui.footer_pile.focus_position = 1
        return True
    elif key in ('ctrl c', 'ctrl d'):
        raise urwid.ExitMainLoop()

    # For any other key, make sure we're focused on command input
    if ui.main_frame.focus_position != 'footer':
        ui.main_frame.focus_position = 'footer'
        ui.footer_pile.focus_position = 1

# Color palette
palette = [
    ('header', 'white', 'dark blue'),
    ('footer', 'white', 'dark red'),
    ('title', 'white,bold', 'black'),
    ('success', 'light green', 'black'),
    ('warning', 'yellow', 'black'),
    ('error', 'light red', 'black'),
    ('info', 'light cyan', 'black'),
    ('normal', 'white', 'black'),
]

class TaskmasterControlShell:
    """Main control shell class"""

    def __init__(self, process_manager=None, daemon=None):
        self.process_manager = process_manager
        self.daemon = daemon
        self.logger = logging.getLogger(__name__)

    def run(self):
        """Run the control shell"""
        global ui

        # Initialize UI
        ui = TaskmasterUI(self.process_manager, self.daemon)

        # Set initial focus to command input
        ui.main_frame.focus_position = 'footer'
        ui.footer_pile.focus_position = 1

        # Run the application
        loop = urwid.MainLoop(ui.main_frame, palette, unhandled_input=on_input)

        try:
            loop.run()
        except KeyboardInterrupt:
            self.logger.info("Control shell interrupted by user")
        except Exception as e:
            self.logger.error(f"Control shell error: {e}")
            raise


if __name__ == "__main__":
    # Initialize UI with mock data
    ui = TaskmasterUI()

    # Set initial focus to command input
    ui.main_frame.focus_position = 'footer'
    ui.footer_pile.focus_position = 1

    # Run the application
    loop = urwid.MainLoop(ui.main_frame, palette, unhandled_input=on_input)
    loop.run()
