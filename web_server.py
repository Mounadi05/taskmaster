#!/usr/bin/env python3
"""
Taskmaster Web Server
Serves the web dashboard and handles API requests
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime
from urllib.parse import parse_qs, urlparse
from http.server import HTTPServer, SimpleHTTPRequestHandler

# Add parent directory to sys.path to import Taskmaster modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.config.manager import ConfigManager
from src.core.Taskmasterctl import TaskmasterClient

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class TaskmasterWebHandler(SimpleHTTPRequestHandler):
    """
    HTTP request handler for Taskmaster web interface
    """
    def __init__(self, *args, **kwargs):
        self.config = kwargs.pop('config', None)
        self.client = kwargs.pop('client', None)
        self.web_root = kwargs.pop('web_root', os.path.join(os.path.dirname(__file__), 'web'))
        super().__init__(*args, **kwargs)

    def log_message(self, format, *args):
        """Override to use our logger"""
        logger.info("%s - %s", self.address_string(), format % args)

    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        query_params = parse_qs(parsed_path.query)

        # API endpoint for Taskmaster commands
        if path == '/command':
            self.handle_command(query_params)
            return

        # Serve the taskmaster log directly
        if path == '/logs':
            try:

                with open('/tmp/taskmasterd.log', 'rb') as f:
                    log_data = f.read()
                self.send_response(200)
                self.send_header('Content-Type', 'text/plain; charset=utf-8')
                self.end_headers()
                self.wfile.write(log_data)
            except FileNotFoundError:
                self.send_error(404, 'Log file not found')
            except Exception as e:
                self.send_error(500, f'Error reading log file: {e}')
            return

        # Handle static files
        if path == '/':
            path = '/index.html'  # Default to index.html

        # Serve files from web directory
        file_path = os.path.join(self.web_root, path.lstrip('/'))
        
        # Set MIME types for specific file extensions
        content_type = self.guess_type(file_path)

        try:
            with open(file_path, 'rb') as f:
                self.send_response(200)
                self.send_header('Content-type', content_type)
                self.end_headers()
                self.wfile.write(f.read())
        except FileNotFoundError:
            self.send_error(404, 'File not found')
        except PermissionError:
            self.send_error(403, 'Permission denied')
        except Exception as e:
            self.send_error(500, f'Error: {str(e)}')

    def handle_command(self, query_params):
        """Handle Taskmaster API commands"""
        cmd_list = query_params.get('cmd', [])
        
        if not cmd_list:
            self.send_error(400, 'Missing command parameter')
            return
        
        cmd_parts = cmd_list[0].split()
        
        try:
            # Forward command to Taskmaster server
            response = self.client.send_command(cmd_parts)
            
            if not response:
                response = {
                    'status': 'error',
                    'message': 'Failed to communicate with Taskmaster server',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Send response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            logger.error(f"Error processing command: {str(e)}")
            error_response = {
                'status': 'error',
                'message': f'Error processing command: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(error_response).encode())

    def guess_type(self, path):
        """Guess the MIME type based on file extension"""
        base, ext = os.path.splitext(path)
        if ext == '.html':
            return 'text/html'
        elif ext == '.css':
            return 'text/css'
        elif ext == '.js':
            return 'application/javascript'
        elif ext in ('.jpg', '.jpeg'):
            return 'image/jpeg'
        elif ext == '.png':
            return 'image/png'
        elif ext == '.gif':
            return 'image/gif'
        elif ext == '.ico':
            return 'image/x-icon'
        elif ext == '.svg':
            return 'image/svg+xml'
        elif ext == '.json':
            return 'application/json'
        return 'application/octet-stream'

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Taskmaster Web Server')
    parser.add_argument('-c', '--config', type=str, default='config_file/master.yaml',
                        help='Path to the configuration file')
    args = parser.parse_args()
    
    try:
        # Load configuration
        config = ConfigManager(args.config)
        webui_config = config.get_webui_config()
        server_config = config.get_server_config()
        
        # Setup TaskmasterClient
        client = TaskmasterClient(
            method=server_config.get('type', 'socket'),
            port=server_config.get('port', 1337),
            host=server_config.get('host', 'localhost')
        )
        # Check if Taskmaster server is running
        try:
            response = client.send_command('alive')
            if not response or response.get('status') != 'success':
                logger.error("Taskmaster server is not running or not responding!")
                sys.exit(1)
        except Exception as e:
            logger.error(f"Failed to connect to Taskmaster server: {str(e)}")
            sys.exit(1)
        
        # Determine web server host and port
        web_host = webui_config.get('host', '127.0.0.1')
        web_port = webui_config.get('port', 8080)
        
        # Create custom handler with access to config and client
        handler = lambda *args, **kwargs: TaskmasterWebHandler(*args, config=config, client=client, **kwargs)
        
        # Start web server
        web_server = HTTPServer((web_host, web_port), handler)
        logger.info(f"Starting Taskmaster Web Server on http://{web_host}:{web_port}")
        logger.info(f"Connected to Taskmaster server at {server_config.get('host')}:{server_config.get('port')} using {server_config.get('type')}")
        
        try:
            web_server.serve_forever()
        except KeyboardInterrupt:
            logger.info("Stopping Taskmaster Web Server...")
            web_server.server_close()
    except Exception as e:
        logger.error(f"Error starting Taskmaster Web Server: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
