"""Configuration parser module for taskmaster.

This module handles YAML configuration file parsing and provides methods
to access different sections of the configuration.
"""

import os
import yaml
from typing import Dict, Any, Optional, Tuple, List
from pathlib import Path

from .validator import ConfigValidator
from .defaults import (
    PROGRAM_DEFAULTS,
    SERVER_DEFAULTS,
    SMTP_DEFAULTS,
    WEBUI_DEFAULTS
)


class ConfigError(Exception):
    pass


class ConfigParser:

    def __init__(self, filepath):
        self.validator = ConfigValidator()
        self.config = {}
        self._parse_errors: List[str] = []
        self.filepath = filepath

    def parse_file(self):
     
        self._parse_errors = []

        try:
            if not os.path.exists(self.filepath):
                raise ConfigError(f"Configuration file not found: {self.filepath}")

            if not os.access(self.filepath, os.R_OK):
                raise ConfigError(f"Configuration file is not readable: {self.filepath}")

            with open(self.filepath, 'r') as f:
                try:
                    config = yaml.safe_load(f)
                except yaml.YAMLError as e:
                    raise ConfigError(f"Invalid YAML format: {self._format_yaml_error(e)}")

            if not config:
                raise ConfigError("Configuration file is empty")

            if not isinstance(config, dict):
                raise ConfigError("Configuration must be a dictionary")

            # Apply defaults and validate structure
            self.config = self._apply_defaults(config)

            # Validate configuration
            is_valid, errors = self.validator.validate_config(self.config)
            if not is_valid:
                self._parse_errors.extend(errors)
                raise ConfigError("Configuration validation failed")

            return True, self.config

        except ConfigError as e:
            return False, {
                "error": str(e),
                "details": self._parse_errors if self._parse_errors else None
            }
        except Exception as e:
            return False, {"error": f"Unexpected error: {str(e)}"}

    def _format_yaml_error(self, error: yaml.YAMLError) -> str:
        """Format YAML error message."""
        if hasattr(error, 'problem_mark'):
            mark = error.problem_mark
            return f"line {mark.line + 1}, column {mark.column + 1}: {error.problem}"
        return str(error)

    def _apply_defaults(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply default values to missing configuration options."""
        result = config.copy()

        # Ensure programs section exists
        if 'programs' not in result:
            result['programs'] = {}

        # Apply program defaults
        for prog_name, prog_config in result['programs'].items():
            if not isinstance(prog_config, dict):
                self._parse_errors.append(f"Program '{prog_name}' configuration must be a dictionary")
                continue

            # Apply defaults for each program
            for key, schema in PROGRAM_DEFAULTS.items():
                if key not in prog_config and 'default' in schema:
                    prog_config[key] = schema['default']

            # Process sub-schemas
            self._process_sub_schemas(prog_config, prog_name)

        # Apply section defaults
        self._apply_section_defaults(result, 'server', SERVER_DEFAULTS)
        self._apply_section_defaults(result, 'smtp', SMTP_DEFAULTS)
        self._apply_section_defaults(result, 'webui', WEBUI_DEFAULTS)

        return result

    def _process_sub_schemas(self, config: Dict[str, Any], context: str) -> None:
        """Process nested configuration schemas."""
        for key, value in config.items():
            if isinstance(value, dict):
                schema = PROGRAM_DEFAULTS.get(key, {}).get('sub_schema')
                if schema:
                    for sub_key, sub_schema in schema.items():
                        if sub_schema.get('required', False) and sub_key not in value:
                            self._parse_errors.append(
                                f"Missing required field '{sub_key}' in {context}.{key}"
                            )
                        elif 'default' in sub_schema and sub_key not in value:
                            value[sub_key] = sub_schema['default']

    def _apply_section_defaults(self, config: Dict[str, Any], section: str, defaults: Dict[str, Any]) -> None:
        """Apply defaults to a configuration section."""
        if section not in config:
            config[section] = {}

        section_config = config[section]
        if not isinstance(section_config, dict):
            self._parse_errors.append(f"'{section}' section must be a dictionary")
            config[section] = {}
            section_config = config[section]

        for key, schema in defaults.items():
            if key not in section_config and 'default' in schema:
                section_config[key] = schema['default']

    def get_parse_errors(self) -> List[str]:
        return self._parse_errors.copy()

    def get_programs(self): 
        return self.config.get('programs', {})

    def get_server(self) -> Dict[str, Any]:
        # Remove debug print and return server configuration with defaults
        return self.config.get('server', {
            'type': 'socket',
            'port': 1337,
            'host': 'localhost'
        })

    def get_smt(self) -> Dict[str, Any]:
        return self.config.get('smtp', {})

    def get_webui(self) -> Dict[str, Any]:
        return self.config.get('webui', {})
