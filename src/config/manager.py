"""Configuration management module for taskmaster."""
import os
import re
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

from .parser import ConfigParser
from .validator import ConfigValidator

class ConfigManager:
    """Manages configuration loading, validation, and access."""

    ENV_VAR_PATTERN = re.compile(r'\$\{([^}]+)\}|\$([a-zA-Z_][a-zA-Z0-9_]*)')
    
    def __init__(self, filepath='config_file/taskmaster.yaml'):
        """Initialize configuration manager."""
        self.parser = ConfigParser(filepath)
        self.validator = ConfigValidator()
        self.config: Dict[str, Any] = {}
        self.config_file = filepath        
        # Parse the configuration file
        success, result = self.parser.parse_file()
        if success:
            self.config = result
        else:
            pass
            
        self.programs = self.parser.get_programs()
        self.server = self.parser.get_server()
        print(f"Server configuration: {self.server}")

        
    def process_env_vars(self) -> None:
        """Process environment variables in configuration values."""
        def replace_env_vars(value: Any) -> Any:
            if isinstance(value, str):
                def replace_var(match):
                    var_name = match.group(1) or match.group(2)
                    return os.environ.get(var_name, '')
                return self.ENV_VAR_PATTERN.sub(replace_var, value)
            elif isinstance(value, dict):
                return {k: replace_env_vars(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [replace_env_vars(item) for item in value]
            return value
            
        self.config = replace_env_vars(self.config)
        
    def process_file_paths(self) -> None:
        if 'programs' in self.config:
            for prog_name, prog_config in self.config['programs'].items():
                if 'workingdir' in prog_config:
                    prog_config['workingdir'] = self._resolve_path(prog_config['workingdir'])
                    
                for stream in ['stdout', 'stderr']:
                    if stream in prog_config:
                        if isinstance(prog_config[stream], str):
                            prog_config[stream] = self._resolve_path(prog_config[stream])
                        elif isinstance(prog_config[stream], dict):
                            if 'path' in prog_config[stream]:
                                prog_config[stream]['path'] = self._resolve_path(prog_config[stream]['path'])
                                
    def resolve_path(self, path: str) -> str:
        """Resolve a path to its absolute form."""
        if not path:
            return path
            
        # Replace environment variables
        path = self.process_env_vars(path)
        
        # Convert to absolute path if relative
        if not os.path.isabs(path):
            config_dir = os.path.dirname(os.path.abspath(self.config_file))
            path = os.path.join(config_dir, path)
            
        return os.path.normpath(path)
        
    def get_program_config(self, program_name: str) -> Optional[Dict[str, Any]]:
        return self.config.get('programs', {}).get(program_name)
        
    def get_all_program_configs(self) -> Dict[str, Dict[str, Any]]:
        return self.config.get('programs', {})
        
    def get_server_config(self) -> Dict[str, Any]:
        return self.config.get('server', {})
        
    def get_smtp_config(self) -> Dict[str, Any]:
        return self.config.get('smtp', {})
        
    def get_webui_config(self) -> Dict[str, Any]:
        return self.config.get('webui', {})
        
    def get_raw_config(self) -> Dict[str, Any]:
        return self.config.copy()