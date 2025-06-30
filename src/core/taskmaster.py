import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config import ConfigParser, ConfigValidator, ConfigManager
import sys, socket, requests, json, argparse

class TaskmasterClient:
    """Client to communicate with Taskmaster server"""
    
    def __init__(self, host='localhost',port=1337):
        self.host = host
        self.port = port
    
    def send_http_command(self, command):
        """Send command via HTTP GET"""
        try:
            url = f"http://{self.host}:{self.port}/command"
            params = {'cmd': command}
            
            print(f"Sending HTTP GET request to {url} with command: {command}")
            response = requests.get(url, params=params, timeout=5)
            
            if response.status_code == 200:
                result = response.json()
                print(f"HTTP Response: {result['message']}")
                return True
            else:
                print(f"HTTP Error: {response.status_code} - {response.text}")
                return False
                
        except requests.RequestException as e:
            print(f"HTTP connection error: {e}")
            return False
    
    def send_socket_command(self, command):
        """Send command via Socket"""
        try:
            print(f"Connecting to socket server at {self.host}:{self.port}")
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(5)
            
            client_socket.connect((self.host, self.port))
            print(f"Sending socket command: {command}")
            
            client_socket.send(f"{command}\n".encode())
            response = client_socket.recv(1024).decode().strip()
            
            print(f"Socket Response: {response}")
            client_socket.close()
            return True
            
        except socket.error as e:
            print(f"Socket connection error: {e}")
            return False
    
    def send_command(self, command, method='http'):
        """Send command using specified method"""
        if method == 'http':
            return self.send_http_command(command)
        elif method == 'socket':
            return self.send_socket_command(command)
        else:
            print("Error: Invalid method. Use 'http' or 'socket'")
            return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Taskmasterctl - Command line client for Taskmaster server')

    
    Config = ConfigManager()
    server_config = Config.get_server_config()
    Config = ConfigManager()
    server_config = Config.get_server_config()
    method = server_config.get('type', 'socket')
    port = server_config.get('port', 1337 if method  == 'socket' else 4242)
    host = server_config.get('host', 'localhost')

    client = TaskmasterClient(host=host, port=port)
    success = client.send_command('start', method)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
