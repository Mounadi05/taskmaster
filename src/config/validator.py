"""Configuration validation module for taskmaster."""
import os
import re
from typing import Dict, List, Tuple, Union, Any

from .defaults import (
    PROGRAM_DEFAULTS,
    SERVER_DEFAULTS,
    SMTP_DEFAULTS,
    WEBUI_DEFAULTS
)

class ConfigValidator:
    """Validates taskmaster configuration files."""
    
    def __init__(self):
        self.errors = []
        
    def validate_config(self, config: dict) -> Tuple[bool, List[str]]:
        """Validate the complete configuration."""
        self.errors = []
        
        if not config:
            self.errors.append("Configuration is empty")
            return False, self.errors
            
        # Validate required sections
        if 'programs' not in config:
            self.errors.append("Missing required 'programs' section")
            return False, self.errors
            
      
        
        return len(self.errors) == 0, self.errors
        
    def validate_programs(self, programs: dict) -> None:
        """Validate the programs section of the configuration."""
        if not isinstance(programs, dict):
            self.errors.append("'programs' section must be a dictionary")
            return
            
        if not programs:
            self.errors.append("No programs defined in configuration")
            return
            
        for program_name, config in programs.items():
            self._validate_program_config(program_name, config)
    
    def validate_program_config(self, name: str, config: dict) -> None:
        """Validate a single program's configuration."""
        if not isinstance(config, dict):
            self.errors.append(f"Program '{name}' configuration must be a dictionary")
            return
            
        for key, schema in PROGRAM_DEFAULTS.items():
            value = config.get(key, schema.get('default'))
            
            # Check required fields
            if schema.get('required', False) and value is None:
                self.errors.append(f"Program '{name}' missing required field '{key}'")
                continue
                
            # Skip validation if value is None and field is optional
            if value is None:
                continue
                
            # Type validation
            if not isinstance(value, schema['type']):
                self.errors.append(
                    f"Program '{name}' field '{key}' must be of type {schema['type'].__name__}"
                )
                continue
                
            # Numeric range validation
            if isinstance(value, (int, float)):
                min_val = schema.get('min')
                max_val = schema.get('max')
                if min_val is not None and value < min_val:
                    self.errors.append(
                        f"Program '{name}' field '{key}' must be >= {min_val}"
                    )
                if max_val is not None and value > max_val:
                    self.errors.append(
                        f"Program '{name}' field '{key}' must be <= {max_val}"
                    )
                    
            if 'choices' in schema and value not in schema['choices']:
                self.errors.append(
                    f"Program '{name}' field '{key}' must be one of: {', '.join(schema['choices'])}"
                )
                
            if 'pattern' in schema and isinstance(value, str):
                if not re.match(schema['pattern'], value):
                    self.errors.append(
                        f"Program '{name}' field '{key}' must match pattern {schema['pattern']}"
                    )
                    
            if isinstance(value, list) and 'element_type' in schema:
                if not all(isinstance(x, schema['element_type']) for x in value):
                    self.errors.append(
                        f"Program '{name}' field '{key}' must be a list of {schema['element_type'].__name__}"
                    )
                    
            if key == 'workingdir' and value is not None:
                if not os.path.isabs(value):
                    self.errors.append(
                        f"Program '{name}' working directory must be an absolute path"
                    )
                elif not os.path.exists(value):
                    self.errors.append(
                        f"Program '{name}' working directory '{value}' does not exist"
                    )
    
    def validate_server(self, config: dict) -> None:
        """Validate server configuration section."""
        if not config:  # Server section is optional
            return
            
        self._validate_section('server', config, SERVER_DEFAULTS)
    
    def validate_smtp(self, config: dict) -> None:
        """Validate SMTP configuration section."""
        if not config:  # SMTP section is optional
            return
            
        self._validate_section('smtp', config, SMTP_DEFAULTS)
    
    def validate_webui(self, config: dict) -> None:
        """Validate Web UI configuration section."""
        if not config:  # Web UI section is optional
            return
            
        self._validate_section('webui', config, WEBUI_DEFAULTS)
    
    def _validate_section(self, section_name: str, config: dict, schema: dict) -> None:
        """Generic section validator using schema."""
        for key, field_schema in schema.items():
            value = config.get(key, field_schema.get('default'))
            
            if value is None and not field_schema.get('required', False):
                continue
                
            if not isinstance(value, field_schema['type']):
                self.errors.append(
                    f"{section_name}.{key} must be of type {field_schema['type'].__name__}"
                )
                continue
                
            if isinstance(value, (int, float)):
                min_val = field_schema.get('min')
                max_val = field_schema.get('max')
                if min_val is not None and value < min_val:
                    self.errors.append(
                        f"{section_name}.{key} must be >= {min_val}"
                    )
                if max_val is not None and value > max_val:
                    self.errors.append(
                        f"{section_name}.{key} must be <= {max_val}"
                    )
                    
            if 'choices' in field_schema and value not in field_schema['choices']:
                self.errors.append(
                    f"{section_name}.{key} must be one of: {', '.join(field_schema['choices'])}"
                )