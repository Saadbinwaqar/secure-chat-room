import socket
import threading
import json
from datetime import datetime

HOST = '0.0.0.0'
PORT = 65432

clients = {}

def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def broadcast(packet, sender_socket):
    for client in list(clients.keys()):
        if client != sender_socket:
            try:
                client.send(packet)
            except:
                client.close()
                del clients[client]

def handle_client(client_socket):
    try:
        pubkey_data = client_socket.recv(4096).decode()
        username = f"User {len(clients)+1}"  # Assign username
        clients[client_socket] = {
            'public_key': pubkey_data,
            'addr': client_socket.getpeername(),
            'username': username
        }
        print(f"[{get_timestamp()}] [SERVER] Public key from {username} {clients[client_socket]['addr']}")

        def send_keys_update():
            keys = {str(info['addr']): info['public_key'] for c, info in clients.items()}
            usernames = {str(info['addr']): info['username'] for c, info in clients.items()}
            packet = json.dumps({
                "keys_update": keys,
                "usernames": usernames
            }).encode()
            for c in clients:
                c.send(packet)

        send_keys_update()

        while True:
            packet = client_socket.recv(16384)
            if not packet:
                break
            broadcast(packet, client_socket)

    except Exception as e:
        print(f"[{get_timestamp()}] Error:", e)

    finally:
        print(f"[{get_timestamp()}] [SERVER] Lost connection {clients[client_socket]['username']} {clients[client_socket]['addr']}")
        client_socket.close()
        del clients[client_socket]
        send_keys_update()

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()

    print(f"[{get_timestamp()}] Server running on {HOST}:{PORT}")

    while True:
        client_socket, addr = server.accept()
        print(f"[{get_timestamp()}] [SERVER] New client {addr}")
        threading.Thread(target=handle_client, args=(client_socket,)).start()

if __name__ == "__main__":
    start_server()