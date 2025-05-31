import socket
import os
import mimetypes
from datetime import datetime

HOST = 'localhost'
PORT = 8080
WWW_ROOT = './www'
LOG_FILE = 'server.log'
  
def log_request(method, path, status):
    """Log the HTTP request with timestamp, method, path, and status code to both console and file."""
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{now}] {method} {path} => {status}"
    print(log_entry)
    try:
        with open(LOG_FILE, "a") as log_file:
            log_file.write(log_entry + "\n")
    except Exception as e:
        print(f"[!] Failed to write to log file: {e}")

def get_mime_type(file_path):
    """Return the MIME type of a file based on its extension."""
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type or 'application/octet-stream'

def handle_request(client_socket):
    """Handle incoming HTTP requests."""
    try:
        request = client_socket.recv(1024).decode('utf-8')
        if not request:
            return

        request_line = request.split('\n')[0]
        try:
            method, path, _ = request_line.split()
        except ValueError:
            bad_request_response = (
                "HTTP/1.1 400 Bad Request\r\n"
                "Content-Type: text/html\r\n\r\n"
                "<h1>400 Bad Request</h1><p>Malformed request line.</p>"
            ).encode('utf-8')
            client_socket.sendall(bad_request_response)
            log_request('UNKNOWN', 'UNKNOWN', 400)
            client_socket.close()
            return

        if method != 'GET':
            client_socket.sendall(b"HTTP/1.1 405 Method Not Allowed\r\nContent-Type: text/html\r\n\r\n<h1>405 Method Not Allowed</h1><p>Only GET is supported.</p>")
            log_request(method, path, 405)
            client_socket.close()
            return

        if path == '/':
            path = '/index.html'

        file_path = os.path.join(WWW_ROOT, path.lstrip('/'))

        if os.path.isfile(file_path):
            try:
                with open(file_path, 'rb') as f:
                    content = f.read()
                mime_type = get_mime_type(file_path)
                response_headers = (
                    f"HTTP/1.1 200 OK\r\n"
                    f"Content-Type: {mime_type}\r\n"
                    f"Content-Length: {len(content)}\r\n"
                    f"Connection: close\r\n\r\n"
                ).encode('utf-8')
                client_socket.sendall(response_headers + content)
                log_request(method, path, 200)
            except Exception as e:
                internal_error_response = (
                    "HTTP/1.1 500 Internal Server Error\r\n"
                    "Content-Type: text/html\r\n\r\n"
                    f"<h1>500 Internal Server Error</h1><p>{str(e)}</p>"
                ).encode('utf-8')
                client_socket.sendall(internal_error_response)
                log_request(method, path, 500)
        else:
            not_found_response = (
                "HTTP/1.1 404 Not Found\r\n"
                "Content-Type: text/html\r\n\r\n"
                "<h1>404 Not Found</h1><p>The page does not exist.</p>"
            ).encode('utf-8')
            client_socket.sendall(not_found_response)
            log_request(method, path, 404)
    except Exception as e:
        internal_error_response = (
            "HTTP/1.1 500 Internal Server Error\r\n"
            "Content-Type: text/html\r\n\r\n"
            f"<h1>500 Internal Server Error</h1><p>{str(e)}</p>"
        ).encode('utf-8')
        client_socket.sendall(internal_error_response)
        log_request('UNKNOWN', 'UNKNOWN', 500)
    finally:
        client_socket.close()

def start_server():
    """Start the HTTP server."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((HOST, PORT))
        server_socket.listen(5)
        print(f"[*] Server listening on http://{HOST}:{PORT}")

        while True:
            try:
                client_socket, _ = server_socket.accept()
                handle_request(client_socket)
            except KeyboardInterrupt:
                print("\n[*] Server shutting down.")
                break
            except Exception as e:
                print(f"[!] Error: {e}")

if __name__ == '__main__':
    start_server()