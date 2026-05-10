import socket
import json
import os
import threading
from datetime import datetime

SERVER_HOST = 'localhost'
SERVER_PORT = 5000
FILES_DIR = 'files'
DEFAULT_USER = 'student'
DEFAULT_PASSWORD = '1234'

file_history = {}

def ensure_files_dir():
    if not os.path.exists(FILES_DIR):
        os.makedirs(FILES_DIR)
        print(f"✓ Directory '{FILES_DIR}' created")

def authenticate(username, password):
    return username == DEFAULT_USER and password == DEFAULT_PASSWORD

def safe_path(filename):
    filename = os.path.basename(filename)
    return os.path.join(FILES_DIR, filename)

def add_history(filename, operation, user):
    if filename not in file_history:
        file_history[filename] = []

    moment = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    file_history[filename].append(f"{moment} - {operation} by {user}")

def handle_client(conn, addr):
    print(f"\n🔗 Client connected from {addr}")
    authenticated = False
    current_user = None

    try:
        while True:
            request_data = conn.recv(4096).decode('utf-8')
            if not request_data:
                break

            try:
                request = json.loads(request_data)
                command = request.get('command')

                print(f"📨 Command received: {command}")

                if command == 'login':
                    username = request.get('username')
                    password = request.get('password')

                    if authenticate(username, password):
                        authenticated = True
                        current_user = username
                        response = {'status': 'success', 'message': f'Welcome {username}!'}
                    else:
                        response = {'status': 'error', 'message': 'Invalid credentials'}

                elif not authenticated:
                    response = {'status': 'error', 'message': 'Not authenticated. Use login first'}

                elif command == 'upload':
                    filename = os.path.basename(request.get('filename'))
                    content = request.get('content', '')

                    filepath = safe_path(filename)
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)

                    add_history(filename, 'uploaded', current_user)
                    response = {'status': 'success', 'message': f'File {filename} uploaded'}

                elif command == 'rename_file':
                    old_name = os.path.basename(request.get('old_name', ''))
                    new_name = os.path.basename(request.get('new_name', ''))

                    old_path = safe_path(old_name)
                    new_path = safe_path(new_name)

                    if not old_name or not new_name:
                        response = {'status': 'error', 'message': 'Old name and new name are required'}
                    elif not os.path.exists(old_path):
                        response = {'status': 'error', 'message': f'File {old_name} does not exist'}
                    elif os.path.exists(new_path):
                        response = {'status': 'error', 'message': f'File {new_name} already exists'}
                    else:
                        os.rename(old_path, new_path)

                        if old_name in file_history:
                            file_history[new_name] = file_history.pop(old_name)

                        add_history(new_name, f'renamed from {old_name} to {new_name}', current_user)
                        response = {'status': 'success', 'message': f'File renamed from {old_name} to {new_name}'}

                elif command == 'read_file':
                    filename = os.path.basename(request.get('filename', ''))
                    filepath = safe_path(filename)

                    if not filename:
                        response = {'status': 'error', 'message': 'Filename is required'}
                    elif not os.path.exists(filepath):
                        response = {'status': 'error', 'message': f'File {filename} does not exist'}
                    else:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()

                        add_history(filename, 'read', current_user)
                        response = {
                            'status': 'success',
                            'message': f'Content of {filename}',
                            'content': content
                        }

                elif command == 'download':
                    filename = os.path.basename(request.get('filename', ''))
                    filepath = safe_path(filename)

                    if not filename:
                        response = {'status': 'error', 'message': 'Filename is required'}
                    elif not os.path.exists(filepath):
                        response = {'status': 'error', 'message': f'File {filename} does not exist'}
                    else:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()

                        add_history(filename, 'downloaded', current_user)
                        response = {
                            'status': 'success',
                            'message': f'File {filename} downloaded',
                            'filename': filename,
                            'content': content
                        }

                elif command == 'edit_file':
                    filename = os.path.basename(request.get('filename', ''))
                    new_content = request.get('content', '')
                    filepath = safe_path(filename)

                    if not filename:
                        response = {'status': 'error', 'message': 'Filename is required'}
                    elif not os.path.exists(filepath):
                        response = {'status': 'error', 'message': f'File {filename} does not exist'}
                    else:
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(new_content)

                        add_history(filename, 'edited', current_user)
                        response = {'status': 'success', 'message': f'File {filename} edited'}

                elif command == 'see_file_operation_history':
                    filename = os.path.basename(request.get('filename', ''))

                    if not filename:
                        response = {'status': 'error', 'message': 'Filename is required'}
                    elif filename not in file_history or len(file_history[filename]) == 0:
                        response = {'status': 'success', 'message': f'No history for {filename}'}
                    else:
                        history_text = "\n".join(file_history[filename])
                        response = {
                            'status': 'success',
                            'message': f'History for {filename}:\n{history_text}'
                        }

                elif command == 'list_files':
                    files = os.listdir(FILES_DIR)
                    response = {'status': 'success', 'files': files}

                elif command == 'logout':
                    authenticated = False
                    current_user = None
                    response = {'status': 'success', 'message': 'Logged out'}

                else:
                    response = {'status': 'error', 'message': f'Unknown command: {command}'}

            except Exception as e:
                response = {'status': 'error', 'message': str(e)}
                print(f"✗ Error: {str(e)}")

            conn.send(json.dumps(response).encode('utf-8'))

    except Exception as e:
        print(f"✗ Connection error: {str(e)}")
    finally:
        conn.close()
        print(f"🔌 Client disconnected from {addr}")

def start_server():
    ensure_files_dir()

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((SERVER_HOST, SERVER_PORT))
    server_socket.listen(5)

    print("=" * 60)
    print("🚀 FTP SERVER STARTED")
    print("=" * 60)
    print(f"Host: {SERVER_HOST}")
    print(f"Port: {SERVER_PORT}")
    print(f"Files Directory: {FILES_DIR}")
    print(f"Default User: {DEFAULT_USER}")
    print(f"Default Password: {DEFAULT_PASSWORD}")
    print("=" * 60)

    try:
        while True:
            conn, addr = server_socket.accept()
            client_thread = threading.Thread(target=handle_client, args=(conn, addr))
            client_thread.daemon = True
            client_thread.start()
    except KeyboardInterrupt:
        print("\n\n⛔ Server shutting down...")
    finally:
        server_socket.close()

if __name__ == '__main__':
    start_server()