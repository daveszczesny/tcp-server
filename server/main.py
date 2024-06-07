import socket
import threading
from poker import Player, PokerRules
import time
from logger import logger

log = logger(Player.player_list)


def handler(client_socket: socket.socket, client_addr, bot_name: str) -> None:
    try:
        Player.create_player(client_socket, bot_name)
        log.send_message_to_client(client_socket, msg=f"Welcome {bot_name}")
        # While loop to keep client handler alive
        while True:
            pass
        
    except Exception as ex:
        print(f"[CLIENT ERROR] - {bot_name}: {ex}")
    finally:
        client_socket.close()

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  #
    server.bind(('0.0.0.0', 9999))
    server.listen(5)

    print("Server listening on port 9999")
    num_players = int(input("Enter amount of connections: "))

    while Player.size() < num_players:
        print("Awaiting connections...")
        client_socket, addr = server.accept()
        bot_name = client_socket.recv(1024).decode('utf-8')
        print(f"Accepted connection from {addr}, Bot: {bot_name}")
        client_handler = threading.Thread(target=handler, args=(client_socket, addr, bot_name))
        client_handler.start()
        print(f"Server player limit: {Player.size()} / {num_players}")


        time.sleep(1)

    print("Server reached player limit...")

    print("[SERVER] Players in Lobby")
    log.send_message_to_clients("Players in Lobby")
    for player in Player.player_list:
        print(f"> {player.name}")
        log.send_message_to_clients(f"> {player.name}")


    option = input("Select Game: \n1. Poker\n")

    if option == "1" or option.lower() == 'poker':
        print("Game Poker selected!")
        log.send_message_to_clients('Poker game selected. Game starting soon... ')
        # Start Poker game

        poker_game = PokerRules(small_blind=50, big_blind=100)
        poker_game.run()




if __name__ == '__main__':
    main()