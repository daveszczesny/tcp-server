import socket


class logger:

    def __init__(self, player_list: list[socket.socket]):
        self.player_list = player_list

    # Send a message to all clients
    def send_message_to_clients(self, msg: str) -> None:
        for player in self.player_list:
            player.conn.send(('[SERVER] ' + msg).encode('utf-8'))



    def send_message_to_client(self, client_socket: socket.socket, msg: str) -> None:
        client_socket.send(('[SERVER] ' + msg).encode('utf-8'))


    def recieve_message_from_client(self, name: str, msg: str) -> None:
        print(f'[CLIENT] - {name}: {msg}')


    def server(self, msg: str) -> None:
        print(f'[SERVER] {msg}')
