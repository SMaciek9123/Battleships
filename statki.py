import sys
import socket
import threading
from random import randint, choice
import time

# Opcje statków
SHIPS_CONFIG = {
    2: [1],
    3: [1],
    5: [2, 3],
    7: [2, 3, 4],
    10: [1, 2, 3, 4, 5]
}
UNITS = ['A', 'B', 'C', 'D', 'E']

# Kolory
COLORS = {
    "reset": "\033[00m",
    "red": "\033[91m",
    "green": "\033[92m",
    "blue": "\033[94m",
    "cyan": "\033[96m",
    "yellow": "\033[93m",
    "pink": "\033[95m",
    "purple": "\033[35m",
    "orange": "\033[38;5;214m"
}

# Globalne zmienne do przechowywania stanu gry
player_boards = [None, None]
player_ships = [None, None]
player_hits = [0, 0]
current_turn = 0
game_size = 5

# Definicje graczy
player_one = {
    "name": "Player 1",
    "hits": 0,
    "wins": 0,
}
player_two = {
    "name": "Player 2",
    "hits": 0,
    "wins": 0,
}

# Historia strzałów
player_one_shots = []
player_two_shots = []


def create_board(size):
    """Tworzy planszę o podanym rozmiarze."""
    return [['O' for _ in range(size)] for _ in range(size)]


def place_ship(board, ships, ship_length, ship_symbol, size):
    """Umieszcza statek na planszy."""
    max_attempts = 1000
    attempts = 0
    while attempts < max_attempts:
        orientation = choice(['V', 'H'])
        row = randint(0, size - 1)
        col = randint(0, size - 1)

        if can_place_ship(board, ship_length, orientation, row, col, size):
            positions = []
            if orientation == 'H':
                for i in range(ship_length):
                    board[row][col + i] = ship_symbol
                    positions.append((row, col + i))
            else:
                for i in range(ship_length):
                    board[row + i][col] = ship_symbol
                    positions.append((row + i, col))

            ships.append({'symbol': ship_symbol, 'positions': positions, 'hits': 0})
            return True

        attempts += 1

    return False


def can_place_ship(board, ship_length, orientation, row, col, size):
    """Sprawdza, czy można umieścić statek na planszy."""
    if orientation == 'H':
        if col + ship_length > size:
            return False
        for i in range(ship_length):
            if board[row][col + i] != 'O':
                return False
            for move_r in range(-1, 2):
                for move_c in range(-1, 2):
                    r, c = row + move_r, col + i + move_c
                    if 0 <= r < size and 0 <= c < size and board[r][c] != 'O':
                        return False
    else:
        if row + ship_length > size:
            return False
        for i in range(ship_length):
            if board[row + i][col] != 'O':
                return False
            for move_r in range(-1, 2):
                for move_c in range(-1, 2):
                    r, c = row + i + move_r, col + move_c
                    if 0 <= r < size and 0 <= c < size and board[r][c] != 'O':
                        return False
    return True


def start_the_game(size):
    """Rozpoczyna grę dla planszy o podanym rozmiarze."""
    player_one_board = create_board(size)
    player_two_board = create_board(size)
    player_one_ships = []
    player_two_ships = []
    ships = SHIPS_CONFIG[size]
    ships_symbols = UNITS

    for i, ship_length in enumerate(ships):
        if not place_ship(player_one_board, player_one_ships, ship_length, ships_symbols[i], size):
            print(f"Failed to place all ships for Player 1 on the {size}x{size} board.")
            sys.exit(1)
        if not place_ship(player_two_board, player_two_ships, ship_length, ships_symbols[i], size):
            print(f"Failed to place all ships for Player 2 on the {size}x{size} board.")
            sys.exit(1)

    return player_one_board, player_two_board, player_one_ships, player_two_ships


