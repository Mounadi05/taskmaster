# Main shell interface
# Interactive control shell with line editing and command processing
"""
Taskmaster Control Shell
Interactive urwid-based control interface
"""

import urwid, random, sys, os,argparse, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from core import Taskmasterctl
from config import ConfigManager
# Application state
current_view = "status"  # status, detail, help
selected_program = None
command_history = []
command_input = ""

old_pathfile = None 

class TaskmasterUI:
    def __init__(self, process_manager=None, daemon=None, filepath='config_file/taskmaster.yaml'):
        self.process_manager = process_manager
        self.daemon = daemon
        self.method = None
        self.port = None
        self.host = None
        self.client = None
        self.programs = {}
        self.filepath = filepath
        self.setup()



    def setup(self, reload=False):
        if reload and old_pathfile:
            self.filepath = old_pathfile
        Config = ConfigManager(self.filepath)
        server_config = Config.get_server_config()
        self.method = server_config.get('type', 'socket')
        self.port = server_config.get('port', 1337)
        self.host = server_config.get('host', 'localhost')
        self.client = Taskmasterctl(self.method, self.port, self.host)
        self.deamon_isAlive()
        if not self.client:
            print("Error: Unable to connect to Taskmaster daemon. Please check your configuration.")
            sys.exit(1)
        self.programs = self.get_programs()
        self.setup_ui()

    def deamon_isAlive(self):
        try:
            response = self.client.send_command('alive')
            print(response)
            if response and response['status'] == 'success':
                pass
            else:
                print("Taskmaster daemon is not running or reachable. Please start the daemon first.")
                sys.exit(1)
        except Exception as e:
            print(f"Error connecting to Taskmaster daemon: {e}")
            sys.exit(1)
        
        
    def get_programs(self):
        response = self.client.send_command('status')
        return response['data']
    
    def get_program(self, program_name):
        return self.programs.get(program_name, None)

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
        elif current_view == "help":
            self.show_help_view()

    def show_status_view(self):
        self.body_walker[:] = [
            urwid.Text(('title', "Program Status Overview")),
            urwid.Divider(),
            urwid.Text(('header', f"{'Name':<15} {'Status':<10} {'PID':<8} {'Uptime':<10} {'Restarts':<8} {'CMD':<40}")),
            urwid.Divider('-'),
        ]
        for name, info in self.programs.items():
            status_color = self.get_status_color(info['status'])
            line = f"{name:<15} {info['status']:<10} {str(info['pid'] or '-'):<8} {info['uptime']:<10} {info['restarts']:<8} {info['cmd']:<40}"
            self.body_walker.append(urwid.Text((status_color, line)))

        self.body_walker.append(urwid.Divider())

        self.footer.set_text("Type 'help' for available commands")

   
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
        programs = self.programs
        if programs:
            self.body_walker.extend([
                urwid.Text(('header', "AVAILABLE PROGRAMS:")),
                urwid.Divider(),
            ])

            # Group programs by status for better organization
            running_programs = []
            stopped_programs = []
            exited_programs = []
            other_programs = []

            for name, info in programs.items():
                status = info.get('status', 'unknown')
                if status == 'running':
                    running_programs.append(name)
                elif status == 'stopped':
                    stopped_programs.append(name)
                elif status == 'exited':
                    exited_programs.append(name)
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
            if exited_programs:
                self.body_walker.append(urwid.Text(('success', "  Exited:")))
                for name in sorted(exited_programs):
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
            if self.programs:
                self.body_walker.extend([
                    urwid.Divider(),
                    urwid.Text(('header', "AVAILABLE PROGRAMS:")),
                ])

                # Group programs by status for better organization
                running_programs = []
                stopped_programs = []
                other_programs = []

                for name, info in self.programs.items():
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
    
    def get_pid(self):
        pid_file = '/tmp/Taskmasterd.pid'
        if os.path.exists(pid_file):
            with open(pid_file, 'r') as f:
                pid = f.read().strip()
                if pid.isdigit():
                    return int(pid)
        return None
    
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
            self.programs = self.get_programs()
            self.refresh_view()
        elif cmd == "help":
            if args:
                # Show detailed help for specific commandaa
                self.show_command_help(args[0])
            else:
                # Show general help view
                current_view = "help"
                self.refresh_view()
        elif cmd == "detail" and args:
            program_name = args[0].strip()
            programs = self.programs.keys()
            if program_name in programs:
                message = self.client.send_command(parts)
                self.show_detail(message['data'], program_name)
            else:
                self.footer.set_text(f"Error: Program '{program_name}' not found")
        elif cmd == "start" and args:
            if self.check_program_cmd(args[0]):
                if args[0] in self.programs and (self.programs[args[0]]['status'] == 'running' or self.programs[args[0]]['status'] == 'starting'):
                    self.footer.set_text(f"Program '{args[0]}' is already running.")
                    return
                message = self.client.send_command(parts)
                self.programs[args[0]] = message['data']  
                current_view = "status" 
                self.refresh_view()
                self.footer.set_text(f"\nStart command sent: {message['message']}")
        elif cmd == "stop" and args:
            if self.check_program_cmd(args[0]):
                if args[0] not in self.programs or (self.programs[args[0]]['status'] != 'running' and self.programs[args[0]]['status'] != 'starting'):
                    self.footer.set_text(f"Program '{args[0]}' is not running.")
                    return
                message = self.client.send_command(parts)
                self.programs[args[0]] = message['data']  
                current_view = "status" 
                self.refresh_view()
                self.footer.set_text(f"\nStop command sent: {message['message']}")
        elif cmd == "restart" and args:
            start = True
            if self.check_program_cmd(args[0]):
                if args[0] not in self.programs or (self.programs[args[0]]['status'] != 'running' and self.programs[args[0]]['status'] != 'starting'):
                    start = False
                message = self.client.send_command(parts)
                self.programs[args[0]] = message['data']
                current_view = "status"
                self.refresh_view()
                if start:
                    self.footer.set_text(f"\n {start} : Restart command sent: {message['message']}")
                else:
                    if message['data']['status'] == 'starting':
                        self.footer.set_text(f"\nstart command sent: program '{args[0]}' was not running, so it was started.")
                    else:
                        self.footer.set_text(f"\nRestart command sent: {message['message']}")
        elif cmd == "pid":
            pid = self.get_pid()
            if pid:
                self.footer.set_text(f"Taskmaster daemon PID: {pid}")
            else:
                self.footer.set_text("Taskmaster daemon is not running or PID file not found.")
        elif cmd == "version":
            self.footer.set_text("Taskmaster Version: 1.1.1")
        elif cmd == "reload":
            self.client.send_command('reload')
            time.sleep(1) 
            self.reload_config()
        else:
            self.footer.set_text(f"Unknown command: {command}. Type 'help' for available commands")


    def check_program_cmd(self, program_name):
        program = self.get_program(program_name.strip())
        if not program:
            self.footer.set_text(f"Error: Program '{program_name}' not found.")
            return False
        cmd = program.get('cmd', '')
        # if cmd:
        #     if not os.path.exists(cmd):
        #         self.footer.set_text(f"Error: Command '{cmd}' for program '{program_name}' does not exist.")
        #         return False
        #     if os.path.isdir(cmd):
        #         self.footer.set_text(f"Error: Command '{cmd}' for program '{program_name}' is a directory, not a file.")
        #         return False
        #     if not os.access(cmd, os.X_OK):
        #         self.footer.set_text(f"Error: Command '{cmd}' for program '{program_name}' is not executable.")
        #         return False
        return True
   
    def reload_config(self):
               
        self.setup('true')
    
    def check_status(self, program_name):
        if program_name in self.programs:
            return self.programs[program_name]['status']
        else:
            return None
        
    def show_detail(self, data,program_name):

        global current_view
        # current_view = "detail"
        self.body_walker[:] = [
            urwid.Text(('title', f"Program Details")),
            urwid.Divider(),
            # Basic Info Section
            urwid.Text(('header', "Basic Information:")),
            urwid.Text(f"Command: {data[program_name].get('cmd', 'N/A')}"),
            urwid.Text(f"Status: {data[program_name].get('status', 'N/A')}"),
            urwid.Text(f"PID: {data[program_name].get('pid', 'N/A')}"),
            urwid.Text(f"Uptime: {data[program_name].get('uptime', 'N/A')} seconds"),
            urwid.Text(f"Restarts: {data[program_name].get('restarts', 'N/A')}"),
            urwid.Text(f"Number of Processes: {data[program_name]['config'].get('numprocs', 'N/A')}"),
            urwid.Text(f"Umask: {data[program_name]['config'].get('umask', 'N/A')}"),
            urwid.Text(f"User: {data[program_name]['config'].get('user', 'N/A')}"),
            urwid.Text(f"Group: {data[program_name]['config'].get('group', 'N/A')}"),
            urwid.Text(f"Priority: {data[program_name]['config'].get('priority', 'N/A')}"),
            urwid.Text(f"Working Directory: {data[program_name]['config'].get('workingdir', 'N/A')}"),
            urwid.Divider(),
            # Process Control Section
            urwid.Text(('header', "Process Control:")),
            urwid.Text(f"Autostart: {data[program_name]['config'].get('autostart', 'N/A')}"),
            urwid.Text(f"Autorestart: {data[program_name]['config'].get('autorestart', 'N/A')}"),
            urwid.Text(f"Exit Codes: {data[program_name]['config'].get('exitcodes', 'N/A')}"),
            urwid.Text(f"Start Retries: {data[program_name]['config'].get('startretries', 'N/A')}"),
            urwid.Text(f"Start Time: {data[program_name]['config'].get('startsecs', 'N/A')} seconds"),
            urwid.Text(f"Stop Signal: {data[program_name]['config'].get('stopsignal', 'N/A')}"),
            urwid.Text(f"Stop Time: {data[program_name]['config'].get('stoptsecs', 'N/A')} seconds"),
            urwid.Divider(),
        ]

        # Logging Section
        stdout = data.get('stdout', {})
        if isinstance(stdout, dict):
            self.body_walker.extend([
                urwid.Text(('header', "Stdout Configuration:")),
                urwid.Text(f"  Path: {stdout.get('path', 'N/A')}"),
                urwid.Text(f"  Max Bytes: {stdout.get('maxbytes', 'N/A')}")
            ])
        else:
            self.body_walker.append(urwid.Text(f"Stdout: {stdout}"))

        self.body_walker.append(urwid.Text(f"Stderr: {data.get('stderr', 'N/A')}"))
        self.body_walker.append(urwid.Divider())

        # Environment Variables Section
        env = data.get('env', {})
        if env:
            self.body_walker.extend([
                urwid.Text(('header', "Environment Variables:")),
            ])
            for key, value in env.items():
                self.body_walker.append(urwid.Text(f"  {key}: {value}"))
            self.body_walker.append(urwid.Divider())

        # Notifications Section
        on_failure = data.get('on_failure', {}).get('smtp', {})
        on_success = data.get('on_success', {}).get('smtp', {})

        if on_failure or on_success:
            self.body_walker.append(urwid.Text(('header', "Notifications:")))
            
            if on_failure:
                self.body_walker.extend([
                    urwid.Text(('warning', "On Failure:")),
                    urwid.Text(f"  Enabled: {on_failure.get('enabled', 'N/A')}"),
                    urwid.Text(f"  Subject: {on_failure.get('subject', 'N/A')}"),
                    urwid.Text(f"  From: {on_failure.get('from', 'N/A')}"),
                    urwid.Text("  To: " + ", ".join(on_failure.get('to', ['N/A'])))
                ])

            if on_success:
                self.body_walker.extend([
                    urwid.Text(('success', "On Success:")),
                    urwid.Text(f"  Enabled: {on_success.get('enabled', 'N/A')}"),
                    urwid.Text(f"  Subject: {on_success.get('subject', 'N/A')}"),
                    urwid.Text(f"  From: {on_success.get('from', 'N/A')}"),
                    urwid.Text("  To: " + ", ".join(on_success.get('to', ['N/A'])))
                ])

        self.body_walker.extend([
            urwid.Divider(),
            urwid.Text(('info', "Press 'status' to return to the main view"))
        ])

        self.footer.set_text("Viewing program details")
        


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

    def run(self):
        """Run the control shell"""
        global ui

        # Initialize UI
        ui = TaskmasterUI(self.process_manager, self.daemon,ui.file_path)

        # Set initial focus to command input
        ui.main_frame.focus_position = 'footer'
        ui.footer_pile.focus_position = 1

        # Run the application
        loop = urwid.MainLoop(ui.main_frame, palette, unhandled_input=on_input)

        try:
            loop.run()
        except KeyboardInterrupt:
            pass
        except Exception as e:
            pass
            raise


if __name__ == "__main__":
    # Initialize UI with mock data
    
    parser = argparse.ArgumentParser(description='Taskmaster Server')
    parser.add_argument('-c', '--config', type=str, default='config_file/taskmaster.yaml',
                        help='Path to the configuration file')
    args = parser.parse_args()
    if args.config:
        old_pathfile = args.config
    else:
        old_pathfile = 'config_file/taskmaster.yaml'

    ui = TaskmasterUI(filepath=args.config)

    # Set initial focus to command input
    ui.main_frame.focus_position = 'footer'
    ui.footer_pile.focus_position = 1
    
    # Run the application
    loop = urwid.MainLoop(ui.main_frame, palette, unhandled_input=on_input)
    loop.run()





