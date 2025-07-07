"""UI display templates for the Taskmaster interface"""

from typing import Dict, List, Any
import urwid

class UITemplates:
    @staticmethod
    def create_program_section(title: str, programs: List[str], color: str = 'normal') -> List[urwid.Widget]:
        """Create a section of program names with a title"""
        if not programs:
            return []
        
        widgets = [
            urwid.Text((color, f"  {title}:")),
        ]
        for name in sorted(programs):
            widgets.append(urwid.Text(f"    {name}"))
        return widgets

    @staticmethod
    def create_program_details_view(data: Dict[str, Any], program_name: str) -> List[urwid.Widget]:
        """Create the program details view"""
        basic_info = [
            urwid.Text(('title', "Program Details")),
            urwid.Divider(),
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
            urwid.Divider()
        ]

        process_control = [
            urwid.Text(('header', "Process Control:")),
            urwid.Text(f"Autostart: {data[program_name]['config'].get('autostart', 'N/A')}"),
            urwid.Text(f"Autorestart: {data[program_name]['config'].get('autorestart', 'N/A')}"),
            urwid.Text(f"Exit Codes: {data[program_name]['config'].get('exitcodes', 'N/A')}"),
            urwid.Text(f"Start Retries: {data[program_name]['config'].get('startretries', 'N/A')}"),
            urwid.Text(f"Start Time: {data[program_name]['config'].get('startsecs', 'N/A')} seconds"),
            urwid.Text(f"Stop Signal: {data[program_name]['config'].get('stopsignal', 'N/A')}"),
            urwid.Text(f"Stop Time: {data[program_name]['config'].get('stoptsecs', 'N/A')} seconds"),
            urwid.Divider()
        ]

        logging_info = []
        stdout = data.get('stdout', {})
        if isinstance(stdout, dict):
            logging_info.extend([
                urwid.Text(('header', "Stdout Configuration:")),
                urwid.Text(f"  Path: {stdout.get('path', 'N/A')}"),
                urwid.Text(f"  Max Bytes: {stdout.get('maxbytes', 'N/A')}"),
                urwid.Divider()
            ])
        else:
            logging_info.extend([
                urwid.Text(f"Stdout: {stdout}"),
                urwid.Divider()
            ])

        # Navigation footer
        navigation = [
            urwid.Text(('info', "Press 'status' to return to the main view"))
        ]

        return basic_info + process_control + logging_info + navigation

    @staticmethod
    def create_status_view(programs: Dict[str, Any]) -> List[urwid.Widget]:
        """Create the status overview view"""
        header = [
            urwid.Text(('title', "Program Status Overview")),
            urwid.Divider(),
            urwid.Text(('header', f"{'Name':<15} {'Status':<10} {'PID':<8} {'Uptime':<10} {'Restarts':<8} {'CMD':<40}")),
            urwid.Divider('-')
        ]

        program_lines = []
        for name, info in programs.items():
            status_color = UITemplates.get_status_color(info['status'])
            line = f"{name:<15} {info['status']:<10} {str(info['pid'] or '-'):<8} {info['uptime']:<10} {info['restarts']:<8} {info['cmd']:<40}"
            program_lines.append(urwid.Text((status_color, line)))

        return header + program_lines + [urwid.Divider()]

    @staticmethod
    def get_status_color(status: str) -> str:
        """Get the color for a program status"""
        colors = {
            'running': 'success',
            'stopped': 'warning',
            'fatal': 'error',
            'starting': 'info'
        }
        return colors.get(status, 'normal')
