# COS 460/540 - Project 2: Simple HTTP Server
# Implements a basic, multi-threaded HTTP/1.1 server using only the standard socket library.
import socket
import threading
import sys
import os
import urllib.parse
from email.utils import formatdate

# Configuration and Utilities
SERVER_NAME = "BobsDiscountServer/2.1"
DEFAULT_MIME_TYPE = "application/octet-stream"

# Maps file extensions to the required Content-Type header.
MIME_TYPES = {
    "html": "text/html",
    "htm": "text/html",
    "css": "text/css",
    "js": "application/javascript",
    "json": "application/json",
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "gif": "image/gif",
    "txt": "text/plain",
}

def get_mime_type(file_path):
    """Determines the Content-Type based on the file extension."""
    if '.' in file_path:
        ext = file_path.split('.')[-1].lower()
        return MIME_TYPES.get(ext, DEFAULT_MIME_TYPE)
    return DEFAULT_MIME_TYPE

# HTTP Response Generation
def format_http_response(status_code, status_text, content_type, content_body):
    """Assembles the full HTTP response as bytes."""
    
    content_length = len(content_body)
    date_header = formatdate(timeval=None, localtime=False, usegmt=True)

    # 1. Status Line (e.g., HTTP/1.1 200 OK)
    response_line = f"HTTP/1.1 {status_code} {status_text}\r\n"
    
    # 2. Required Headers
    headers = [
        f"Date: {date_header}",
        f"Server: {SERVER_NAME}",
        f"Content-Type: {content_type}",
        f"Content-Length: {content_length}",
        "Connection: close"
    ]
    
    # 3. Assemble and Encode Headers (ending with the critical \r\n\r\n)
    header_string = response_line + '\r\n'.join(headers) + '\r\n\r\n'
    
    # Combine header (bytes) and body (bytes).
    return header_string.encode('latin-1') + content_body


# Path Resolution and File Serving

def build_response(uri_path, doc_root):
    """
    Handles URI decoding, path resolution, security checks, file I/O, 
    and returns the final formatted HTTP response.
    """
    
    # 1. URI Decoding
    try:
        uri_path = urllib.parse.unquote(uri_path)
    except Exception:
        error_html = b"<h1>400 Bad Request</h1>"
        return format_http_response(400, "Bad Request", "text/html", error_html)

    # 2. Index Handling
    if uri_path.endswith('/'):
        uri_path += 'index.html'

    # Combine document root and relative path safely
    relative_path = uri_path.lstrip('/')
    full_path = os.path.join(doc_root, relative_path)

    # 3. Directory Traversal Prevention
    abs_doc_root = os.path.abspath(doc_root)
    abs_full_path = os.path.abspath(full_path)

    # Ensure the resolved path is strictly inside the document root
    if not abs_full_path.startswith(abs_doc_root):
        error_html = b"<h1>404 Not Found (Security Violation)</h1>"
        return format_http_response(404, "Not Found", "text/html", error_html)

    # 4. Attempt to Read File
    try:
        # Open in binary mode ('rb') for all file types (images, CSS, HTML, etc.)
        with open(full_path, 'rb') as f:
            content_body = f.read()

        mime_type = get_mime_type(full_path)

        # Success: 200 OK
        return format_http_response(200, "OK", mime_type, content_body)

    except FileNotFoundError:
        # Failure: 404 Not Found
        error_html = b"<h1>404 Not Found</h1>"
        return format_http_response(404, "Not Found", "text/html", error_html)

# Threaded Client Handler
def handle_request(client_socket, doc_root):
    """Handles a single client connection in a separate thread."""
    
    request_data = b''
    try:
        # Read request data until the end of headers (\r\n\r\n)
        while True:
            chunk = client_socket.recv(1024)
            if not chunk:
                break
            request_data += chunk
            if b'\r\n\r\n' in request_data:
                break

    except socket.error as e:
        # Handle connection reset or errors during receive
        print(f"Socket error during receive: {e}")
        client_socket.close()
        return

    if not request_data:
        client_socket.close()
        return  

    try:
        # Decode and split the request line
        request_lines = request_data.decode('latin-1').split('\r\n')
        request_line = request_lines[0]
        method, uri_path, http_version = request_line.split()
    except Exception:
        # Malformed request line
        client_socket.close()
        return

    # Only GET is required
    if method != 'GET':
        client_socket.close()
        return

    # Build and send the response
    response_bytes = build_response(uri_path, doc_root)

    try:
        client_socket.sendall(response_bytes)
    except socket.error as e:
        print(f"Socket error while sending response: {e}")
        
    client_socket.close()

# Main Server Initialization
def start_server(port, doc_root):
    """Initializes the server socket and enters the main accept loop."""
    
    if not os.path.isdir(doc_root):
        print(f"Error: Document root '{doc_root}' is not a valid directory.")
        sys.exit(1)

    # 1. Socket Setup (AF_INET=IPv4, SOCK_STREAM=TCP)
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        # 2. Bind and Listen
        server_socket.bind(('', port)) # Bind to all interfaces
        server_socket.listen(5)
    except socket.error as e:
        print(f"Failed to bind or listen on port {port}: {e}")
        sys.exit(1)
    
    print(f"Serving HTTP on port {port} with document root '{os.path.abspath(doc_root)}' ...")
    
    # 3. Main Accept Loop
    while True:
        try:
            # Blocking call: waits for a new client connection
            client_socket, client_address = server_socket.accept()
            print(f"Accepted connection from {client_address[0]}:{client_address[1]}")
            
            # Start a new thread for concurrent handling
            handler_thread = threading.Thread(
                target=handle_request, 
                args=(client_socket, doc_root)
            )
            handler_thread.daemon = True
            handler_thread.start()
            
        except KeyboardInterrupt:
            # Graceful shutdown on Ctrl+C
            print("\nShutting down server...")
            server_socket.close()
            break
        except Exception as e:
            print(f"An unexpected error occurred in the main loop: {e}")

# Execution
if __name__ == "__main__":
    # Check for required command-line arguments
    if len(sys.argv) != 3:
        print("Usage: python http_server.py <port> <document_root>")
        sys.exit(1)

    # Parse and validate arguments
    try:
        port = int(sys.argv[1])
        document_root = sys.argv[2]
    except ValueError:
        print("Error: Port must be an integer.")
        sys.exit(1)

    start_server(port, document_root)