
from .parser import ConfigParser
from .validator import ConfigValidator


class ConfigManager:    
    def __init__(self):
        self.parser = ConfigParser()
        self.validator = ConfigValidator()
        self.config = None
    
    def load_config(self, config_path):
        try:
            config = self.parser.parse_config_file(config_path)
            is_valid, errors = self.validator.validate_config(config)
            
            if is_valid:
                self.config = config
                return True, config, []
            else:
                return False, None, errors
                
        except (FileNotFoundError, Exception) as e:
            return False, None, [str(e)]
    
    def get_config(self):
        return self.config
    
    def reload_config(self, config_path):
        return self.load_config(config_path)
