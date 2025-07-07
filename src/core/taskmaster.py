"""
Taskmaster Control Shell
Interactive urwid-based control interface for managing taskmaster processes.
"""

import urwid, random, sys, os, argparse, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from core import Taskmasterctl
from config import ConfigManager
from templates.help_templates import CommandHelpTemplates, CommandCategory  
from templates.ui_templates import UITemplates

# Application state
current_view = "status"  # status, detail, help
selected_program = None
command_history = []
command_input = ""
old_pathfile = None 

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

class TaskmasterUI:
    """Main UI class for the Taskmaster control shell"""
    
    def __init__(self, process_manager=None, daemon=None, filepath='config_file/taskmaster.yaml'):
        """Initialize the TaskmasterUI instance"""
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
        if reload:
            self.programs = self.get_programs()
        else :
            self.programs = self.get_programs()
            self.setup_ui()

    def deamon_isAlive(self):
        try:
            response = self.client.send_command('alive')
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
        """Display the status overview of all programs"""
        self.body_walker[:] = UITemplates.create_status_view(self.programs)
        self.footer.set_text("Type 'help' for available commands")

   
    def show_help_view(self):
        """Display the general help overview"""
        help_sections = []

        # Overview
        help_sections.extend([
            urwid.Text(('title', "TASKMASTER CONTROL SHELL - HELP")),
            urwid.Divider(),
            urwid.Text(('header', "OVERVIEW:")),
            urwid.Text(f"  {CommandHelpTemplates.get_overview_help()}"),
            urwid.Divider()
        ])

        # Commands by category
        command_help = CommandHelpTemplates.get_command_help()
        commands_by_category = {}
        for cmd_name, cmd_info in command_help.items():
            category = cmd_info['category']
            if category not in commands_by_category:
                commands_by_category[category] = []
            commands_by_category[category].append((cmd_name, cmd_info['description']))

        help_sections.append(urwid.Text(('header', "AVAILABLE COMMANDS:")))
        help_sections.append(urwid.Divider())

        for category in CommandCategory:
            if category in commands_by_category:
                color = 'success' if category == CommandCategory.PROGRAM_MANAGEMENT else \
                       'info' if category == CommandCategory.INFORMATION else 'warning'
                help_sections.append(urwid.Text((color, f"{category.value}:")))
                for cmd_name, description in sorted(commands_by_category[category]):
                    syntax = command_help[cmd_name]['syntax']
                    help_sections.append(urwid.Text(f"  {syntax:<20} - {description}"))
                help_sections.append(urwid.Divider())

        # Command syntax help
        help_sections.append(urwid.Text(('header', "COMMAND SYNTAX:")))
        for syntax_help in CommandHelpTemplates.get_command_syntax_help():
            help_sections.append(urwid.Text(f"  • {syntax_help}"))

        help_sections.append(urwid.Divider())

        # Available programs section
        if self.programs:
            programs_by_status = {'running': [], 'stopped': [], 'exited': [], 'other': []}
            for name, info in self.programs.items():
                status = info.get('status', 'unknown')
                if status in programs_by_status:
                    programs_by_status[status].append(name)
                else:
                    programs_by_status['other'].append(name)

            if any(programs_by_status.values()):
                help_sections.append(urwid.Text(('header', "AVAILABLE PROGRAMS:")))
                help_sections.append(urwid.Divider())
                
                if programs_by_status['running']:
                    help_sections.extend(UITemplates.create_program_section("Running", programs_by_status['running'], 'success'))
                if programs_by_status['stopped']:
                    help_sections.extend(UITemplates.create_program_section("Stopped", programs_by_status['stopped'], 'warning'))
                if programs_by_status['exited']:
                    help_sections.extend(UITemplates.create_program_section("Exited", programs_by_status['exited'], 'info'))
                if programs_by_status['other']:
                    help_sections.extend(UITemplates.create_program_section("Other", programs_by_status['other']))
                help_sections.append(urwid.Divider())
        else:
            help_sections.extend([
                urwid.Text(('warning', "No programs currently configured.")),
                urwid.Text("Use 'reload' to load configuration or check your config file."),
                urwid.Divider(),
            ])

        # Navigation help
        help_sections.append(urwid.Text(('header', "NAVIGATION:")))
        for nav_help in CommandHelpTemplates.get_navigation_help():
            help_sections.append(urwid.Text(f"  • {nav_help}"))
        help_sections.append(urwid.Divider())
        
        help_sections.append(urwid.Text(('info', "For detailed help on any command, type: help <command>")))

        # Update the display
        self.body_walker[:] = help_sections
        self.footer.set_text("General Help - Type 'help <command>' for detailed command help")

    def show_command_help(self, command_name):
        """Show detailed help for a specific command"""
        command_name = command_name.lower()

        command_help = CommandHelpTemplates.get_command_help()
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

    
    def get_pid(self):
        pid_file = '/tmp/Taskmasterd.pid'
        if os.path.exists(pid_file):
            with open(pid_file, 'r') as f:
                pid = f.read().strip()
                if pid.isdigit():
                    return int(pid)
        return None
    
    def handle_command(self, command):
        """Process and execute user commands"""
        global current_view, selected_program

        command = command.strip().lower()
        parts = command.split()

        if not parts:
            return

        cmd = parts[0]
        args = parts[1:] if len(parts) > 1 else []

        if cmd in ["quit", "exit"]:
            raise urwid.ExitMainLoop()
            
        elif cmd == "status":
            current_view = "status"
            self.programs = self.get_programs()
            self.refresh_view()
            
        elif cmd == "help":
            if args:
                self.show_command_help(args[0])
            else:
                current_view = "help"
                self.refresh_view()
                
        elif cmd == "detail" and args:
            program_name = args[0].strip()
            if program_name in self.programs:
                message = self.client.send_command(parts)
                self.show_detail(message['data'], program_name)
            else:
                self.footer.set_text(f"Error: Program '{program_name}' not found")
                
        elif cmd == "start" and args:
            self.handle_start_command(args[0])
            
        elif cmd == "stop" and args:
            self.handle_stop_command(args[0])
            
        elif cmd == "restart" and args:
            self.handle_restart_command(args[0])
            
        elif cmd == "pid":
            pid = self.get_pid()
            if pid:
                self.footer.set_text(f"Taskmaster daemon PID: {pid}")
            else:
                self.footer.set_text("Taskmaster daemon is not running or PID file not found.")
                
        elif cmd == "version":
            self.footer.set_text("Taskmaster Version: 1.1.1")
            
        elif cmd == "reload":
            self.handle_reload_command()
            
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
        

    def handle_start_command(self, program_name):
        """Handle the start command for a program"""
        if self.check_program_cmd(program_name):
            if program_name in self.programs and (
                self.programs[program_name]['status'] in ['running', 'starting']
            ):
                self.footer.set_text(f"Program '{program_name}' is already running.")
                return
                
            message = self.client.send_command(['start', program_name])
            self.programs[program_name] = message['data']
            current_view = "status"
            self.refresh_view()
            self.footer.set_text(f"\nStart command sent: {message['message']}")

    def handle_stop_command(self, program_name):
        """Handle the stop command for a program"""
        if self.check_program_cmd(program_name):
            if program_name not in self.programs or (
                self.programs[program_name]['status'] not in ['running', 'starting']
            ):
                self.footer.set_text(f"Program '{program_name}' is not running.")
                return
                
            message = self.client.send_command(['stop', program_name])
            self.programs[program_name] = message['data']
            current_view = "status"
            self.refresh_view()
            self.footer.set_text(f"\nStop command sent: {message['message']}")

    def handle_restart_command(self, program_name):
        """Handle the restart command for a program"""
        if self.check_program_cmd(program_name):
            was_running = True
            if program_name not in self.programs or (
                self.programs[program_name]['status'] not in ['running', 'starting']
            ):
                was_running = False
                
            message = self.client.send_command(['restart', program_name])
            self.programs[program_name] = message['data']
            current_view = "status"
            self.refresh_view()
            
            if not was_running and message['data']['status'] == 'starting':
                self.footer.set_text(
                    f"\nStart command sent: program '{program_name}' was not running, so it was started."
                )
            else:
                self.footer.set_text(f"\nRestart command sent: {message['message']}")

    def handle_reload_command(self):
        """Handle the reload command"""
        self.client.send_command('reload')
        time.sleep(1.5)
        self.reload_config()
        

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



