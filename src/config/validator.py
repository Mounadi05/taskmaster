
class ConfigValidator:
    
    def __init__(self):
        self.errors = []
    
    def validate_config(self, config):
        self.errors = []
        
        if not config:
            self.errors.append("config file `taskmaster.conf` is empty")
            return False, self.errors
        
        if 'programs' not in config:
            self.errors.append("Missing 'programs' section in configuration")
            return False, self.errors
        
        programs = config['programs']
        if not isinstance(programs, dict):
            self.errors.append("'programs' must be a dictionary/object")
            return False, self.errors
        
        if len(programs) == 0:
            self.errors.append("No programs defined in 'programs' section")
            return False, self.errors
        
        for program_name, program_details in programs.items():
            if not isinstance(program_details, dict):
                self.errors.append(f"Program '{program_name}' must be a dictionary/object")
                continue
                
            if 'cmd' not in program_details:
                self.errors.append(f"Program '{program_name}' missing required 'cmd' attribute")
            elif not program_details['cmd'] or not isinstance(program_details['cmd'], str):
                self.errors.append(f"Program '{program_name}' 'cmd' must be a non-empty string")
        
        return (len(self.errors) == 0), self.errors
    
 
            
    def validate_server(self, server):
        if not server:
            return self.generate_config_server()
        
        
        if 'type' not in server:
            print("Error: Missing 'type' in server communication configuration")
            raise ValueError("Missing 'type' in server communication configuration")
            exit(1)
        
        comm_type = server['type']
        
        if 'port' not in server:
            # Set default port based on type
            if comm_type == 'socket':
                server['port'] = 1337
            elif comm_type == 'http':
                server['port'] = 4242
            else:
               raise ValueError(f"Invalid server type '{comm_type}'. Must be 'socket' or 'http'.")
        
        return server

    def generate_config_server(self):
        """Generate a default configuration dictionary"""
        return {
            'server': {
                'type': 'socket',
                'port': 1337,
                'host': 'localhost'
                }
            }