import socket


def start_client():
    server_ip = input("Enter server IP: ").strip()
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((server_ip, 5555))
    welcome_message = client.recv(1024).decode('utf-8')
    print(welcome_message)

    while True:
        message = input("Enter your move (row col): ")
        client.sendall(message.encode('utf-8'))
        response = client.recv(1024).decode('utf-8')
        print(response)


if __name__ == "__main__":
    start_client()
