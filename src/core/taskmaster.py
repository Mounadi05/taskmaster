import sys,os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config import ConfigParser, ConfigValidator,ConfigManager




def main():
    
    config_file = "../../config_file/taskmaster.conf"
    manager = ConfigManager()
    manager.load_config(config_file)
    config = manager.get_config()

if __name__ == "__main__":
    sys.exit(main())