def handle_client(client_socket, player_id):
    """Obsługuje połączenie z klientem."""
    global current_turn, game_size
    client_socket.sendall(f"Welcome Player {player_id + 1}!\n".encode('utf-8'))
    while True:
        try:
            data = client_socket.recv(1024).decode('utf-8')
            if not data:
                break
            print(f"Received from Player {player_id + 1}: {data}")
            # Tu dodaj logikę gry
            if data.startswith("SIZE:"):
                game_size = int(data.split(":")[1])
                client_socket.sendall("SIZE_ACK\n".encode('utf-8'))
                start_the_game(game_size)
            elif player_id == current_turn:
                # Przetwarzanie ruchu gracza
                client_socket.sendall("Move received\n".encode('utf-8'))
                current_turn = (current_turn + 1) % 2  # Zmiana tury
            else:
                client_socket.sendall("Not your turn\n".encode('utf-8'))
        except ConnectionResetError:
            break
    client_socket.close()


def shooting(player, opponent_board, opponent_ships, board, size):
    """Obsługuje strzał gracza."""
    while True:
        try:
            guess = input(f"{player['name']}, guess Row and Column: ").strip().lower()
            guess_row, guess_col = map(int, guess.split())
            guess_row -= 1
            guess_col -= 1
        except ValueError:
            print("Enter valid numbers for row and column")
            continue
        else:
            if 0 <= guess_row < size and 0 <= guess_col < size:
                if board[guess_row][guess_col] != 'O':
                    print(
                        COLORS['orange'] + "You have already shot at this location. Choose another." + COLORS['reset'])
                    continue
                break
            else:
                print("Guess out of range, try again")

    if player['name'] == player_one['name']:
        player_one_shots.append((guess_row + 1, guess_col + 1))
    else:
        player_two_shots.append((guess_row + 1, guess_col + 1))

    if hit(opponent_board, guess_row, guess_col):
        if player['name'] == player_one['name']:
            print(COLORS['green'] + f"{player['name']} hit a ship!" + COLORS['reset'])
            opponent_board[guess_row][guess_col] = 'X'
            board[guess_row][guess_col] = COLORS['green'] + 'X' + COLORS['reset']
        else:
            print(COLORS['green'] + f"{player['name']} hit a ship!" + COLORS['reset'])
            opponent_board[guess_row][guess_col] = 'Y'
            board[guess_row][guess_col] = COLORS['green'] + 'Y' + COLORS['reset']
        for ship in opponent_ships:
            if (guess_row, guess_col) in ship['positions']:
                ship['hits'] += 1
                if sunk(ship):
                    print(COLORS['blue'] + f"{player['name']} sunk a ship!" + COLORS['reset'])
                    mark_surroundings(board, ship, size)
                break
        player['hits'] += 1
    else:
        if player['name'] == player_one['name']:
            print(COLORS['red'] + f"{player['name']} missed :(" + COLORS['reset'])
            board[guess_row][guess_col] = COLORS['red'] + 'x' + COLORS['reset']
        else:
            print(COLORS['red'] + f"{player['name']} missed :(" + COLORS['reset'])
            board[guess_row][guess_col] = COLORS['red'] + 'y' + COLORS['reset']
    print(f"{player['name']}'s view of the board: ")
    show_board(board)
    return 'continue'


def mark_surroundings(board, ship, size):
    """Zaznacza otoczenie zatopionego statku."""
    for (row, col) in ship['positions']:
        for r in range(row - 1, row + 2):
            for c in range(col - 1, col + 2):
                if 0 <= r < size and 0 <= c < size and board[r][c] == 'O':
                    board[r][c] = COLORS['yellow'] + '.' + COLORS['reset']


def hit(board, row, col):
    """Sprawdza, czy statek został trafiony."""
    return board[row][col] in UNITS


def sunk(ship):
    """Sprawdza, czy statek został zatopiony."""
    return ship['hits'] == len(ship['positions'])


def show_board(board):
    """Wyświetla planszę."""
    for row in board:
        print(" ".join(row))


