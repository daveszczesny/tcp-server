import random
import socket
import time
import json
from logger import logger

class Deck:

    suits: list[str] = ['spades', 'hearts', 'diamonds', 'clubs']
    ranks: list[str] = ['2','3','4','5','6','7','8','9','10','jack','queen','king','ace']
    
    deck_of_cards: list[str] = []

    def __init__(self):
        self.create_deck_of_cards()

    def create_deck_of_cards(self):
        for suit in self.suits:
            for rank in self.ranks:
                self.deck_of_cards.append(rank + ' of ' + suit)

    def print(self):
        for card in self.deck_of_cards:
            print(card)


    def pick_card(self) -> str:
        assert len(self.deck_of_cards) > 0, "No cards in deck"

        card: str = random.choice(self.deck_of_cards)
        self.deck_of_cards.remove(card)
        return card


    # Use method at start of game to deal cards to players
    def deal_cards_poker(self) -> list[str, str]:
        return [self.pick_card(), self.pick_card()]


class Player:

    player_list: list = []

    def __init__(self, conn, name):
        self._conn = conn   
        self._name = name
        self._has_lost: bool = False

    @property
    def conn(self):
        return self._conn
    
    @conn.setter
    def conn(self, value: socket.socket):
        self._conn = value

    @property
    def name(self) -> str:
        return self._name
    
    @name.setter
    def name(self, value: str):
        self._name = value

    @property
    def has_lost(self) -> bool:
        return self._has_lost

    @has_lost.setter
    def has_lost(self, value: bool) -> None:
        self._has_lost = value

    @staticmethod
    def remove_player(conn: socket.socket):
        Player.player_list.remove(conn)

    @staticmethod
    def create_player(conn: socket.socket, name: str):
        Player.player_list.append(Player(conn, name))


    @staticmethod
    def size() -> int:
        return len(Player.player_list)

log = logger(Player.player_list)

class PokerPlayer(Player):
    def __init__(self, conn, name, chips: int=10_000):
        super().__init__(conn, name)
        self._cards: list[str] = []
        self._chips: int = chips
        self._bought_in: bool = False

    @staticmethod
    def convert_player_to_poker_player():
        converted_players = []
        for player in Player.player_list:
            poker_player = PokerPlayer(player.conn, player.name)
            converted_players.append(poker_player)

        Player.player_list = converted_players


    @property
    def cards(self):
        return self._cards
    
    @cards.setter
    def cards(self, value):
        self._cards = value


    @property
    def chips(self) -> int:
        return self._chips
    
    @chips.setter
    def chips(self, value) -> None:
        self._chips = value

    @property
    def bought_in(self):
        return self._bought_in
    
    @bought_in.setter
    def bought_in(self, value: bool):
        self._bought_in = value



class PokerRules:    
    def __init__(self, big_blind: int = 0, small_blind: int = 0):
        self.poker_deck = Deck()
        PokerPlayer.convert_player_to_poker_player()

        self.blinds: bool = False
        self._big_blind = big_blind
        self._small_blind = small_blind

        self.player_small_blind: PokerPlayer
        self.player_big_blind: PokerPlayer

        self.pot: int = 0

        if PokerPlayer.size() > 1:
            self.blinds = True
        else:
            print('[SERVER] Not enough players for big blind / small blind poker')

        
        if self.blinds:
            self.player_small_blind = PokerPlayer.player_list[0]
            log.send_message_to_client(Player.player_list[0].conn, "You are small bind!")

            self.player_big_blind = PokerPlayer.player_list[1]
            log.send_message_to_client(Player.player_list[1].conn, "You are big blind!")
        
            log.send_message_to_clients(f"Big blind is {self.big_blind}, and small blind is {self.small_blind}")


        # Assign cards to player
        log.send_message_to_clients("Dealer is shuffling cards...")
        time.sleep(1)
        for player in PokerPlayer.player_list:
            player.cards = self.poker_deck.deal_cards_poker()
            log.send_message_to_client(player.conn, f"You got dealt {player.cards}")

    
    def put_blinds(self):
        self.player_small_blind.chips -= self.small_blind
        self.player_big_blind.chips -= self.big_blind
        self.pot += self.small_blind + self.big_blind
        for player in PokerPlayer.player_list:
            log.send_message_to_client(player.conn, f"You currently have {player.chips} chips left")

    def construct_game_state_to_json(self, player: PokerPlayer):
        gamestate = {
            'pot': self.pot,
            'hand': player.cards
        }

        return json.dumps(gamestate).encode('utf-8')
    

    def game_actions(self, player: PokerPlayer):
        actions = [
            'fold',
            'raise',
            'call'
        ]

        if not  player.bought_in:
            actions.insert(0, 'buy-in')

        return json.dumps(actions).encode('utf-8')
    
    def handle_response(self, response: str, player: PokerPlayer, is_small_bid: bool):

        """
            expected response:
            {
                'action': 'buy-in'
            }
            or when more data is needed
            {
                'action': 'raise'
                'amount': 5000
            }
        """
        try:
            res = json.loads(response)
            # for debugging uncomment below line
            log.server(f'Player {player.name}: {res}')

            if res['action'] == 'buy-in':
                if is_small_bid:
                    player.chips -= self.small_blind
                    self.pot += self.small_blind
                else:
                    player.chips -= self.big_blind
                    self.pot += self.big_blind

                log.server(f"{player.name} bought in!")
                log.send_message_to_clients(f"{player.name} bought in!")
            elif res['action'] == 'fold':
                player.has_lost = True

                log.server(f"{player.name} has folded")
                log.send_message_to_clients(f"{player.name} has folded")

            elif res['action'] == 'raise':
                if player.chips > res['amount']:
                    player.chips -= int(res['amount'])
                    self.pot += int(res['amount'])
                    log.server(f'{player.name} raised {res["amount"]}')
                    log.send_message_to_clients(f'{player.name} raised {res["amount"]}')
                else:
                    # If player raised an amount they don't have
                    # they go all in
                    self.pot += player.chips
                    player.chips = 0
                    log.server(f'{player.name} raised {player.chips}')
                    log.send_message_to_clients(f'{player.name} raised {player.chips}')

            elif res['action'] == 'call':
                log.server(f'{player.name} called')
                log.send_message_to_clients(f'{player.name} called')


        except Exception as ex:
            log.server(f'Error when decoding response from user {player.name} {ex}')


    def run(self):
        while True:
            log.server("Putting down blinds")
            self.put_blinds()

            self.player_small_blind.conn.send(self.construct_game_state_to_json(self.player_small_blind))
            # send player instructions on what they can do
            self.player_small_blind.conn.send("Action required: ".encode('utf-8') + self.game_actions(self.player_small_blind))
            # expect a reply from said user
            response = self.player_small_blind.conn.recv(1024).decode('utf-8')

            self.handle_response(response, self.player_small_blind, True)
            self.player_small_blind.conn.recv(1024).decode('utf-8')

    # blinds
    @property
    def big_blind(self):
        return self._big_blind
    
    @big_blind.setter
    def big_blind(self, value: int):
        assert value >= 0, "Value cannot be negative!"
        self._big_blind = value

    @property
    def small_blind(self):
        return self._small_blind
    
    @small_blind.setter
    def small_blind(self, value: int):
        assert value >= 0, "Value cannot be negative!"
        self._small_blind = value


    @property
    def player_big_blind(self):
        return self._player_big_blind
    
    @player_big_blind.setter
    def player_big_blind(self, conn: PokerPlayer):
        self._player_big_blind = conn
    

