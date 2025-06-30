"""Configuration file parser for Taskmaster.

This module handles YAML configuration file parsing and provides methods
to access different sections of the configuration.
"""

import yaml ,os


class ConfigParser:
    
    def __init__(self, config_path='config_file/taskmaster.yaml'):
        """Initialize the ConfigParser with a default configuration path."""
        self.config_path = config_path
        self.config = self.parse_config_file()

    def parse_config_file(self):
        try:
            with open(self.config_path, 'r') as file:
                config = yaml.safe_load(file)
            return config
        except FileNotFoundError:
            raise FileNotFoundError(f"config file `{self.config_path}` not found")
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"YAML parsing error: {e}")
    
    def get_server(self):
        return self.config['server']
    
    def get_program(self):
        return self.config.get('programs',{})   
    