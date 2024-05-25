import socket
import threading
from statki import handle_client  # Importujemy funkcję handle_client z pliku statki.py

# Konfiguracja serwera
SERVER_IP = '0.0.0.0'
SERVER_PORT = 5555


def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((SERVER_IP, SERVER_PORT))
    server.listen(2)
    print(f"Server started, listening on {SERVER_IP}:{SERVER_PORT}...")

    for player_id in range(2):
        client_socket, client_address = server.accept()
        print(f"Accepted connection from {client_address}")
        player_thread = threading.Thread(target=handle_client, args=(client_socket, player_id))
        player_thread.start()


if __name__ == "__main__":
    start_server()
