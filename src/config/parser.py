"""
Configuration file parser
Handles YAML parsing and initial structure validation
"""
import yaml
import os


class ConfigParser:
    
    def __init__(self):
        pass
    
    def parse_config_file(self, config_path):

        try:
            with open(config_path, 'r') as file:
                config = yaml.safe_load(file)
            return config
        except FileNotFoundError:
            raise FileNotFoundError(f"config file `{config_path}` not found")
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"YAML parsing error: {e}")
    
    