def show_menu_2(player, opponent_board, opponent_ships, board, size):
    """Wyświetla menu dla gracza w trakcie gry."""
    while True:
        print(f"\n{player['name']}'s turn")
        print("1. Shoot")
        print("2. View board")
        print("3. Surrender")
        choice = input("Choose what to do: ").strip()

        if choice == '1':
            return shooting(player, opponent_board, opponent_ships, board, size)
        elif choice == '2':
            print(f"{player['name']}'s view of the board: ")
            show_board(board)
        elif choice == '3':
            return 'surrender'
        else:
            print("Invalid choice, please choose again")


def turns(number_of_turns):
    """Zwraca aktualnego gracza na podstawie liczby tur."""
    return player_one if number_of_turns % 2 == 0 else player_two


def show_menu_1():
    """Wyświetla menu główne gry."""
    global player_one, player_two
    while True:
        print("1. Offline game")
        print("2. Online game")
        print("3. Test")
        print("4. Instruction")
        print("5. Exit")
        choice = input("Choose an option 1-5: ").strip()

        if choice == '1':
            player_one["name"] = input("Enter name for Player 1: ").strip() or "Player 1"
            player_two["name"] = input("Enter name for Player 2: ").strip() or "Player 2"
            choose_board_size()

        elif choice == '2':
            player_one["name"] = input("Enter your name: ").strip() or "Player 1"
            online_game()

        elif choice == '3':
            player_one["name"] = "Player 1"
            player_two["name"] = "Player 2"
            size = 2
            main(size)

        elif choice == '4':
            print(COLORS[
                      'yellow'] + "Instructions: \n1. Players take turns guessing row and column to find opponent's "
                                  "ships.\n2. The game ends when all ships of one player are sunk.\n" +
                  COLORS['reset'])
        elif choice == '5':
            print("Goodbye!")
            sys.exit()
        else:
            print("Invalid choice, please choose again")


def choose_board_size():
    """Umożliwia wybór rozmiaru planszy."""
    global game_size
    while True:
        print("\nChoose board size:")
        print("1. 3x3 (1 ship of size 1x1)")
        print("2. 5x5 (2 ships: 1x2, 1x3)")
        print("3. 7x7 (3 ships: 1x2, 1x3, 1x4)")
        print("4. 10x10 (5 ships: 1x1, 1x2, 1x3, 1x4, 1x5)")
        choice = input("Choose an option (1-4): ").strip()
        if choice == '1':
            game_size = 3
            break
        elif choice == '2':
            game_size = 5
            break
        elif choice == '3':
            game_size = 7
            break
        elif choice == '4':
            game_size = 10
            break
        else:
            print("Invalid choice, please choose again")

    for conn in connections:
        conn[0].sendall(f"SIZE:{game_size}\n".encode('utf-8'))
        response = conn[0].recv(1024).decode('utf-8')
        if response.strip() != "SIZE_ACK":
            print("Error: Failed to synchronize board size with client.")
            sys.exit(1)

    start_the_game(game_size)
    main(game_size)


def play_again():
    """Pytanie o ponowną grę."""
    while True:
        print("\n1. Rematch")
        print("2. Return to Menu")
        choice = input("Choose an option: ").strip()

        if choice == '1':
            return 'rematch'
        elif choice == '2':
            return 'menu'
        else:
            print("Invalid choice, please choose again.")


def end_game_stats():
    """Wyświetla statystyki gry na końcu."""
    print(f"Player 1 hits: {player_one['hits']}, misses: {len(player_one_shots) - player_one['hits']}")
    print(f"Player 2 hits: {player_two['hits']}, misses: {len(player_two_shots) - player_two['hits']}")


