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

        # Use mock data if no process manager provided
        self.use_mock_data = process_manager is None

        self.setup_ui()

    def get_programs(self):
        """Get programs data from process manager or mock data"""
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
            urwid.Text(('title', "Taskmaster Control Shell - Help")),
            urwid.Divider(),
            urwid.Text("Available Commands:"),
            urwid.Divider(),
            urwid.Text("  status                 - Show status of all programs"),
            urwid.Text("  start <program>        - Start a program"),
            urwid.Text("  stop <program>         - Stop a program"),
            urwid.Text("  restart <program>      - Restart a program"),
            urwid.Text("  detail <program>       - Show detailed info for a program"),
            urwid.Text("  reload                 - Reload configuration"),
            urwid.Text("  help                   - Show this help"),
            urwid.Text("  quit                   - Exit taskmaster"),
            urwid.Divider(),
            urwid.Text("Program Names:"),
            urwid.Divider(),
        ]

        programs = self.get_programs()
        for name in programs.keys():
            self.body_walker.append(urwid.Text(f"  {name}"))

        self.body_walker.extend([
            urwid.Divider(),
            urwid.Text("Type 'status' to return to main view")
        ])

        self.footer.set_text("Help - Type any command to continue")

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


# For standalone execution (backward compatibility)
if __name__ == "__main__":
    # Initialize UI with mock data
    ui = TaskmasterUI()

    # Set initial focus to command input
    ui.main_frame.focus_position = 'footer'
    ui.footer_pile.focus_position = 1

    # Run the application
    loop = urwid.MainLoop(ui.main_frame, palette, unhandled_input=on_input)
    loop.run()
