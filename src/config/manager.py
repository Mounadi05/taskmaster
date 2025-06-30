
from .parser import ConfigParser
from .validator import ConfigValidator

class ConfigManager:    
    def __init__(self, config_file_path='config_file/taskmaster.yaml'):
        self.parser = ConfigParser(config_file_path)
        self.validator = ConfigValidator()
        
        self.programs = self.parser.get_program()
        self.server =  self.validator.validate_server(self.parser.get_server())
    
    def get_program_config(self, program_name):
        return self.programs.get(program_name)
    
    def get_all_programs(self):
        return self.programs
    
    def get_server_config(self):
        return  self.server
    
    def reload_config(self):
        """Reload configuration from file"""
        self.parser = ConfigParser(self.parser.config_path)
        self.server = self.parser.get_server_config()
        self.programs = self.parser.get_program_configs()
        
        is_valid, errors = self.validator.validate_config(self.programs)
        if not is_valid:
            raise ValueError(f"Configuration validation failed: {errors}")
        
        return True