def main(size):
    """Główna funkcja uruchamiająca grę."""
    global game_board_size, player_one_board, player_two_board, player_one_shots, player_two_shots
    game_board_size = size
    player_one_board, player_two_board, player_one_ships, player_two_ships = start_the_game(size)
    player_one_view = create_board(size)
    player_two_view = create_board(size)
    player_one['hits'] = 0
    player_two['hits'] = 0
    player_one_shots = []
    player_two_shots = []
    number_of_turns = 0

    print("-------GOOD LUCK-------")
    while player_one['hits'] < sum(SHIPS_CONFIG[size]) and player_two['hits'] < sum(SHIPS_CONFIG[size]):
        current_player = turns(number_of_turns)
        opponent_board = player_two_board if current_player == player_one else player_one_board
        opponent_ships = player_two_ships if current_player == player_one else player_one_ships
        current_view = player_one_view if current_player == player_one else player_two_view

        print(f"Turn {number_of_turns}: {current_player['name']}'s turn")
        result = show_menu_2(current_player, opponent_board, opponent_ships, current_view, size)
        if result == 'surrender':
            if current_player == player_one:
                player_two['wins'] += 1
            else:
                player_one['wins'] += 1
            break
        number_of_turns += 1

    if player_one['hits'] >= sum(SHIPS_CONFIG[size]):
        print(COLORS['pink'] + f"{player_one['name']} wins!" + COLORS['reset'])
        player_one['wins'] += 1
    elif player_two['hits'] >= sum(SHIPS_CONFIG[size]):
        print(COLORS['pink'] + f"{player_two['name']} wins!" + COLORS['reset'])
        player_two['wins'] += 1

    print('The current match score is %d : %d (Player 1 : Player 2)' % (player_one["wins"], player_two["wins"]))
    end_game_stats()
    result = play_again()
    if result == 'rematch':
        main(size)
    else:
        show_menu_1()


connections = []


def start_server():
    """Uruchamia serwer gry."""
    global connections
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', 5555))
    server.listen(2)
    print("Server started, waiting for connections...")

    def accept_connections():
        while len(connections) < 2:
            try:
                server.settimeout(300)  # Ustaw limit czasu na 5 minut
                client_socket, client_address = server.accept()
                connections.append((client_socket, client_address))
                print(f"Accepted connection from {client_address}")
                if len(connections) == 2:
                    for conn in connections:
                        conn[0].sendall("CONNECTED\n".encode('utf-8'))
                    break
            except socket.timeout:
                print("No connection received within 5 minutes. Returning to menu.")
                break

    accept_thread = threading.Thread(target=accept_connections)
    accept_thread.start()
    accept_thread.join()

    if len(connections) < 2:
        for conn in connections:
            conn[0].close()
        connections = []
        return False

    for player_id, (client_socket, client_address) in enumerate(connections):
        player_thread = threading.Thread(target=handle_client, args=(client_socket, player_id))
        player_thread.start()

    return True


def start_client():
    """Uruchamia klienta gry."""
    server_ip = input("Enter server IP: ").strip()
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((server_ip, 5555))
    welcome_message = client.recv(1024).decode('utf-8')
    print(welcome_message)

    connected_message = client.recv(1024).decode('utf-8')
    if connected_message.strip() == "CONNECTED":
        print("Connection successful. Waiting for host to choose board size...")
    else:
        print("Failed to connect properly. Exiting.")
        return

    while True:
        message = input("Enter your move (row col): ")
        client.sendall(message.encode('utf-8'))
        response = client.recv(1024).decode('utf-8')
        print(response)


def online_game():
    """Funkcja do obsługi gry online."""
    while True:
        print("\nOnline Game:")
        print("1. Host game")
        print("2. Join game")
        choice = input("Choose an option (1-2): ").strip()

        if choice == '1':
            if start_server():
                print("Connection successful. Proceeding to board size selection...")
                choose_board_size()
            else:
                print("Returning to menu...")
                show_menu_1()
            break
        elif choice == '2':
            start_client()
            break
        else:
            print("Invalid choice, please choose again.")


if __name__ == "__main__":
    show_menu_1()
