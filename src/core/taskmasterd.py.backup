

import socket ,threading ,time, logging, os, sys, signal, argparse
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config import ConfigManager
from process import ProcessManager, ProcessMonitor, ProcessCommands
from notifications import SMTPNotifier

old_pathfile = None
current_server = None

logging.basicConfig(
    filename='/tmp/taskamasterd.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class TaskmasterHTTPHandler(BaseHTTPRequestHandler):
    def __init__(self, server_instance, *args, **kwargs):
        self.taskmaster_server = server_instance
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)
        query_params = parse_qs(parsed_path.query)
        
        if parsed_path.path == '/command':
            cmd_list = query_params.get('cmd', [])
            if not cmd_list:
                self.send_error(400, "Missing command parameter")
                return
                
            command, args = parse_request(cmd_list)
            if not command:
                self.send_error(400, "Invalid command format")
                return

            try:
                response = process_command(command, args, self.taskmaster_server)

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())
            except Exception as e:
                self.send_error(500, f"Error processing command: {str(e)}")
        else:
            self.send_error(404, "Endpoint not found")
    
    def log_message(self, format, *args):
        """Override to suppress HTTP server logs"""
        pass

class SocketServer:
    """Socket server for handling raw socket connections"""
    
    def __init__(self, host='localhost', port=1337, taskmaster_server=None):
        self.host = host
        self.port = port
        self.socket = None
        self.running = False
        self.taskmaster_server = taskmaster_server
    
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
                
                try:
                    command, args = parse_request(data.split())
                    response = process_command(command, args, self.taskmaster_server)
                except Exception as e:
                    response = {
                        "status": "error",
                        "message": f"Error processing command: {str(e)}",
                        "timestamp": datetime.now().isoformat()
                    }
                
                client_socket.send(json.dumps(response).encode() + b'\n')
                
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
    
    def __init__(self, port, server_type='socket', config_manager=None,smtp_config=None):
        self.port = port
        self.server_type = server_type  # 'http', 'socket'
        self.http_server = None
        self.socket_server = None
        self.running = False
        self.process_manager = ProcessManager(config_manager, smtp_config=smtp_config)
        self.smtp_notifier = SMTPNotifier(smtp_config)
        self.process_commands = ProcessCommands(self.process_manager)
    
    def start(self):
        """Start HTTP and/or Socket servers based on server_type"""
        logging.info(f"Starting Taskmaster server with type: {self.server_type}, port: {self.port}")
        
        self.running = True
        
        # Start HTTP server if requested
        if self.server_type in ['http']:
            try:
                http_port = self.port if self.port else 4242
                handler = lambda *args: TaskmasterHTTPHandler(self, *args)
                self.http_server = HTTPServer(('localhost', http_port), handler)
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
                self.socket_server = SocketServer(port=socket_port, taskmaster_server=self)
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
    

def daemonize(working_directory='/tmp'):
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
    os.chdir(working_directory)
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

def signal_handler():
    global current_server
    
    if current_server:
        current_server.stop()
    
    if os.path.exists('/tmp/Taskmasterd.pid'):
        os.rmdir('/tmp/Taskmasterd.pid')
    sys.exit(0)


def parse_request(message:list):
    cmd = message[0]
    args = message[1:]
    print(f"Command: {cmd}, Args: {args}")
    return cmd, args
    
def process_command(command, args, server_instance=None):
        """Process the command and log it"""
        # Get or create the process_commands instance
        if not hasattr(process_command, 'process_commands'):
            if server_instance and hasattr(server_instance, 'process_commands'):
                process_command.process_commands = server_instance.process_commands
            else:
                # Create a new instance if server is not available
                process_command.process_commands = ProcessCommands(ProcessManager(None))

        response = None
        if command == 'alive':
            response = {
                "status": "success",
                "message": "Taskmaster server is alive",
                "timestamp": datetime.now().isoformat()
            }
        elif command == 'start':
            response = process_command.process_commands.start(args[0] if args else None)
        elif command == 'stop':
            response = process_command.process_commands.stop(args[0] if args else None)
        elif command == 'restart':
            response = process_command.process_commands.restart(args[0] if args else None)
        elif command == 'status':
             response = process_command.process_commands.status()
        elif command == 'detail':
            if args:
                response = process_command.process_commands.status(args[0])
        elif command == 'reload':
            response = reload_config(None, reload=True)
        else:
            response = {
                "status": "error",
                "message": "unknown command",
                "timestamp": datetime.now().isoformat()
            }
        
        # logging.info(response['message'])
        # print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {response['message']}")
        
        return response    


def reload_config(config,reload=False):
    global old_pathfile, current_server
    print(f"Reloading configuration...{old_pathfile}")
    if current_server:
        current_server.stop()
        time.sleep(0.5)
    if reload and old_pathfile:
        config = old_pathfile
    Config = ConfigManager(config)
    server_config = Config.get_server_config()
    type = server_config.get('type', 'socket')
    port = server_config.get('port', 1337)
    host = server_config.get('host', 'localhost')
    smtp_config = Config.get_smtp_config()

    server = TaskmasterServer(port=port, server_type=type, config_manager=Config,smtp_config=smtp_config)
    server.start()

def main():
    global old_pathfile
    """Main function"""
    parser = argparse.ArgumentParser(description='Taskmaster Server')
    parser.add_argument('-n', '--no-daemon', action='store_false', dest='daemon', default=True,
                        help='Run in the foreground (default: run as daemon)')
    parser.add_argument('-c', '--config', type=str, default='config_file/taskmaster.yaml',
                        help='Path to the configuration file')

    args = parser.parse_args()
    # Set up signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)



    if os.path.exists('/tmp/Taskmasterd.pid'):
        with open('/tmp/Taskmasterd.pid', 'r') as f:
            pid = int(f.read().strip())
        try:
            if os.getpgid(pid) >= 0:
                print(f"Taskmaster daemon is already running with PID {pid}...")
            sys.exit(1)
        except OSError:
            pass
    work_dir = os.getcwd()
    if args.daemon == False:
        print("Running in foreground mode")
    else:
        print("Running in daemon mode")
        daemonize(working_directory=work_dir)
        
    with open('/tmp/Taskmasterd.pid', 'w') as f:
        f.write(str(os.getpid()))
    
    if args.config:
        old_pathfile = args.config
    else:
        old_pathfile = 'config_file/taskmaster.yaml'

    reload_config(args.config)

    # Config = ConfigManager(args.config)
    # server_config = Config.get_server_config()
    # type = server_config.get('type', 'socket')
    # port = server_config.get('port', 1337)
    # host = server_config.get('host', 'localhost')
    # smtp_config = Config.get_smtp_config()

    # server = TaskmasterServer(port=port, server_type=type, config_manager=Config,smtp_config=smtp_config)
    # server.start()

if __name__ == "__main__":
    main()
    sys.exit(0)