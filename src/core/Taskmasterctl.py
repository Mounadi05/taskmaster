import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config import ConfigParser, ConfigValidator, ConfigManager
import sys, socket, requests, json, argparse

class TaskmasterClient:
    """Client to communicate with Taskmaster server"""
    
    def __init__(self,method, port, host):
        self.method = method
        self.port = port
        self.host = host
    def send_http_command(self, command):
        """Send command via HTTP GET"""
        try:
            
            url = f"http://{self.host}:{self.port}/command"
            params = {'cmd': command}
            response = requests.get(url, params=params, timeout=5)
            
            if response.status_code == 200:
                result = response.json()
                return result
            else:
                return False
                
        except requests.RequestException as e:
            return False
    
    def send_socket_command(self, command):
        """Send command via Socket"""
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(5)
            
            client_socket.connect((self.host, self.port))

            client_socket.send(f"{command}\n".encode())
            response_text = client_socket.recv(4092).decode().strip()
            client_socket.close()
            try:
                return json.loads(response_text)
            except json.JSONDecodeError:
                return {"status": "error", "message": f"Invalid response: {response_text}"}
            
        except socket.error as e:
            print(f"Socket connection error: {e}")
            return {"status": "error", "message": f"Connection error: {e}"}

    
    def send_command(self, command):
        if self.method == 'http':
            return self.send_http_command(command)
        elif self.method == 'socket':
            return self.send_socket_command(command)
        else:
            print("Error: Invalid method. Use 'http' or 'socket'")
            return False

