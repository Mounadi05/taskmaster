"""Process worker module.

This module handles individual process execution and lifecycle management.
"""
import os
import sys
import pwd
import grp
import signal
import logging
import subprocess
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

class ProcessWorker:
    """Handles individual process lifecycle."""

    def __init__(self, name: str, config: Dict[str, Any], manager):
        self.name = name
        self.config = config
        self.manager = manager
        self.logger = logging.getLogger(f"worker.{name}")
        
        self.process: Optional[subprocess.Popen] = None
        self.start_time: Optional[datetime] = None
        self.stop_time: Optional[datetime] = None
        self.restart_count = 0
        self.status = "stopped"
        self.exit_code: Optional[int] = None
        self.pid: Optional[int] = None


    def start(self) -> bool:
        if self.is_running():
            self.logger.warning(f"Process {self.name} is already running")
            return False

        try:
            env = os.environ.copy()
            env.update(self.config.get('env', {}))

            uid = None
            gid = None
            if 'user' in self.config:
                try:
                    pw = pwd.getpwnam(self.config['user'])
                    uid = pw.pw_uid
                    gid = pw.pw_gid
                except KeyError:
                    self.logger.error(f"User {self.config['user']} not found")
                    return False

            if 'group' in self.config:
                try:
                    gr = grp.getgrnam(self.config['group'])
                    gid = gr.gr_gid
                except KeyError:
                    self.logger.error(f"Group {self.config['group']} not found")
                    return False

            # Set umask if specified
            if 'umask' in self.config:
                old_umask = os.umask(int(self.config['umask'], 8))

            # Create stdout/stderr file handles
            stdout = self._setup_log_file('stdout')
            stderr = self._setup_log_file('stderr')

            # Start the process
            self.process = subprocess.Popen(
                self.config['cmd'].split(),
                stdout=stdout,
                stderr=stderr,
                env=env,
                cwd=self.config.get('workingdir'),
                preexec_fn=lambda: self._preexec(uid, gid)
            )

            self.status = "starting"
            self.pid = self.process.pid
            self.start_time = datetime.now()
            self.exit_code = None

            self.logger.info(f"Started process {self.name} with PID {self.pid}")
            return True

        except Exception as e:
            self.logger.error(f"Error starting process {self.name}: {e}")
            self.status = "error"
            return False

      

    def stop(self) -> bool:
        """Stop the process."""

        if not self.is_running():
            return True

        try:

            stop_signal = getattr(signal, f"SIG{self.config.get('stopsignal', 'TERM')}")
            stop_time = self.config.get('stoptsecs', 10)

            os.kill(self.pid, stop_signal)
            self.status = "stopping"
            
            # Wait for process to stop
            try:
                print(f"Waiting for process {self.name} to stop... )")
                self.process.wait(timeout=stop_time)
                self.status = "stopped"
                self.stop_time = datetime.now()
                return True
            except subprocess.TimeoutExpired:
                # Force kill if timeout
                print(f"Process {self.name} did not stop in time, force killing with SIGKILL")
                os.kill(self.pid, signal.SIGKILL)
                self.process.wait()
                self.status = "stopped"
                self.stop_time = datetime.now()
                return True

        except ProcessLookupError:
            # Process already dead
            self.status = "stopped"
            self.stop_time = datetime.now()
            return True
        except Exception as e:
            print(f"Error stopping process {self.name}: {e}")
            self.logger.error(f"Error stopping process {self.name}: {e}")
            return False

    def restart(self) -> bool:
        success = self.start()
        if success:
            self.restart_count += 1
        return success

    def is_running(self) -> bool:
        if self.process is None or self.pid is None:
            return False

        try:
            os.kill(self.pid, 0)
            
            if self.process.poll() is not None:
                # Process has finished, collect exit status
                self.exit_code = self.process.returncode
                print(f"Process {self.name} with PID {self.pid} has exited with code {self.exit_code}")
                self.status = "exited"
                self.stop_time = datetime.now()
                return False
                
            if self.status == "starting" and self.start_time:
                start_duration = (datetime.now() - self.start_time).total_seconds()
                if start_duration >= self.config.get('startsecs', 1):
                    self.status = "running"
            
            return True
        except OSError:
            if self.status != "exited":
                self.status = "stopped"
            return False

    def get_status(self) -> Dict[str, Any]:
        """Get current process status."""
        status = {
            "name": self.name,
            "status": self.status,
            "pid": self.pid,
            "uptime": self._get_uptime(),
            "restarts": self.restart_count,
            "exitcode": self.exit_code,
            "cmd": self.config['cmd'],
            "config": {
                "numprocs": self.config.get('numprocs', 1),
                "autostart": self.config.get('autostart', False),
                "autorestart": self.config.get('autorestart', 'unexpected'),
                "startsecs": self.config.get('startsecs', 1),
                "stopsignal": self.config.get('stopsignal', 'TERM'),
                "stoptsecs": self.config.get('stoptsecs', 10),
                "exitcodes": self.config.get('exitcodes', [0]),
                "startretries": self.config.get('startretries', 3),
                "user": self.config.get('user'),
                "group": self.config.get('group'),
                "workingdir": self.config.get('workingdir','/tmp'),
                "env": self.config.get('env', {}),
                "umask": self.config.get('umask', '022'),
                "priority": self.config.get('priority', None),
            }
        }
        return status

    def update_config(self, new_config: Dict[str, Any]):
        """Update process configuration."""
        self.config = new_config

    def _preexec(self, uid: Optional[int], gid: Optional[int]):
        """Handle pre-execution setup."""
        # Set priority if specified
        priority = self.config.get('priority')
        if priority is not None:
            try:
                os.nice(priority)
            except OSError as e:
                self.logger.warning(f"Failed to set priority: {e}")

        # Set user and group if specified
        if gid is not None:
            try:
                os.setgid(gid)
            except OSError as e:
                self.logger.error(f"Failed to set group: {e}")
                sys.exit(1)

        if uid is not None:
            try:
                os.setuid(uid)
            except OSError as e:
                self.logger.error(f"Failed to set user: {e}")
                sys.exit(1)

    def _setup_log_file(self, stream: str) -> Optional[int]:
        """Set up log file for stdout/stderr."""
        config = self.config.get(stream)
        if not config:
            return subprocess.DEVNULL

        if isinstance(config, str):
            return open(config, 'a')
        elif isinstance(config, dict):
            return open(config['path'], 'a')
        
        return subprocess.DEVNULL

    def _get_uptime(self) -> str:
        """Get process uptime as string."""
        if not self.start_time or not self.is_running():
            return "0s"

        uptime = datetime.now() - self.start_time
        hours = uptime.seconds // 3600
        minutes = (uptime.seconds % 3600) // 60
        seconds = uptime.seconds % 60

        if hours > 0:
            return f"{hours}h {minutes}m"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
        
    def should_autorestart(self) -> bool:
                
        autorestart = self.config.get('autorestart', 'unexpected')
        exitcodes = self.config.get('exitcodes', [0])
        
        if autorestart == 'always':
            print(f"Process {self.name} should always restart.")
            self.restart()
        elif autorestart == 'unexpected' and self.exit_code not in exitcodes:
            return True
        
        return False