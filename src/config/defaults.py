"""Default configuration values and validation schemas for taskmaster."""
import os
import pwd
import grp
from typing import Any, Dict, List

def get_supported_signals() -> List[str]:
    """Get list of supported signals."""
    return ['TERM', 'HUP', 'INT', 'QUIT', 'KILL', 'USR1', 'USR2']

def validate_user(username: str) -> bool:
    """Validate if user exists."""
    try:
        pwd.getpwnam(username)
        return True
    except KeyError:
        return False

def validate_group(groupname: str) -> bool:
    """Validate if group exists."""
    try:
        grp.getgrnam(groupname)
        return True
    except KeyError:
        return False

# Program configuration defaults and validation rules
PROGRAM_DEFAULTS = {
    'cmd': {
        'required': True,
        'type': str,
        'help': 'The command to run'
    },
    'numprocs': {
        'default': 1,
        'type': int,
        'min': 0,
        'max': 100,
        'help': 'Number of processes to spawn'
    },
    'umask': {
        'default': '022',
        'type': str,
        'pattern': r'^[0-7]{3}$',
        'help': 'File mode creation mask'
    },
    'workingdir': {
        'default': None,
        'type': str,
        'validate': os.path.exists,
        'help': 'Directory to change to before executing'
    },
    'autostart': {
        'default': False,
        'type': bool,
        'help': 'Start automatically when taskmaster starts'
    },
    'autorestart': {
        'default': 'never',
        'type': str,
        'choices': ['always', 'never', 'unexpected'],
        'help': 'Restart policy (always, never, unexpected)'
    },
    'exitcodes': {
        'default': [0],
        'type': list,
        'element_type': int,
        'help': 'Expected exit codes'
    },
    'startretries': {
        'default': 3,
        'type': int,
        'min': 0,
        'help': 'Number of retries before giving up'
    },
    'startsecs': {
        'default': 1,
        'type': int,
        'min': 0,
        'help': 'Program needs to stay running for this many seconds to consider the start successful'
    },
    'stopsignal': {
        'default': 'TERM',
        'type': str,
        'choices': get_supported_signals(),
        'help': 'Signal to use to kill the program'
    },
    'stoptsecs': {
        'default': 10,
        'type': int,
        'min': 0,
        'help': 'Number of seconds to wait for stop before killing'
    },
    'stdout': {
        'default': None,
        'type': (str, dict),
        'help': 'Stdout log file path or configuration',
        'sub_schema': {
            'path': {'type': str, 'required': True},
            'maxbytes': {'type': int, 'default': 0},
            'backups': {'type': int, 'default': 0}
        }
    },
    'stderr': {
        'default': None,
        'type': (str, dict),
        'help': 'Stderr log file path or configuration',
        'sub_schema': {
            'path': {'type': str, 'required': True},
            'maxbytes': {'type': int, 'default': 0},
            'backups': {'type': int, 'default': 0}
        }
    },
    'env': {
        'default': {},
        'type': dict,
        'help': 'Environment variables to set'
    },
    'user': {
        'default': None,
        'type': str,
        'validate': validate_user,
        'help': 'User to run as'
    },
    'group': {
        'default': None,
        'type': str,
        'validate': validate_group,
        'help': 'Group to run as'
    },
    'priority': {
        'default': 999,
        'type': int,
        'min': -20,
        'max': 19,
        'help': 'Process priority (niceness)'
    }
}

# Server configuration defaults
SERVER_DEFAULTS = {
    'type': {
        'default': 'socket',
        'type': str,
        'choices': ['socket', 'http'],
        'help': 'Server communication type'
    },
    'port': {
        'default': 1337,
        'type': int,
        'min': 1,
        'max': 65535,
        'help': 'Server port number'
    },
    'host': {
        'default': 'localhost',
        'type': str,
        'help': 'Server hostname or IP address'
    }
}

# SMTP notification defaults
SMTP_DEFAULTS = {
    'enabled': {
        'default': False,
        'type': bool,
        'help': 'Enable SMTP notifications'
    },
    'server': {
        'default': 'localhost',
        'type': str,
        'help': 'SMTP server hostname'
    },
    'port': {
        'default': 587,
        'type': int,
        'min': 1,
        'max': 65535,
        'help': 'SMTP server port'
    },
    'use_tls': {
        'default': True,
        'type': bool,
        'help': 'Use TLS for SMTP connection'
    },
    'username': {
        'default': None,
        'type': str,
        'help': 'SMTP authentication username'
    },
    'password': {
        'default': None,
        'type': str,
        'help': 'SMTP authentication password'
    }
}

# Web UI configuration defaults
WEBUI_DEFAULTS = {
    'enabled': {
        'default': False,
        'type': bool,
        'help': 'Enable web interface'
    },
    'host': {
        'default': '127.0.0.1',
        'type': str,
        'help': 'Web interface bind address'
    },
    'port': {
        'default': 8080,
        'type': int,
        'min': 1,
        'max': 65535,
        'help': 'Web interface port number'
    },
    'auth': {
        'default': {
            'enabled': True,
            'username': 'admin',
            'password': 'changeme'
        },
        'type': dict,
        'help': 'Web interface authentication settings',
        'sub_schema': {
            'enabled': {'type': bool, 'default': True},
            'username': {'type': str, 'default': 'mounadi05'},
            'password': {'type': str, 'default': 'ytaya07'}
        }
    }
}