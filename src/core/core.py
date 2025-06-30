

import socket ,threading ,time, logging, os, sys, signal, argparse
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config import ConfigManager

logging.basicConfig(
    filename='/tmp/taskamasterd.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class TaskmasterHTTPHandler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)
        query_params = parse_qs(parsed_path.query)
        
        if parsed_path.path == '/command':
            command = query_params.get('cmd', [None])[0]
            if command in ['start', 'stop']:
                response = self.process_command(command)
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())
            else:
                self.send_error(400, "Invalid command. Use 'start' or 'stop'")
        else:
            self.send_error(404, "Endpoint not found")

    
    def process_command(self, command):
        """Process the command and log it"""
        if command == 'start':
            message = "start done"
        elif command == 'stop':
            message = "stop done"
        else:
            message = "unknown command"
        
        logging.info(message)
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")
        
        return {"status": "success", "message": message, "timestamp": datetime.now().isoformat()}
    
    def log_message(self, format, *args):
        """Override to suppress HTTP server logs"""
        pass

class SocketServer:
    """Socket server for handling raw socket connections"""
    
    def __init__(self, host='localhost', port=1337):
        self.host = host
        self.port = port
        self.socket = None
        self.running = False
    
    def start(self):
        """Start the socket server"""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.socket.bind((self.host, self.port))
            self.socket.listen(5)
            self.running = True
            print(f"Socket server listening on {self.host}:{self.port}")
            
            while self.running:
                try:
                    client_socket, address = self.socket.accept()
                    client_thread = threading.Thread(
                        target=self.handle_client, 
                        args=(client_socket, address)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                except socket.error:
                    if self.running:
                        print("Socket error occurred")
                    break
                    
        except Exception as e:
            print(f"Socket server error: {e}")
        finally:
            if self.socket:
                self.socket.close()
    
    def handle_client(self, client_socket, address):
        """Handle individual client connections"""
        print(f"Socket connection from {address}")
        
        try:
            while True:
                data = client_socket.recv(1024).decode().strip()
                if not data:
                    break
                
                print(f"Received socket command: {data}")
                
                if data.lower() in ['start', 'stop']:
                    message = f"{data.lower()} done"
                    logging.info(message)
                    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")
                    response = f"{message}\n"
                else:
                    response = "Invalid command. Use 'start' or 'stop'\n"
                
                client_socket.send(response.encode())
                
        except Exception as e:
            print(f"Error handling socket client {address}: {e}")
        finally:
            client_socket.close()
            print(f"Socket connection closed for {address}")
    
    def stop(self):
        """Stop the socket server"""
        self.running = False
        if self.socket:
            self.socket.close()

class TaskmasterServer:
    """Main Taskmaster server that handles both HTTP and Socket connections"""
    
    def __init__(self, port, server_type='socket'):
        self.port = port
        self.server_type = server_type  # 'http', 'socket'
        self.http_server = None
        self.socket_server = None
        self.running = False
    
    def start(self):
        """Start HTTP and/or Socket servers based on server_type"""
        print(f"Server type: {self.server_type}")
        
        self.running = True
        
        # Start HTTP server if requested
        if self.server_type in ['http']:
            try:
                http_port = self.port if self.port else 4242
                self.http_server = HTTPServer(('localhost', http_port), TaskmasterHTTPHandler)
                http_thread = threading.Thread(target=self.http_server.serve_forever)
                http_thread.daemon = True
                http_thread.start()
                print(f"HTTP server started on http://localhost:{http_port}")
            except Exception as e:
                print(f"Failed to start HTTP server: {e}")
                if self.server_type == 'http':
                    return
        
        # Start Socket server if requested
        if self.server_type in ['socket']:
            try:
                socket_port = self.port if self.port else 1337
                self.socket_server = SocketServer(port=socket_port)
                socket_thread = threading.Thread(target=self.socket_server.start)
                socket_thread.daemon = True
                socket_thread.start()
                print(f"Socket server started on localhost:{socket_port}")
            except Exception as e:
                print(f"Failed to start Socket server: {e}")
                if self.server_type == 'socket':
                    return
        
        # Keep the main thread alive
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down servers...")
            self.stop()
    
    def stop(self):
        """Stop both servers"""
        self.running = False
        
        if self.http_server:
            self.http_server.shutdown()
            print("HTTP server stopped")
        
        if self.socket_server:
            self.socket_server.stop()
            print("Socket server stopped")

def daemonize():
    """Daemonize the current process"""
    try:
        # First fork
        pid = os.fork()
        if pid > 0:
            # Exit first parent
            sys.exit(0)
    except OSError as e:
        print(f"Fork #1 failed: {e}")
        sys.exit(1)
    
    # Decouple from parent environment
    os.chdir("/")
    os.setsid()
    os.umask(0)
    
    try:
        # Second fork
        pid = os.fork()
        if pid > 0:
            # Exit second parent
            sys.exit(0)
    except OSError as e:
        print(f"Fork #2 failed: {e}")
        sys.exit(1)
    
    # Redirect standard file descriptors
    sys.stdout.flush()
    sys.stderr.flush()
    
    # Redirect stdin, stdout, stderr to /dev/null
    with open('/dev/null', 'r') as dev_null_r:
        os.dup2(dev_null_r.fileno(), sys.stdin.fileno())
    
    with open('/dev/null', 'a+') as dev_null_w:
        os.dup2(dev_null_w.fileno(), sys.stdout.fileno())
        os.dup2(dev_null_w.fileno(), sys.stderr.fileno())

def signal_handler(signum, frame):
    """Handle termination signals"""
    print(f"\nReceived signal {signum}, shutting down...")
    sys.exit(0)

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Taskmaster Server')
    parser.add_argument('-d', '--daemon', action='store_true',
                        help='Run as daemon')
    
    args = parser.parse_args()
    # Set up signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
   
    if args.daemon:
        print(f"Starting server as daemon (type: {args.type})")
        daemonize()
        
        with open('/tmp/Taskmasterd.pid', 'w') as f:
            f.write(str(os.getpid()))
    Config = ConfigManager()
    server_config = Config.get_server_config()
    args.type = server_config.get('type', 'socket')
    args.port = server_config.get('port', 1337 if args.type == 'socket' else 4242)
    args.host = server_config.get('host', 'localhost')

    server = TaskmasterServer(port=args.port, server_type=args.type)
    server.start()



if __name__ == "__main__":
    main()
    sys.exit(0)